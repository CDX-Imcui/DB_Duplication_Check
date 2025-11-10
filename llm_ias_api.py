import os
import json
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

# 从环境变量加载配置
IAS_API_BASE_URL = os.getenv("IAS_API_BASE_URL", "http://dmx-api.zj.sgcc.com.cn")
IAS_API_KEY = os.getenv("IAS_API_KEY", "33768df4e44e41d2a5a621065fa7d552")
IAS_MODEL = os.getenv("IAS_MODEL", "[2.0-模型中心]Qwen3-32B-A100")


class LLMIasApi:
    """国网智能分析平台大模型接口客户端"""
    
    def __init__(self):
        self.base_url = IAS_API_BASE_URL
        self.api_key = IAS_API_KEY
        self.model = IAS_MODEL
        
    def _do_request(
        self, 
        endpoint: str, 
        data: Dict[str, Any], 
        content_type: str = "application/json;charset=utf-8"
    ) -> Dict[str, Any]:
        """
        执行HTTP请求的底层方法
        
        Args:
            endpoint: API端点路径（如 /lmp-cloud-ias-server/api/llm/chat/completions/）
            data: 请求体数据
            content_type: 内容类型
            
        Returns:
            API响应的JSON数据
        """
        # 构造完整URL
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # 构造请求头
        headers = {
            "Content-Type": content_type,
            "Authorization": self.api_key
        }
        
        # ========== 请求前打印 ==========
        print("=" * 80)
        print("🚀 LLM API 请求开始")
        print("=" * 80)
        print(f"📍 URL: {url}")
        print(f"🔑 Authorization: {self.api_key[:20]}...{self.api_key[-10:]}")  # 隐藏中间部分
        print(f"📝 Content-Type: {content_type}")
        print(f"📦 请求数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("=" * 80)
        
        try:
            # 发送POST请求
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=60
            )
            
            
            # 解析JSON响应
            result = response.json()
            
            # ========== 请求成功后打印 ==========
            print("=" * 80)
            print("✅ LLM API 请求成功")
            print("=" * 80)
            print(f"📊 状态码: {response.status_code}")
            print(f"⏱️  响应时间: {response.elapsed.total_seconds():.2f}秒")
            print(f"📥 响应数据:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print("=" * 80)
            
            return result
            
        except requests.exceptions.Timeout:
            # ========== 超时错误打印 ==========
            print("=" * 80)
            print("⏰ LLM API 请求超时")
            print("=" * 80)
            print(f"❌ 错误类型: Timeout")
            print(f"⏱️  超时时间: 60秒")
            print("=" * 80)
            
            return {
                "error": {
                    "type": "timeout_error",
                    "message": "请求超时"
                }
            }
        except requests.exceptions.HTTPError as e:
            # ========== HTTP错误打印 ==========
            print("=" * 80)
            print("❌ LLM API HTTP 错误")
            print("=" * 80)
            print(f"📊 状态码: {e.response.status_code}")
            print(f"📄 错误详情:")
            print(e.response.text)
            print("=" * 80)
            
            return {
                "error": {
                    "type": "http_error",
                    "message": f"HTTP错误: {e.response.status_code}",
                    "details": e.response.text
                }
            }
        except requests.exceptions.RequestException as e:
            # ========== 请求异常打印 ==========
            print("=" * 80)
            print("❌ LLM API 请求异常")
            print("=" * 80)
            print(f"⚠️  异常类型: {type(e).__name__}")
            print(f"📄 异常信息: {str(e)}")
            print("=" * 80)
            
            return {
                "error": {
                    "type": "request_error",
                    "message": f"请求异常: {str(e)}"
                }
            }
        except json.JSONDecodeError:
            # ========== JSON解析错误打印 ==========
            raw_text = response.text if 'response' in locals() else None
            print("=" * 80)
            print("❌ LLM API JSON 解析失败")
            print("=" * 80)
            print(f"📄 原始响应内容:")
            print(raw_text[:500] if raw_text else "无响应内容")  # 只打印前500字符
            print("=" * 80)
            
            return {
                "error": {
                    "type": "parse_error",
                    "message": "响应JSON解析失败",
                    "raw_response": raw_text
                }
            }
    
    def chat_completions(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.95,
        top_p: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        # ========== FAKE 数据区域 - 测试时手动切换注释 ==========
        
        # # FAKE 1: 成功响应 - 标准JSON格式
        # return {
        #     "id": "chatcmpl-test-12345",
        #     "object": "chat.completion",
        #     "created": 1699999999,
        #     "choices": [
        #         {
        #             "index": 0,
        #             "message": {
        #                 "role": "assistant",
        #                 "content": '{"score": 85, "reason": "fakefake项目名称高度相似---1111"}'
        #             },
        #             "finish_reason": "stop"
        #         }
        #     ],
        #     "usage": {
        #         "prompt_tokens": 50,
        #         "completion_tokens": 30,
        #         "total_tokens": 80
        #     }
        # }
        
        # # FAKE 2: 成功响应 - 带Markdown代码块的JSON
        # return {
        #     "id": "chatcmpl-test-12346",
        #     "object": "chat.completion",
        #     "created": 1699999999,
        #     "choices": [
        #         {
        #             "index": 0,
        #             "message": {
        #                 "role": "assistant",
        #                 "content": '```json\n{"score": 92, "reason": "内容几乎完全一致"}\n```'
        #             },
        #             "finish_reason": "stop"
        #         }
        #     ],
        #     "usage": {
        #         "prompt_tokens": 50,
        #         "completion_tokens": 30,
        #         "total_tokens": 80
        #     }
        # }
        
        # # FAKE 3: 成功响应 - 低相似度
        # return {
        #     "id": "chatcmpl-test-12347",
        #     "object": "chat.completion",
        #     "created": 1699999999,
        #     "choices": [
        #         {
        #             "index": 0,
        #             "message": {
        #                 "role": "assistant",
        #                 "content": '{"score": 15, "reason": "项目类型完全不同"}'
        #             },
        #             "finish_reason": "stop"
        #         }
        #     ],
        #     "usage": {
        #         "prompt_tokens": 50,
        #         "completion_tokens": 30,
        #         "total_tokens": 80
        #     }
        # }
        
        # # FAKE 4: 错误响应 - 超时错误
        # return {
        #     "error": {
        #         "type": "timeout_error",
        #         "message": "请求超时"
        #     }
        # }
        
        # # FAKE 5: 错误响应 - HTTP错误
        # return {
        #     "error": {
        #         "type": "http_error",
        #         "message": "HTTP错误: 500",
        #         "details": "Internal Server Error"
        #     }
        # }
        
        # # FAKE 6: 错误响应 - 格式错误（不符合JSON规范）
        # return {
        #     "id": "chatcmpl-test-12348",
        #     "object": "chat.completion",
        #     "created": 1699999999,
        #     "choices": [
        #         {
        #             "index": 0,
        #             "message": {
        #                 "role": "assistant",
        #                 "content": "这是一个无效的JSON格式响应"
        #             },
        #             "finish_reason": "stop"
        #         }
        #     ],
        #     "usage": {
        #         "prompt_tokens": 50,
        #         "completion_tokens": 30,
        #         "total_tokens": 80
        #     }
        # }
        
        # # FAKE 7: 错误响应 - 空choices
        # return {
        #     "id": "chatcmpl-test-12349",
        #     "object": "chat.completion",
        #     "created": 1699999999,
        #     "choices": [],
        #     "usage": {
        #         "prompt_tokens": 50,
        #         "completion_tokens": 0,
        #         "total_tokens": 50
        #     }
        # }


        """
        语义大模型对话接口
        
        Args:
            messages: 对话历史，格式为 [{"role": "user", "content": "..."}]
            model: 模型ID，默认使用环境变量配置的模型
            stream: 是否使用流式输出
            temperature: 随机性控制，范围(0, 1.0]，默认0.95
            top_p: 多样性控制，范围[0, 1.0]，默认0.7
            max_tokens: 最大生成token数
            **kwargs: 其他可选参数（presence_penalty, tools, tool_choice等）
            
        Returns:
            API响应数据
            
        示例:
            >>> api = LLMIasApi()
            >>> result = api.chat_completions([
            ...     {"role": "user", "content": "介绍一下国网衢州供电公司"}
            ... ])
        """
        # 构造请求数据
        request_data = {
            "model": model or self.model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
            "top_p": top_p
        }
        
        # 添加可选参数
        if max_tokens is not None:
            request_data["max_tokens"] = max_tokens
            
        # 添加其他可选参数
        for key, value in kwargs.items():
            if key in ["presence_penalty", "tools", "tool_choice", "parallel_tool_calls"]:
                request_data[key] = value
        
        # 发起请求
        endpoint = "/lmp-cloud-ias-server/api/llm/chat/completions/"
        
        return self._do_request(endpoint, request_data)
    
    def chat_completions_v2(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        语义大模型对话接口 V2 版本
        
        V2版本与原接口的区别：流式输出时没有event:data事件类型
        
        Args:
            messages: 对话历史
            model: 模型ID
            **kwargs: 其他参数同 chat_completions
            
        Returns:
            API响应数据
        """
        # 使用 V2 端点
        endpoint = "/lmp-cloud-ias-server/api/llm/chat/completions/V2"
        
        request_data = {
            "model": model or self.model,
            "messages": messages,
            **kwargs
        }
        
        return self._do_request(endpoint, request_data)

