from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
import logging
from pydantic import BaseModel
from decimal import Decimal

from shared.models.database import get_db
from shared.models.saved_meal_models import SavedMeal, SavedMealNutrition, UserSavedMealFavorite
from shared.models.food_models import FoodRecord, NutritionDetail
from shared.models.user_models import User
from shared.utils.auth import get_current_user
from shared.models.schemas import BaseResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/saved-meals", tags=["保存菜品"])


# Pydantic 模型定义
class SavedMealNutritionCreate(BaseModel):
    serving_size: float = 100
    serving_unit: str = "g"
    calories: float
    protein: float
    fat: float
    carbohydrates: float
    dietary_fiber: float = 0
    sugar: float = 0
    sodium: float = 0
    cholesterol: float = 0
    vitamin_a: float = 0
    vitamin_c: float = 0
    vitamin_d: float = 0
    calcium: float = 0
    iron: float = 0
    potassium: float = 0


class SavedMealCreate(BaseModel):
    meal_name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: bool = False
    nutrition: SavedMealNutritionCreate


class SavedMealUpdate(BaseModel):
    meal_name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    nutrition: Optional[SavedMealNutritionCreate] = None


class SavedMealResponse(BaseModel):
    id: int
    meal_name: str
    description: Optional[str]
    image_url: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    is_public: bool
    usage_count: int
    favorite_count: int
    created_at: str
    updated_at: str
    nutrition: Optional[SavedMealNutritionCreate]
    is_favorited: Optional[bool] = False  # 当前用户是否收藏

    class Config:
        from_attributes = True


@router.post("/", response_model=BaseResponse[SavedMealResponse])
async def create_saved_meal(
    meal_data: SavedMealCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建保存的菜品"""
    try:
        # 创建保存的菜品
        saved_meal = SavedMeal(
            user_id=current_user.id,
            meal_name=meal_data.meal_name,
            description=meal_data.description,
            image_url=meal_data.image_url,
            category=meal_data.category,
            tags=meal_data.tags,
            is_public=meal_data.is_public
        )
        db.add(saved_meal)
        db.flush()  # 获取ID
        
        # 创建营养信息
        nutrition = SavedMealNutrition(
            saved_meal_id=saved_meal.id,
            **meal_data.nutrition.model_dump()
        )
        db.add(nutrition)
        db.commit()
        
        # 构建响应
        response_data = SavedMealResponse(
            id=saved_meal.id,
            meal_name=saved_meal.meal_name,
            description=saved_meal.description,
            image_url=saved_meal.image_url,
            category=saved_meal.category,
            tags=saved_meal.tags,
            is_public=saved_meal.is_public,
            usage_count=saved_meal.usage_count,
            favorite_count=saved_meal.favorite_count,
            created_at=saved_meal.created_at.isoformat(),
            updated_at=saved_meal.updated_at.isoformat(),
            nutrition=SavedMealNutritionCreate(**meal_data.nutrition.model_dump())
        )
        
        return BaseResponse(success=True, data=response_data, message="菜品保存成功")
        
    except Exception as e:
        logger.error(f"创建保存菜品失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="保存菜品失败")


@router.post("/from-food-record/{food_record_id}", response_model=BaseResponse[SavedMealResponse])
async def create_saved_meal_from_record(
    food_record_id: int,
    meal_name: str,
    description: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    is_public: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从食物记录创建保存的菜品"""
    try:
        # 获取食物记录
        food_record = db.query(FoodRecord).filter(
            and_(FoodRecord.id == food_record_id, FoodRecord.user_id == current_user.id)
        ).first()
        
        if not food_record:
            raise HTTPException(status_code=404, detail="食物记录不存在")
        
        # 获取营养信息
        nutrition_source = None
        if food_record.nutrition_detail:
            nutrition_source = food_record.nutrition_detail
        elif food_record.analysis_result:
            nutrition_source = food_record.analysis_result.nutrition_facts
        else:
            raise HTTPException(status_code=400, detail="食物记录缺少营养信息")
        
        # 创建保存的菜品
        saved_meal = SavedMeal(
            user_id=current_user.id,
            meal_name=meal_name,
            description=description or food_record.description,
            image_url=food_record.image_url,
            category=category,
            tags=tags,
            is_public=is_public
        )
        db.add(saved_meal)
        db.flush()
        
        # 创建营养信息
        if hasattr(nutrition_source, 'calories'):  # NutritionDetail
            nutrition = SavedMealNutrition(
                saved_meal_id=saved_meal.id,
                calories=float(nutrition_source.calories),
                protein=float(nutrition_source.protein),
                fat=float(nutrition_source.fat),
                carbohydrates=float(nutrition_source.carbohydrates),
                dietary_fiber=float(nutrition_source.dietary_fiber),
                sugar=float(nutrition_source.sugar),
                sodium=float(nutrition_source.sodium),
                cholesterol=float(nutrition_source.cholesterol),
                vitamin_a=float(nutrition_source.vitamin_a),
                vitamin_c=float(nutrition_source.vitamin_c),
                vitamin_d=float(nutrition_source.vitamin_d),
                calcium=float(nutrition_source.calcium),
                iron=float(nutrition_source.iron),
                potassium=float(nutrition_source.potassium)
            )
        else:  # NutritionFacts (from analysis result)
            nutrition = SavedMealNutrition(
                saved_meal_id=saved_meal.id,
                calories=float(nutrition_source.total_calories),
                protein=float(nutrition_source.macronutrients.protein),
                fat=float(nutrition_source.macronutrients.fat),
                carbohydrates=float(nutrition_source.macronutrients.carbohydrates),
                dietary_fiber=float(nutrition_source.macronutrients.dietary_fiber),
                sugar=float(nutrition_source.macronutrients.sugar),
                sodium=float(nutrition_source.vitamins_minerals.sodium or 0),
                cholesterol=float(nutrition_source.vitamins_minerals.cholesterol or 0),
                vitamin_a=float(nutrition_source.vitamins_minerals.vitamin_a or 0),
                vitamin_c=float(nutrition_source.vitamins_minerals.vitamin_c or 0),
                vitamin_d=float(nutrition_source.vitamins_minerals.vitamin_d or 0),
                calcium=float(nutrition_source.vitamins_minerals.calcium or 0),
                iron=float(nutrition_source.vitamins_minerals.iron or 0),
                potassium=float(nutrition_source.vitamins_minerals.potassium or 0)
            )
        
        db.add(nutrition)
        db.commit()
        
        # 构建响应
        nutrition_data = SavedMealNutritionCreate(
            calories=float(nutrition.calories),
            protein=float(nutrition.protein),
            fat=float(nutrition.fat),
            carbohydrates=float(nutrition.carbohydrates),
            dietary_fiber=float(nutrition.dietary_fiber),
            sugar=float(nutrition.sugar),
            sodium=float(nutrition.sodium),
            cholesterol=float(nutrition.cholesterol),
            vitamin_a=float(nutrition.vitamin_a),
            vitamin_c=float(nutrition.vitamin_c),
            vitamin_d=float(nutrition.vitamin_d),
            calcium=float(nutrition.calcium),
            iron=float(nutrition.iron),
            potassium=float(nutrition.potassium)
        )
        
        response_data = SavedMealResponse(
            id=saved_meal.id,
            meal_name=saved_meal.meal_name,
            description=saved_meal.description,
            image_url=saved_meal.image_url,
            category=saved_meal.category,
            tags=saved_meal.tags,
            is_public=saved_meal.is_public,
            usage_count=saved_meal.usage_count,
            favorite_count=saved_meal.favorite_count,
            created_at=saved_meal.created_at.isoformat(),
            updated_at=saved_meal.updated_at.isoformat(),
            nutrition=nutrition_data
        )
        
        return BaseResponse(success=True, data=response_data, message="从食物记录保存菜品成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从食物记录创建保存菜品失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="保存菜品失败")


@router.get("/", response_model=BaseResponse[List[SavedMealResponse]])
async def get_saved_meals(
    category: Optional[str] = Query(None, description="分类筛选"),
    is_public: Optional[bool] = Query(None, description="是否为公共菜品"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取保存的菜品列表"""
    try:
        query = db.query(SavedMeal).outerjoin(SavedMealNutrition)
        
        # 筛选条件
        if is_public is None:
            # 默认显示用户自己的菜品和公共菜品
            query = query.filter(
                or_(SavedMeal.user_id == current_user.id, SavedMeal.is_public == True)
            )
        elif is_public:
            query = query.filter(SavedMeal.is_public == True)
        else:
            query = query.filter(SavedMeal.user_id == current_user.id)
        
        if category:
            query = query.filter(SavedMeal.category == category)
        
        if search:
            query = query.filter(
                or_(
                    SavedMeal.meal_name.contains(search),
                    SavedMeal.description.contains(search)
                )
            )
        
        # 分页
        total = query.count()
        meals = query.order_by(desc(SavedMeal.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        # 获取当前用户的收藏状态
        meal_ids = [meal.id for meal in meals]
        favorites = db.query(UserSavedMealFavorite).filter(
            and_(
                UserSavedMealFavorite.user_id == current_user.id,
                UserSavedMealFavorite.saved_meal_id.in_(meal_ids)
            )
        ).all()
        favorite_meal_ids = {fav.saved_meal_id for fav in favorites}
        
        # 构建响应
        response_data = []
        for meal in meals:
            nutrition_data = None
            if meal.nutrition_template:
                nutrition_data = SavedMealNutritionCreate(
                    serving_size=float(meal.nutrition_template.serving_size),
                    serving_unit=meal.nutrition_template.serving_unit,
                    calories=float(meal.nutrition_template.calories),
                    protein=float(meal.nutrition_template.protein),
                    fat=float(meal.nutrition_template.fat),
                    carbohydrates=float(meal.nutrition_template.carbohydrates),
                    dietary_fiber=float(meal.nutrition_template.dietary_fiber),
                    sugar=float(meal.nutrition_template.sugar),
                    sodium=float(meal.nutrition_template.sodium),
                    cholesterol=float(meal.nutrition_template.cholesterol),
                    vitamin_a=float(meal.nutrition_template.vitamin_a),
                    vitamin_c=float(meal.nutrition_template.vitamin_c),
                    vitamin_d=float(meal.nutrition_template.vitamin_d),
                    calcium=float(meal.nutrition_template.calcium),
                    iron=float(meal.nutrition_template.iron),
                    potassium=float(meal.nutrition_template.potassium)
                )
            
            meal_response = SavedMealResponse(
                id=meal.id,
                meal_name=meal.meal_name,
                description=meal.description,
                image_url=meal.image_url,
                category=meal.category,
                tags=meal.tags,
                is_public=meal.is_public,
                usage_count=meal.usage_count,
                favorite_count=meal.favorite_count,
                created_at=meal.created_at.isoformat(),
                updated_at=meal.updated_at.isoformat(),
                nutrition=nutrition_data,
                is_favorited=meal.id in favorite_meal_ids
            )
            response_data.append(meal_response)
        
        return BaseResponse(
            success=True, 
            data=response_data, 
            message=f"获取成功，共 {total} 个菜品"
        )
        
    except Exception as e:
        logger.error(f"获取保存菜品列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取菜品列表失败")


@router.get("/{meal_id}", response_model=BaseResponse[SavedMealResponse])
async def get_saved_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个保存的菜品详情"""
    try:
        meal = db.query(SavedMeal).filter(SavedMeal.id == meal_id).first()
        
        if not meal:
            raise HTTPException(status_code=404, detail="菜品不存在")
        
        # 检查权限
        if not meal.is_public and meal.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此菜品")
        
        # 检查是否收藏
        is_favorited = False
        if meal.is_public and meal.user_id != current_user.id:
            favorite = db.query(UserSavedMealFavorite).filter(
                and_(
                    UserSavedMealFavorite.user_id == current_user.id,
                    UserSavedMealFavorite.saved_meal_id == meal_id
                )
            ).first()
            is_favorited = favorite is not None
        
        # 构建营养信息
        nutrition_data = None
        if meal.nutrition_template:
            nutrition_data = SavedMealNutritionCreate(
                serving_size=float(meal.nutrition_template.serving_size),
                serving_unit=meal.nutrition_template.serving_unit,
                calories=float(meal.nutrition_template.calories),
                protein=float(meal.nutrition_template.protein),
                fat=float(meal.nutrition_template.fat),
                carbohydrates=float(meal.nutrition_template.carbohydrates),
                dietary_fiber=float(meal.nutrition_template.dietary_fiber),
                sugar=float(meal.nutrition_template.sugar),
                sodium=float(meal.nutrition_template.sodium),
                cholesterol=float(meal.nutrition_template.cholesterol),
                vitamin_a=float(meal.nutrition_template.vitamin_a),
                vitamin_c=float(meal.nutrition_template.vitamin_c),
                vitamin_d=float(meal.nutrition_template.vitamin_d),
                calcium=float(meal.nutrition_template.calcium),
                iron=float(meal.nutrition_template.iron),
                potassium=float(meal.nutrition_template.potassium)
            )
        
        response_data = SavedMealResponse(
            id=meal.id,
            meal_name=meal.meal_name,
            description=meal.description,
            image_url=meal.image_url,
            category=meal.category,
            tags=meal.tags,
            is_public=meal.is_public,
            usage_count=meal.usage_count,
            favorite_count=meal.favorite_count,
            created_at=meal.created_at.isoformat(),
            updated_at=meal.updated_at.isoformat(),
            nutrition=nutrition_data,
            is_favorited=is_favorited
        )
        
        return BaseResponse(success=True, data=response_data, message="获取菜品详情成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取保存菜品详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取菜品详情失败")


@router.put("/{meal_id}", response_model=BaseResponse[SavedMealResponse])
async def update_saved_meal(
    meal_id: int,
    meal_data: SavedMealUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新保存的菜品"""
    try:
        meal = db.query(SavedMeal).filter(
            and_(SavedMeal.id == meal_id, SavedMeal.user_id == current_user.id)
        ).first()
        
        if not meal:
            raise HTTPException(status_code=404, detail="菜品不存在或无权限修改")
        
        # 更新菜品信息
        update_data = meal_data.model_dump(exclude_unset=True, exclude={'nutrition'})
        for field, value in update_data.items():
            setattr(meal, field, value)
        
        # 更新营养信息
        if meal_data.nutrition:
            if meal.nutrition_template:
                nutrition_update = meal_data.nutrition.model_dump()
                for field, value in nutrition_update.items():
                    setattr(meal.nutrition_template, field, value)
            else:
                nutrition = SavedMealNutrition(
                    saved_meal_id=meal.id,
                    **meal_data.nutrition.model_dump()
                )
                db.add(nutrition)
        
        db.commit()
        db.refresh(meal)
        
        # 构建响应 (简化版，实际应该重新查询完整数据)
        return BaseResponse(success=True, data=None, message="菜品更新成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新保存菜品失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="更新菜品失败")


@router.delete("/{meal_id}", response_model=BaseResponse[None])
async def delete_saved_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除保存的菜品"""
    try:
        meal = db.query(SavedMeal).filter(
            and_(SavedMeal.id == meal_id, SavedMeal.user_id == current_user.id)
        ).first()
        
        if not meal:
            raise HTTPException(status_code=404, detail="菜品不存在或无权限删除")
        
        db.delete(meal)
        db.commit()
        
        return BaseResponse(success=True, data=None, message="菜品删除成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除保存菜品失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="删除菜品失败")


@router.post("/{meal_id}/favorite", response_model=BaseResponse[None])
async def toggle_favorite_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """收藏/取消收藏公共菜品"""
    try:
        meal = db.query(SavedMeal).filter(
            and_(SavedMeal.id == meal_id, SavedMeal.is_public == True)
        ).first()
        
        if not meal:
            raise HTTPException(status_code=404, detail="公共菜品不存在")
        
        if meal.user_id == current_user.id:
            raise HTTPException(status_code=400, detail="不能收藏自己的菜品")
        
        # 检查是否已收藏
        favorite = db.query(UserSavedMealFavorite).filter(
            and_(
                UserSavedMealFavorite.user_id == current_user.id,
                UserSavedMealFavorite.saved_meal_id == meal_id
            )
        ).first()
        
        if favorite:
            # 取消收藏
            db.delete(favorite)
            meal.favorite_count = max(0, meal.favorite_count - 1)
            message = "取消收藏成功"
        else:
            # 添加收藏
            favorite = UserSavedMealFavorite(
                user_id=current_user.id,
                saved_meal_id=meal_id
            )
            db.add(favorite)
            meal.favorite_count += 1
            message = "收藏成功"
        
        db.commit()
        return BaseResponse(success=True, data=None, message=message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"收藏/取消收藏菜品失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="操作失败")


@router.post("/{meal_id}/use", response_model=BaseResponse[None])
async def use_saved_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """使用保存的菜品（增加使用计数）"""
    try:
        meal = db.query(SavedMeal).filter(SavedMeal.id == meal_id).first()
        
        if not meal:
            raise HTTPException(status_code=404, detail="菜品不存在")
        
        # 检查权限
        if not meal.is_public and meal.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权使用此菜品")
        
        # 增加使用计数
        meal.usage_count += 1
        db.commit()
        
        return BaseResponse(success=True, data=None, message="使用记录已更新")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"使用保存菜品失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="操作失败")