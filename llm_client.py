import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

TONGYI_API_KEY = os.getenv("TONGYI_API_KEY")
TONGYI_API_URL = os.getenv("TONGYI_API_URL")
TONGYI_MODEL = os.getenv("TONGYI_MODEL", "qwen-plus")

class LLMClient:
    def __init__(self):
        self.api_key = TONGYI_API_KEY
        self.url = TONGYI_API_URL
        self.model = TONGYI_MODEL

    def compare_texts(self, text1: str, text2: str, field_name: str = "未知字段"):
        """调用通义大模型对两个字段进行相似度比较"""
        prompt = f"""
你是一个文本相似度分析助手。  
现在有两个文本需要比较，请完成以下任务：  

1. 根据语义相似度给出一个 0~100 的分数（整数，越高表示越相似）。  
2. 用简短中文解释打分原因（不超过20字）。  

请严格按照以下 JSON 格式返回结果，不要输出其他多余内容：  

{{
  "score": <int>,   
  "reason": "<string>"
}}

下面是待比较的内容：  
- 字段名称: {field_name}  
- 目标文本: {text1}  
- 候选文本: {text2}  
"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "input": {"messages": [{"role": "user", "content": prompt}]}
        }

        try:
            response = requests.post(self.url, headers=headers, json=payload, timeout=30)
            result = response.json()
            # 解析 LLM 输出
            raw_output = result["output"]["text"]
            return json.loads(raw_output)
        except Exception as e:
            return {"score": 0, "reason": f"调用失败: {e}"}
