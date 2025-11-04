# test_api.py
import json
import hmac
import hashlib
import requests
import time

t1 = time.time()

# ========== 配置 ==========
# API_URL = "http://192.168.56.1:8000/"  # 改成你的服务地址
API_URL = "https://fe6e397606e6.ngrok-free.app/"  # 改成你的服务地址
SECRET_KEY = "your_shared_secret_key"  # 和服务端 .env 里一致

# ========== 构造数据 ==========
data = {
    "bizType": "demandDuplication",
    "bizContent": {
        "id": 19,
        "type": "demandProposal"
    }
}

# ========== 生成签名 ==========
def generate_sign(data_dict, secret):
    # 重要：排序 + 无空格
    data_str = json.dumps(data_dict, separators=(',', ':'), sort_keys=True)
    return hmac.new(
        secret.encode('utf-8'),
        data_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

sign = generate_sign(data, SECRET_KEY)
print("Generated sign:", sign)

# ========== 发送请求 ==========
payload = {
    "data": data,
    "sign": sign
}

response = requests.post(API_URL, json=payload)
print("Status Code:", response.status_code)
print("Response Body:", response.json())
print("Running Time:", time.time() - t1)