import json
import requests
from config import config
import os
from openai import OpenAI


def generate_itinerary(user_input):
    """使用大语言模型生成旅行计划"""
    try:
        api_key = config.LLM["api_key"]
        api_url = config.LLM["api_url"]
        print(api_url)
        # 构造提示词
        prompt = f"""
        作为专业AI旅行规划师，请根据用户需求生成详细旅行计划。
        用户需求: {user_input}
        以json格式返回
        1. 行程标题(title)
        2. 每日行程安排(daily_schedule)：按天划分，包含时间点和活动
        3. 住宿推荐(accommodation)：包含推荐酒店和理由，使用city，hotel，reason
        4. 交通方式(transportation)：各地点间的交通方式及费用换算为人民币，使用route，method，cost_per_person
        5. 景点推荐(attractions)：包含简介和门票信息和地理位置（使用经纬度）,使用name，description，ticket_price，address
        6. 餐厅推荐(restaurants)：包含菜系和人均消费换算为人民币，使用name，cuisine，average_cost
        7. 预算明细(budget_details)：分类列出各项预计费用换算成人民币
        8. 总预算(total_budget)：换算成人民币
        9. 旅行注意事项(notes)：根据目的地和人群定制
        10.使用 cost_per_person ticket_price average_cost
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        client = OpenAI(
            # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
            # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
            api_key=config.LLM['api_key'],
            # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        completion = client.chat.completions.create(
            model="qwen-plus",  # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            messages=[
                {'role': 'system', 'content': prompt}
            ]
        )
        print(completion.choices[0].message.content)
        return completion.choices[0].message.content
    except json.JSONDecodeError:
        return {"error": "行程格式错误，无法解析"}
    except Exception as e:
        return {"error": f"语言模型获取不到: {str(e)}"}


def analyze_budget(itinerary_id, expenses, original_budget, note=None):
    """分析预算执行情况"""
    try:
        total_spent = sum(float(exp['amount']) for exp in expenses)
        remaining = float(original_budget) - total_spent

        # 按类别统计
        category_stats = {}
        for exp in expenses:
            cat = exp['category']
            category_stats[cat] = category_stats.get(cat, 0) + float(exp['amount'])

        # 生成AI建议
        extra_note = f"\n用户语音备注: {note}" if note else ""
        prompt = f"""
        预算分析:
        原始预算: {original_budget}元
        已花费: {total_spent}元
        剩余预算: {remaining}元
        花费分类: {category_stats}
        {extra_note}

        请给出预算调整建议，控制在200字以内。
        """

        api_key = config.LLM["api_key"]
        api_url = config.LLM["api_url"]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        client = OpenAI(
            # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
            # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
            api_key=config.LLM['api_key'],
            # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        completion = client.chat.completions.create(
            model="qwen-plus",  # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            messages=[
                {'role': 'system', 'content': prompt}
            ]
        )
        print(completion.choices[0].message.content)
        #return completion.choices[0].message.content
        suggestion = completion.choices[0].message.content
        return {
            "itinerary_id": itinerary_id,
            "original_budget": original_budget,
            "total_spent": round(total_spent, 2),
            "remaining_budget": round(remaining, 2),
            "category_breakdown": category_stats,
            "suggestions": suggestion
        }

    except Exception as e:
        return {"error": f"预算分析失败: {str(e)}"}
