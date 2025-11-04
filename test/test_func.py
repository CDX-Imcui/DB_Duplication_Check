import os
import json
from dotenv import load_dotenv
from db_client import DBClient
from llm_client_local import LLMClient
from duplicate_checker import DuplicateChecker
import time

load_dotenv()

if __name__ == "__main__":
    t1 = time.time()
    # 初始化数据库和 LLM
    db = DBClient(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME")
    )
    llm = LLMClient()
    checker = DuplicateChecker(db, llm)

    # 示例：查找 demandProposal 表 id=24 的相似数据
    output = checker.check_duplicates(24, "demandProposal")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"running time: {time.time() - t1}")
