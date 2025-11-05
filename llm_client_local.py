import os
import json
from dotenv import load_dotenv
import logging

# --- 1. 导入你测试代码中需要的库 ---
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

load_dotenv()
# --- 2. 从 .env 或使用你的本地路径加载模型 ---
# (建议把这个路径 "F:\..." 也加入到 .env 文件中，例如 QWEN_MODEL_PATH=...)
# 这里我们使用 'r' 来确保 Windows 路径被正确读取
# DEFAULT_MODEL_PATH = r"F:\Downloads\modelscope\models\Qwen\Qwen3-Reranker-0___6B"
LOCAL_MODEL_PATH = os.getenv("QWEN_MODEL_PATH")


class LLMClient:
    def __init__(self):
        # --- 3. 修改 __init__：不再获取 API Key，而是加载本地模型 ---
        logging.info(f"正在从本地路径加载模型: {LOCAL_MODEL_PATH}")
        self.model = None
        try:
            # 加载你在 test_code.py 中使用的模型
            self.model = SentenceTransformer(LOCAL_MODEL_PATH)
            logging.info("本地模型加载成功。")
        except Exception as e:
            logging.error(f"加载本地模型 {LOCAL_MODEL_PATH} 失败: {e}")
            logging.error("请检查路径是否正确，以及是否已安装 sentence_transformers 和 torch。")

    def compare_texts(self, text1: str, text2: str, field_name: str = "未知字段"):
        """
        重写此方法：使用本地 embedding 模型计算相似度。
        不再调用通义 API。
        """

        # 检查模型是否加载成功
        if self.model is None:
            return {"score": 0, "reason": "本地模型未加载"}

        try:
            # --- 4. 替换核心逻辑：使用你 test_client.py 中的方法 ---

            # 1. 编码：获取两个文本的向量
            embeddings_np = self.model.encode([text1, text2])

            # 2. 准备计算：将 1D 向量 reshape 为 2D
            vec_a = embeddings_np[0].reshape(1, -1)
            vec_b = embeddings_np[1].reshape(1, -1)

            # 3. 计算：获取余弦相似度
            #    结果是一个 2D 矩阵，我们取 [0][0] 得到那个浮点数值
            sim = cosine_similarity(vec_a, vec_b)[0][0]

            # 4. 转换：将相似度 (0.0 ~ 1.0) 转换为 0-100 的整数分数
            score = int(np.round(sim * 100))

            # 5. 返回：
            #    注意：我们无法生成 "reason"，所以提供一个占位符
            return {
                "score": score,
                "reason": "本地模型相似度计算"
            }

        except Exception as e:
            logging.error(f"本地模型推理失败: {e}")
            return {"score": 0, "reason": f"调用失败: {e}"}