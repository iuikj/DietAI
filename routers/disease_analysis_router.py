from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from shared.models.database import get_db
from shared.models.schemas import BaseResponse, DiseaseCreate, AllergyCreate, NutritionDetailCreate
from shared.utils.auth import get_current_user
from shared.models.user_models import User
from shared.models.disease_analysis_models import Disease, Allergy, DiseaseAnalysisResult
from shared.models.food_models import FoodRecord, NutritionDetail

from langgraph_sdk import get_client

router = APIRouter(prefix="/disease-analysis", tags=["疾病分析"])

# 1. 疾病录入接口
def get_or_create_disease(db: Session, user_id: int, disease_data: dict) -> Disease:
    disease = db.query(Disease).filter_by(user_id=user_id, disease_name=disease_data["disease_name"]).first()
    if not disease:
        disease = Disease(user_id=user_id, **disease_data)
        db.add(disease)
        db.commit()
        db.refresh(disease)
    return disease

@router.post("/disease", response_model=BaseResponse)
async def create_disease(
    disease: DiseaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    disease_obj = get_or_create_disease(db, current_user.id, disease.dict())
    return BaseResponse(success=True, message="疾病信息录入成功", data={"disease_id": disease_obj.id}, timestamp=datetime.now())

# 2. 过敏原录入接口
def get_or_create_allergy(db: Session, user_id: int, allergy_data: dict) -> Allergy:
    allergy = db.query(Allergy).filter_by(user_id=user_id, allergen_name=allergy_data["allergen_name"]).first()
    if not allergy:
        allergy = Allergy(user_id=user_id, **allergy_data)
        db.add(allergy)
        db.commit()
        db.refresh(allergy)
    return allergy

@router.post("/allergy", response_model=BaseResponse)
async def create_allergy(
    allergy: AllergyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allergy_obj = get_or_create_allergy(db, current_user.id, allergy.dict())
    return BaseResponse(success=True, message="过敏原信息录入成功", data={"allergy_id": allergy_obj.id}, timestamp=datetime.now())

# 3. 疾病分析接口（结构化分析模式）
@router.post("/analyze", response_model=BaseResponse)
async def analyze_disease(
    food_record_id: int = Body(..., description="食物记录ID"),
    nutrition_detail_id: int = Body(..., description="营养详情ID"),
    disease_id: int = Body(..., description="疾病ID"),
    allergy_id: Optional[int] = Body(None, description="过敏原ID（可选）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        client = get_client(url="http://127.0.0.1:2024")
        assistant = await client.assistants.create(
            graph_id="disease_analysis_agent",
            config={
                "configurable": {
                    "vision_model_provider": "openai",
                    "vision_model": "gpt-4o",
                    "analysis_model_provider": "openai",
                    "analysis_model": "gpt-4o"
                }
            }
        )
        thread = await client.threads.create()
        
        # 查表组装agent输入
        food_record = db.query(FoodRecord).get(food_record_id)
        nutrition_detail = db.query(NutritionDetail).get(nutrition_detail_id)
        disease = db.query(Disease).get(disease_id)
        allergy = db.query(Allergy).get(allergy_id) if allergy_id else None
        
        if not (food_record and nutrition_detail and disease):
            raise HTTPException(status_code=400, detail="缺少必要的分析输入（食物记录、营养详情、疾病）")
        
        input_data = {
            "foodrecord": food_record.to_dict() if hasattr(food_record, 'to_dict') else dict(food_record.__dict__),
            "nutritiondetail": nutrition_detail.to_dict() if hasattr(nutrition_detail, 'to_dict') else dict(nutrition_detail.__dict__),
            "disease": disease.to_dict() if hasattr(disease, 'to_dict') else dict(disease.__dict__),
            "allergen": allergy.to_dict() if allergy else None
        }
        
        # 去除SQLAlchemy私有字段
        for k in list(input_data.keys()):
            if isinstance(input_data[k], dict):
                input_data[k].pop('_sa_instance_state', None)
        
        run = await client.runs.create(
            assistant_id=assistant["assistant_id"],
            thread_id=thread['thread_id'],
            input=input_data
        )
        
        while True:
            result = await client.threads.get_state(thread["thread_id"])
            current_step = result.get('values', {}).get("current_step")
            if result.get('values', {}).get("error_message") is not None:
                error_msg = result.get('values', {}).get("error_message")
                raise HTTPException(status_code=500, detail=error_msg)
            if current_step == "completed":
                break
        
        result_values = result.get("values", {})
        
        # 写入分析结果表
        analysis_obj = DiseaseAnalysisResult(
            user_id=current_user.id,
            disease_id=disease.id,
            allergen_id=allergy.id if allergy else None,
            risky_nutrients=result_values.get("disease_analysis", {}).get("risky_nutrients"),
            risk_explanations=result_values.get("disease_analysis", {}).get("risk_explanations"),
            avoid_foods=result_values.get("disease_analysis", {}).get("avoid_foods"),
            health_tips=result_values.get("disease_analysis", {}).get("health_tips"),
            agent_raw_result=result_values,
            formatted_output=result_values.get("formatted_output"),
            analysis_time=datetime.now()
        )
        db.add(analysis_obj)
        db.commit()
        db.refresh(analysis_obj)
        
        return BaseResponse(
            success=True,
            message="疾病分析完成，结果已存储",
            data={"analysis_id": analysis_obj.id, "result": result_values},
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"疾病分析失败: {str(e)}")

# 4. 查询分析历史
@router.get("/history", response_model=BaseResponse)
async def get_analysis_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = db.query(DiseaseAnalysisResult).filter_by(user_id=current_user.id).order_by(DiseaseAnalysisResult.analysis_time.desc()).all()
    data = [
        {
            "id": r.id,
            "disease_id": r.disease_id,
            "allergen_id": r.allergen_id,
            "analysis_time": r.analysis_time,
            "risky_nutrients": r.risky_nutrients,
            "risk_explanations": r.risk_explanations,
            "avoid_foods": r.avoid_foods,
            "health_tips": r.health_tips,
            "formatted_output": r.formatted_output
        } for r in results
    ]
    return BaseResponse(success=True, message="分析历史查询成功", data=data, timestamp=datetime.now()) 