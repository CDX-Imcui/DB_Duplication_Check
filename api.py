import os
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # 可选：处理跨域
from pydantic import BaseModel
from typing import Dict, Any
from dotenv import load_dotenv
from db_client import DBClient
from llm_client import LLMClient
from duplicate_checker import DuplicateChecker
import hmac
import hashlib

# 加载环境变量
load_dotenv()

# 初始化组件
db = DBClient(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME")
)
llm = LLMClient()
checker = DuplicateChecker(db, llm)

app = FastAPI(title="Demand Duplicate Checker API")

# 可选：允许跨域（根据部署情况决定）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 建议改为具体域名
    allow_methods=["POST"],
    allow_headers=["*"],
)

# -------------------------------
# 验签：获取 secret key
# -------------------------------
SECRET_KEY = os.getenv("SIGN_SECRET_KEY", "your_default_secret_key")
if not SECRET_KEY:
    raise ValueError("SIGN_SECRET_KEY is required in .env")

# def verify_sign(data: Dict[str, Any], sign: str) -> bool:
#     """
#     验证签名是否正确
#     """
#     # 将 data 对象序列化为标准 JSON 字符串（排序、无空格）
#     data_str = json.dumps(data, separators=(',', ':'), sort_keys=True)
#     expected_sign = hmac.new(
#         SECRET_KEY.encode(),
#         data_str.encode(),
#         hashlib.sha256
#     ).hexdigest()
#     # 使用 hmac.compare_digest 防止时序攻击
#     return hmac.compare_digest(expected_sign, sign)

# -------------------------------
# 接口定义
# -------------------------------
@app.post("/")
async def handle_duplications(request: Request):
    """
    统一入口：处理各种 bizType 请求
    """
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    data = body.get("data")
    sign = body.get("sign")

    if not data or not sign:
        raise HTTPException(status_code=400, detail="Missing data or sign")

    # # 验签
    # if not verify_sign(data, sign):
    #     raise HTTPException(status_code=401, detail="Invalid signature")

    biz_type = data.get("bizType")
    biz_content = data.get("bizContent", {})

    if not biz_type:
        raise HTTPException(status_code=400, detail="Missing bizType")

    # 路由不同业务
    if biz_type == "demandDuplication":
        try:
            record_id = biz_content.get("id")
            record_type = biz_content.get("type")
            if not record_id or not record_type:
                raise HTTPException(status_code=400, detail="Missing id or type in bizContent")

            result = checker.check_duplicates(record_id, record_type)
            result["bizType"] = biz_type
            return result
        except Exception as e:
            return {"code": 500, "msg": str(e), "bizType": biz_type, "bizContent": {}}
    else:
        return {"code": 400, "msg": f"Unsupported bizType: {biz_type}", "bizType": biz_type, "bizContent": {}}