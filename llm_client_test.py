import json
from llm_client import LLMClient

    
if __name__ == "__main__":
    client = LLMClient()
    
    client.compare_texts(
        text1="智能电网建设项目",
        text2="智慧电网建设方案",
        field_name="测试字段",
    )