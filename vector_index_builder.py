import os
import json
from typing import Dict, Tuple, List, Any, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from db_client import DBClient, TABLE_PK_MAP
import pickle

class VectorIndexBuilder:
    def __init__(self, db_client: DBClient):
        self.db = db_client

        # DEFAULT_MODEL_PATH = r"F:\Downloads\modelscope\models\sentence-transformers\all-MiniLM-L6-v2"
        DEFAULT_MODEL_PATH = r"/DB_Duplication_Check/sentence-transformers/all-MiniLM-L6-v2"
        LOCAL_MODEL_PATH = os.getenv("LOCAL_MODEL_PATH", DEFAULT_MODEL_PATH)
        self.model = SentenceTransformer(LOCAL_MODEL_PATH)
        self.index_dir = "vector_indexes"
        
        # 创建索引存储目录
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)

    def build_and_save_indexes(self):
        """为所有表构建向量索引并保存到磁盘"""
        print("开始构建向量索引...")
        
        for table in TABLE_PK_MAP.keys():
            print(f"正在处理表: {table}")
            self._build_table_index(table)
        
        print("所有向量索引构建完成并已保存到磁盘")

    def _build_table_index(self, table: str):
        """为单个表构建向量索引"""
        # 获取表的所有记录
        records = self.db.get_all_records(table)
        if not records:
            print(f"表 {table} 没有记录，跳过")
            return

        # 收集所有文本内容用于向量化
        texts = []
        for record in records:
            # 将记录的所有文本字段合并为一个文本
            text_fields = [str(record[col]) for col in record.keys() if col != TABLE_PK_MAP[table] and record[col]]
            combined_text = ' '.join(text_fields)
            texts.append(combined_text)

        # 向量化所有文本
        print(f"正在向量化 {len(texts)} 条记录...")
        embeddings = self.model.encode(texts)
        
        # 创建FAISS索引
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # 使用内积相似度
        faiss.normalize_L2(embeddings)  # 归一化向量以获得更好的相似度计算
        index.add(embeddings.astype(np.float32))
        
        # 保存索引到磁盘
        index_file = os.path.join(self.index_dir, f"{table}_index.faiss")
        faiss.write_index(index, index_file)
        
        # 保存记录数据到磁盘
        records_file = os.path.join(self.index_dir, f"{table}_records.pkl")
        with open(records_file, 'wb') as f:
            pickle.dump(records, f)
        
        print(f"表 {table} 的索引已保存: {index_file}")
        print(f"表 {table} 的记录已保存: {records_file}")

    def update_index_incremental(self, table: str, new_records: list = None) -> Optional[Tuple[faiss.Index, List[Dict[str, Any]]]]:
        """
        增量更新指定表的向量索引
        
        Args:
            table: 表名
            new_records: 新记录列表，如果为None则从数据库获取所有记录并重建索引
        """
        print(f"开始增量更新表 {table} 的向量索引...")
        
        # 索引和记录文件路径
        index_file = os.path.join(self.index_dir, f"{table}_index.faiss")
        records_file = os.path.join(self.index_dir, f"{table}_records.pkl")
        
        # 如果索引文件不存在，则构建完整索引
        if not os.path.exists(index_file) or not os.path.exists(records_file):
            print(f"索引文件不存在，构建完整索引...")
            self._build_table_index(table)
            index = faiss.read_index(index_file)
            with open(records_file, 'rb') as f:
                records = pickle.load(f)
            return index, records
        
        # 加载现有索引和记录
        try:
            index = faiss.read_index(index_file)
            with open(records_file, 'rb') as f:
                existing_records = pickle.load(f)
        except Exception as e:
            print(f"加载现有索引失败: {e}，重新构建完整索引...")
            self._build_table_index(table)
            index = faiss.read_index(index_file)
            with open(records_file, 'rb') as f:
                records = pickle.load(f)
            return index, records
        
        # 如果没有提供新记录，则从数据库获取所有记录（相当于重建索引）
        if new_records is None:
            print("未提供新记录，获取数据库中的所有记录...")
            new_records = self.db.get_all_records(table)
            
            # 检查是否需要更新（简单的记录数比较）
            if len(existing_records) == len(new_records):
                print("记录数未发生变化，跳过更新")
        
        # 确定需要添加的新记录
        existing_ids = {record[TABLE_PK_MAP[table]] for record in existing_records}
        records_to_add = [
            record for record in new_records 
            if record[TABLE_PK_MAP[table]] not in existing_ids
        ]
        
        if not records_to_add:
            print("没有需要添加的新记录")
        else:
            print(f"发现 {len(records_to_add)} 条新记录需要添加")
            
        print(f"发现 {len(records_to_add)} 条新记录需要添加")
        
        # 准备新记录的文本内容
        texts = []
        for record in records_to_add:
            text_fields = [str(record[col]) for col in record.keys() if col != TABLE_PK_MAP[table] and record[col]]
            combined_text = ' '.join(text_fields)
            texts.append(combined_text)
        
        if not texts:
            print("没有有效的文本内容需要向量化")
        else:
            # 向量化新记录
            print(f"正在向量化 {len(texts)} 条新记录...")
            new_embeddings = self.model.encode(texts)
            faiss.normalize_L2(new_embeddings)

            # 添加到现有索引
            index.add(new_embeddings.astype(np.float32))

            # 更新记录列表
            existing_records.extend(records_to_add)

        pk = TABLE_PK_MAP[table]
        new_ids = {str(r[pk]) for r in (new_records or [])}

        # 修改检测：主键相同但文本不同
        modified = False
        new_map = {str(r[pk]): r for r in (new_records or [])}
        for i, r in enumerate(existing_records):
            rid = r.get(pk) if isinstance(r, dict) else None
            if rid is None:
                continue
            if str(rid) not in new_ids:
                # 占位为“墓碑行”，保留主键，增加 __deleted__ 标记，不能删除元素因为要保持下标对齐
                existing_records[i] = {pk: rid, "__deleted__": True}  # 标记删除：只改 records，不改 FAISS
                continue
            new_r = new_map.get(str(rid))
            old_data = {k: v for k, v in r.items() if k != pk}
            new_data = {k: v for k, v in new_r.items() if k != pk}
            if old_data != new_data:
                modified = True
                break
        print("【modified:", modified)

        # # 另存为 JSON
        # existing_json_file = os.path.join(self.index_dir, f"{table}_records_existing.json")
        # new_json_file = os.path.join(self.index_dir, f"{table}_records_new.json")
        # try:
        #     with open(existing_json_file, 'w', encoding='utf-8') as f:
        #         json.dump(existing_records, f, ensure_ascii=False, indent=2, default=str)
        #     with open(new_json_file, 'w', encoding='utf-8') as f:
        #         json.dump(new_records or [], f, ensure_ascii=False, indent=2, default=str)
        #     print(f"已导出现有记录到: {existing_json_file}")
        #     print(f"已导出新记录到: {new_json_file}")
        # except Exception as e:
        #     print(f"导出 JSON 失败: {e}")

        if modified:
            texts = []
            existing_records = new_records
            for record in existing_records:
                # 保持你原有的“拼接所有非主键字段”的规则，不改动字段选择逻辑
                text_fields = [str(record[col]) for col in record.keys() if col != pk and record[col]]
                combined_text = ' '.join(text_fields)
                texts.append(combined_text)

            if texts:
                print(f"检测到文本改动，准备全量向量化 {len(texts)} 条记录并重建索引...")
                new_embeddings = self.model.encode(texts)
                faiss.normalize_L2(new_embeddings)
                dim = new_embeddings.shape[1]
                index = faiss.IndexFlatIP(dim)
                index.add(new_embeddings.astype(np.float32))
            else:
                print("存活记录为空，写入空索引...")
                dim = self.model.get_sentence_embedding_dimension()
                index = faiss.IndexFlatIP(dim)
        
        # 保存更新后的索引和记录
        faiss.write_index(index, index_file)
        with open(records_file, 'wb') as f:
            pickle.dump(existing_records, f)
            
        print(f"表 {table} 的索引已更新，当前共有 {len(existing_records)} 条记录")
        return index, existing_records

    def update_all_indexes_incremental(self) -> Dict[str, Tuple[faiss.Index, List[Dict[str, Any]]]]:
        """增量更新所有表的向量索引"""
        print("开始增量更新所有表的向量索引...")
        updated: Dict[str, Tuple[faiss.Index, List[Dict[str, Any]]]] = {}
        for table in TABLE_PK_MAP.keys():
            print(f"正在处理表: {table}")
            # 获取当前表的所有记录用于增量更新
            current_records = self.db.get_all_records(table)
            updated[table] = self.update_index_incremental(table, current_records)
        print("所有表的向量索引增量更新完成")
        return updated


def main():
    """主函数，用于构建所有表的向量索引"""
    from dotenv import load_dotenv
    import os
    
    # 加载环境变量
    load_dotenv()
    
    print((
        os.getenv("DB_HOST"),
        int(os.getenv("DB_PORT", 3306)),
        os.getenv("DB_USER"),
        os.getenv("DB_PASSWORD"),
        os.getenv("DB_NAME")
    ))

    # 初始化数据库客户端
    db = DBClient(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME")
    )
    
    # 构建并保存向量索引
    builder = VectorIndexBuilder(db)
    builder.build_and_save_indexes()

if __name__ == "__main__":
    main()