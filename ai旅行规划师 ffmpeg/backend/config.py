import os
from dotenv import load_dotenv

# 基础配置
load_dotenv()


class Config:
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
   ## print(SECRET_KEY)
    DEBUG = True

    # 科大讯飞语音识别配置
    XUNFEI = {
        'appid': os.getenv('XUNFEI_APPID', '你的appid'),
        'api_key': os.getenv('XUNFEI_API_KEY', '你的api_key'),
        'api_secret': os.getenv('XUNFEI_API_SECRET', '你的api_secret')
    }

    # 高德地图API配置
    AMAP = {
        'key': os.getenv('AMAP_KEY', '你的高德地图key')
    }

    # 百度地图API配置
    BAIDU = {
        'ak': os.getenv('BAIDU_AK', 'gvMUm7Z13BdS8Zgm3ZTKXE3DWlLBil2z')
    }

    # 大语言模型配置(阿里云通义千问)
    LLM = {
        'api_key': os.getenv('LLM_API_KEY', '你的api_key'),
        'api_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    }

    # Supabase配置(云端存储)
    SUPABASE = {
        'url': os.getenv('SUPABASE_URL', 'url'),
        'key': os.getenv('SUPABASE_KEY', 'key')

    }


config = Config()

