from sqlalchemy import Column, Integer, String, Date, Float, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from shared.models.database import Base
from datetime import datetime

class Allergy(Base):
    __tablename__ = 'allergy'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    allergen_type = Column(Integer, nullable=False, comment="过敏原类型：1食物2药物3环境4其他")
    allergen_name = Column(String(100), nullable=False)
    severity_level = Column(Integer, nullable=True)
    reaction_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Disease(Base):
    __tablename__ = 'disease'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    disease_code = Column(String(20), nullable=True)
    disease_name = Column(String(200), nullable=False)
    severity_level = Column(Integer, nullable=True)
    diagnosed_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class DiseaseAnalysisResult(Base):
    __tablename__ = 'disease_analysis_result'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    disease_id = Column(Integer, ForeignKey('disease.id'), nullable=False)
    allergen_id = Column(Integer, ForeignKey('allergy.id'), nullable=True)
    analysis_time = Column(DateTime, default=datetime.utcnow)
    risky_nutrients = Column(JSON, nullable=True, comment="需注意的营养成分列表")
    risk_explanations = Column(JSON, nullable=True, comment="风险说明列表")
    avoid_foods = Column(JSON, nullable=True, comment="建议避免的食物列表")
    health_tips = Column(JSON, nullable=True, comment="个性化健康建议列表")
    agent_raw_result = Column(JSON, nullable=True, comment="Agent原始返回结果")
    formatted_output = Column(Text, nullable=True, comment="格式化文本输出")
    created_at = Column(DateTime, default=datetime.utcnow)

    disease = relationship('Disease', backref='analysis_results')
    allergen = relationship('Allergy', backref='analysis_results') 