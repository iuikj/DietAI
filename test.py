import unittest
import asyncio
from agent.disease_analysis_agent.agent import graph
from agent.disease_analysis_agent.utils.states import InputState
from agent.disease_analysis_agent.utils.configuration import Configuration


class TestDiseaseAnalysisAgent(unittest.TestCase):
    """疾病分析Agent测试类"""
    
    def setUp(self):
        """测试前的设置"""
        # 使用agent.py中已经编译好的graph
        self.graph = graph
        
        # 构造配置
        self.config = Configuration(
            vision_model_provider="openai",
            vision_model="gpt-4o",
            analysis_model_provider="openai",
            analysis_model="gpt-4o"
        )
    
    def test_extract_mode(self):
        """测试模式A：有user_input时抽取疾病/过敏原信息"""
        print("=== 测试模式A：抽取疾病/过敏原信息 ===")
        
        # 示例输入 - 有user_input
        input_state: InputState = {
            "user_input": "我有高血压，还有花生过敏，最近血压有点高",
            "foodrecord": None,
            "disease": None,
            "allergen": None,
            "nutritiondetail": None
        }
        
        # 执行 graph
        result = asyncio.run(self.graph.ainvoke(input_state, config=self.config.__dict__))
        
        print("抽取结果:")
        print(f"疾病信息: {result.get('disease')}")
        print(f"过敏原信息: {result.get('allergen')}")
        print(f"当前步骤: {result.get('current_step')}")
        print()
        
        # 验证结果 - 有user_input时，流程在extract_disease_allergy_info后直接结束
        self.assertIsNotNone(result.get('disease'), "应该提取到疾病信息")
        self.assertIsNotNone(result.get('allergen'), "应该提取到过敏原信息")
        self.assertEqual(result.get('current_step'), "extracted_disease_allergy", "当前步骤应该是extracted_disease_allergy")
        # 有user_input时不会生成disease_analysis和formatted_output
        self.assertIsNone(result.get('disease_analysis'), "有user_input时不应该生成disease_analysis")
        self.assertIsNone(result.get('formatted_output'), "有user_input时不应该生成formatted_output")
    
    def test_analysis_mode(self):
        """测试模式B：无user_input时进行疾病风险分析"""
        print("=== 测试模式B：疾病风险分析 ===")
        
        # 示例输入 - 无user_input，有结构化数据
        input_state: InputState = {
            "user_input": None,
            "foodrecord": {
                "record_date": "2025-01-15",
                "meal_type": 2,  # 午餐
                "food_name": "红烧牛肉饭",
                "description": "米饭、红烧牛肉、西兰花、胡萝卜"
            },
            "disease": {
                "disease_code": "I10",
                "disease_name": "高血压",
                "severity_level": 2,
                "diagnosed_date": "2023-01-15",
                "notes": "需控制钠摄入，避免血压波动"
            },
            "allergen": {
                "allergen_type": 1,
                "allergen_name": "花生",
                "severity_level": 2,
                "reaction_description": "皮肤瘙痒，呼吸困难"
            },
            "nutritiondetail": {
                "food_record_id": 1,
                "calories": 850,
                "protein": 45,
                "fat": 35,
                "carbohydrates": 85,
                "dietary_fiber": 8,
                "sugar": 12,
                "sodium": 1200,  # 高钠，对高血压不利
                "cholesterol": 120,
                "vitamin_a": 800,
                "vitamin_c": 45,
                "vitamin_d": 2,
                "calcium": 180,
                "iron": 8,
                "potassium": 650
            }
        }
        
        # 执行 graph
        result = asyncio.run(self.graph.ainvoke(input_state, config=self.config.__dict__))
        
        print("分析结果:")
        print(f"疾病分析: {result.get('disease_analysis')}")
        print(f"格式化输出: {result.get('formatted_output')}")
        print(f"当前步骤: {result.get('current_step')}")
        print()
        
        # 验证结果
        self.assertIsNotNone(result.get('disease_analysis'), "应该生成疾病分析结果")
        self.assertIsNotNone(result.get('formatted_output'), "应该生成格式化输出")
        self.assertEqual(result.get('current_step'), "completed", "当前步骤应该是completed")
    
    def test_empty_input(self):
        """测试空输入情况"""
        print("=== 测试空输入情况 ===")
        
        # 空输入
        input_state: InputState = {
            "user_input": None,
            "foodrecord": None,
            "disease": None,
            "allergen": None,
            "nutritiondetail": None
        }
        
        # 执行 graph
        result = asyncio.run(self.graph.ainvoke(input_state, config=self.config.__dict__))
        
        print("空输入结果:")
        print(f"疾病分析: {result.get('disease_analysis')}")
        print(f"格式化输出: {result.get('formatted_output')}")
        print(f"当前步骤: {result.get('current_step')}")
        print()
        
        # 验证结果 - 空输入时应该设置错误信息
        self.assertIsNone(result.get('disease_analysis'), "空输入时不应该生成分析结果")
        self.assertIsNotNone(result.get('error_message'), "空输入时应该设置错误信息")
        self.assertEqual(result.get('current_step'), "format_final_response", "当前步骤应该是format_final_response")


if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2)
