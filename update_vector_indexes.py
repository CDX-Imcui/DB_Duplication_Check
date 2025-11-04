#!/usr/bin/env python3
"""
向量索引增量更新脚本
"""

import os
from dotenv import load_dotenv
from db_client import DBClient
from vector_index_builder import VectorIndexBuilder

def main():
    # 加载环境变量
    load_dotenv()
    
    # 初始化数据库客户端
    db = DBClient(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME")
    )
    
    # 创建索引构建器
    builder = VectorIndexBuilder(db)
    
    # 增量更新所有表的索引
    builder.update_all_indexes_incremental()

if __name__ == "__main__":
    main()