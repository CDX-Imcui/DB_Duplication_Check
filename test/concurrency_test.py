import asyncio
import aiohttp
import time
import json
import hmac
import hashlib
from datetime import datetime

# API配置
API_URL = "http://192.168.56.1:8000/"
SECRET_KEY = "your_sign_secret_key"

# 测试数据
test_requests = [
    {
        "data": {
            "bizType": "demandDuplication",
            "bizContent": {
                "id": 24,
                "type": "demandProposal"
            }
        }
    },
    {
        "data": {
            "bizType": "demandDuplication",
            "bizContent": {
                "id": 25,
                "type": "demandProposal"
            }
        }
    },
    {
        "data": {
            "bizType": "demandDuplication",
            "bizContent": {
                "id": 26,
                "type": "demandProposal"
            }
        }
    }
]

def generate_sign(data_dict, secret):
    """生成签名"""
    data_str = json.dumps(data_dict, separators=(',', ':'), sort_keys=True)
    return hmac.new(
        secret.encode('utf-8'),
        data_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

async def send_request(session, request_data):
    """发送单个请求"""
    # 添加签名
    request_data["sign"] = generate_sign(request_data["data"], SECRET_KEY)
    
    start_time = time.time()
    try:
        async with session.post(API_URL, json=request_data) as response:
            result = await response.json()
            end_time = time.time()
            return {
                "status": response.status,
                "response_time": end_time - start_time,
                "result": result
            }
    except Exception as e:
        end_time = time.time()
        return {
            "status": "error",
            "response_time": end_time - start_time,
            "error": str(e)
        }

async def concurrent_test(concurrent_requests=20):
    """并发测试"""
    print(f"开始并发测试，并发请求数: {concurrent_requests}")
    
    async with aiohttp.ClientSession() as session:
        # 准备请求任务
        tasks = []
        for i in range(concurrent_requests):
            # 循环使用测试数据
            request_data = test_requests[i % len(test_requests)]
            tasks.append(send_request(session, request_data.copy()))
        
        # 记录开始时间
        start_time = time.time()
        
        # 并发执行所有请求
        results = await asyncio.gather(*tasks)
        
        # 记录结束时间
        end_time = time.time()
        
        # 分析结果
        total_time = end_time - start_time
        successful_requests = sum(1 for r in results if r["status"] == 200)
        failed_requests = concurrent_requests - successful_requests
        avg_response_time = sum(r["response_time"] for r in results) / concurrent_requests
        
        test_result = {
            "test_time": datetime.now().isoformat(),
            "concurrent_requests": concurrent_requests,
            "total_time": total_time,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "avg_response_time": avg_response_time,
            "throughput": concurrent_requests/total_time,
            "details": []
        }
        
        print(f"\n=== 测试结果 ===")
        print(f"总请求数: {concurrent_requests}")
        print(f"成功请求数: {successful_requests}")
        print(f"失败请求数: {failed_requests}")
        print(f"总耗时: {total_time:.2f} 秒")
        print(f"平均响应时间: {avg_response_time:.2f} 秒")
        print(f"吞吐量: {concurrent_requests/total_time:.2f} 请求/秒")
        
        # 显示每个请求的详细信息
        print(f"\n=== 详细信息 ===")
        for i, result in enumerate(results):
            detail = {
                "request_id": i+1,
                "status": result['status'],
                "response_time": result['response_time']
            }
            
            print(f"请求 {i+1}: 状态={result['status']}, "
                  f"响应时间={result['response_time']:.2f}秒")
                  
            if "error" in result:
                detail["error"] = result['error']
                print(f"  错误: {result['error']}")
            else:
                detail["result_summary"] = {
                    "code": result['result'].get('code', 'N/A'),
                    "msg": result['result'].get('msg', 'N/A'),
                    "similar_demands_count": len(result['result'].get('bizContent', {}).get('similarDemands', []))
                }
            
            test_result["details"].append(detail)
        
        return test_result

def save_results_to_file(results):
    """将测试结果保存到本地文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"concurrency_test_results_{timestamp}.json"
    
    output_data = {
        "test_suite_time": datetime.now().isoformat(),
        "test_results": results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试结果已保存到文件: {filename}")
    return filename

async def main():
    """主函数"""
    print("API并发能力测试")
    print("=" * 50)
    
    # 只进行20用户并发测试
    print(f"\n测试并发数: 20")
    print("-" * 30)
    result = await concurrent_test(20)
    
    # 保存结果到文件
    save_results_to_file([result])

if __name__ == "__main__":
    asyncio.run(main())