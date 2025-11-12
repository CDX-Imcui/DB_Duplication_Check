# import json
# from llm_ias_api import LLMIasApi
#
#
# class LLMClient:
#     """
#     LLM客户端封装类
#     用于文本相似度比较，现已切换到国网智能分析平台大模型接口
#     """
#
#     def __init__(self):
#         # 使用新的国网智能分析平台接口
#         self.ias_api = LLMIasApi()
#
#     def compare_texts(self, text1: str, text2: str, field_name: str = "未知字段"):
#         """
#         调用大模型对两个字段进行相似度比较
#
#         Args:
#             text1: 目标文本
#             text2: 候选文本
#             field_name: 字段名称
#
#         Returns:
#             {"score": int, "reason": str} 格式的字典
#         """
#         prompt = f"""
# 你是一个文本相似度分析助手。
# 现在有两个文本需要比较，请完成以下任务：
#
# 1. 根据语义相似度给出一个 0~100 的分数（整数，越高表示越相似）。
# 2. 用简短中文解释打分原因（不超过20字）。
#
# 请严格按照以下 JSON 格式返回结果，不要输出其他多余内容：
#
# {{
#   "score": <int>,
#   "reason": "<string>"
# }}
#
# 下面是待比较的内容：
# - 字段名称: {field_name}
# - 目标文本: {text1}
# - 候选文本: {text2}
# """
#
#         try:
#             # 调用国网智能分析平台接口
#             response = self.ias_api.chat_completions(
#                 messages=[
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0.7,  # 降低随机性，使结果更稳定
#                 max_tokens=500    # 限制输出长度
#             )
#
#             # 检查是否有错误
#             if "error" in response:
#                 return {
#                     "score": 0,
#                     "reason": f"接口错误: {response['error'].get('message', '未知错误')}"
#                 }
#
#             # 解析响应
#             # 根据国网接口文档，响应格式为：
#             # {
#             #   "id": "...",
#             #   "object": "chat.completion",
#             #   "created": ...,
#             #   "choices": [{"message": {"content": "..."}}],
#             #   "usage": {...}
#             # }
#             if "choices" in response and len(response["choices"]) > 0:
#                 content = response["choices"][0].get("message", {}).get("content", "")
#
#                 # 尝试解析 JSON 格式的内容
#                 try:
#                     # 移除可能的markdown代码块标记
#                     content = content.strip()
#                     if content.startswith("```json"):
#                         content = content[7:]
#                     if content.startswith("```"):
#                         content = content[3:]
#                     if content.endswith("```"):
#                         content = content[:-3]
#                     content = content.strip()
#
#                     result = json.loads(content)
#
#                     # 验证返回格式
#                     if "score" in result and "reason" in result:
#                         return {
#                             "score": int(result["score"]),
#                             "reason": str(result["reason"])
#                         }
#                     else:
#                         return {"score": 0, "reason": "返回格式不正确"}
#
#                 except json.JSONDecodeError:
#                     # 如果无法解析为JSON，尝试提取分数和原因
#                     return {"score": 0, "reason": f"解析失败: {content[:50]}"}
#             else:
#                 return {"score": 0, "reason": "响应内容为空"}
#
#         except Exception as e:
#             return {"score": 0, "reason": f"调用失败: {str(e)}"}

#############################################

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

