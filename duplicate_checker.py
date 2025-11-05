import json
import os
from typing import Dict, Any, List, Tuple
try:
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import pickle
    VECTOR_SIMILARITY_AVAILABLE = True
except ImportError:
    VECTOR_SIMILARITY_AVAILABLE = False
    print("警告: 未安装向量相似度依赖包，将使用默认的RapidFuzz")
    from rapidfuzz import fuzz

from db_client import DBClient, TABLE_PK_MAP
from llm_client import LLMClient
from vector_index_builder import VectorIndexBuilder

class DuplicateChecker:
    def __init__(self, db: DBClient, llm: LLMClient):
        self.db = db
        self.llm = llm
        self.index_dir = "vector_indexes"
        # 创建索引构建器
        self.builder = VectorIndexBuilder(db)
        
        if VECTOR_SIMILARITY_AVAILABLE:
            # 初始化句子转换模型
            # self.model = SentenceTransformer(r"F:\Downloads\modelscope\models\sentence-transformers")
            self.model = SentenceTransformer(r"/DB_Duplication_Check/sentence-transformers/all-MiniLM-L6-v2")
            # 存储每个表的向量索引
            self.vector_indexes: Dict[str, Tuple[faiss.Index, List[Dict[str, Any]]]] = {}
            # 尝试从磁盘加载向量索引
            self._load_vector_indexes()
        else:
            self.model = None
            self.vector_indexes = None


    def _load_vector_indexes(self):
        """从磁盘加载向量索引"""
        if not os.path.exists(self.index_dir):
            print("向量索引目录不存在，将使用实时构建")
            return
            
        print("正在从磁盘加载向量索引...")
        for table in TABLE_PK_MAP.keys():
            index_file = os.path.join(self.index_dir, f"{table}_index.faiss")
            records_file = os.path.join(self.index_dir, f"{table}_records.pkl")
            
            if os.path.exists(index_file) and os.path.exists(records_file):
                try:
                    # 加载FAISS索引
                    index = faiss.read_index(index_file)
                    
                    # 加载记录数据
                    with open(records_file, 'rb') as f:
                        records = pickle.load(f)
                    
                    self.vector_indexes[table] = (index, records)
                    print(f"已加载表 {table} 的索引和记录 (共{len(records)}条记录)")
                except Exception as e:
                    print(f"加载表 {table} 的索引失败: {e}")
                    self.vector_indexes[table] = (None, [])
            else:
                print(f"表 {table} 的索引文件不存在，将在需要时实时构建")
                self.vector_indexes[table] = (None, [])


    def build_vector_index(self, table: str):
        """为指定表构建向量索引"""
        if not VECTOR_SIMILARITY_AVAILABLE:
            return
            
        # 获取表的所有记录
        records = self.db.get_all_records(table)
        if not records:
            self.vector_indexes[table] = (None, [])
            return

        # 收集所有文本内容用于向量化
        texts = []
        for record in records:
            # 将记录的所有文本字段合并为一个文本
            text_fields = [str(record[col]) for col in record.keys() if col != TABLE_PK_MAP[table] and record[col]]
            combined_text = ' '.join(text_fields)
            texts.append(combined_text)

        # 向量化所有文本
        embeddings = self.model.encode(texts)
        
        # 创建FAISS索引
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # 使用内积相似度
        faiss.normalize_L2(embeddings)  # 归一化向量以获得更好的相似度计算
        index.add(embeddings.astype(np.float32))
        
        # 保存索引和对应的记录
        self.vector_indexes[table] = (index, records)


    def vector_similarity(self, text1: str, text2: str) -> float:
        """使用向量计算两个文本的相似度"""
        if not VECTOR_SIMILARITY_AVAILABLE:
            return 0.0
            
        # 向量化两个文本
        embeddings = self.model.encode([text1, text2])
        # 归一化向量
        faiss.normalize_L2(embeddings)
        # 计算余弦相似度（内积）
        similarity = np.dot(embeddings[0], embeddings[1])
        # 转换为0-100的分数
        return float(similarity * 100)
        
    def rough_similarity(self, text1: str, text2: str) -> int:
        """快速相似度计算（粗筛阶段）"""
        if VECTOR_SIMILARITY_AVAILABLE:
            return int(self.vector_similarity(text1, text2))
        else:
            return fuzz.token_sort_ratio(str(text1), str(text2))

    def ensure_singleTarget_in_index(self, table: str, target_id: int, row: dict | None = None, text_cols: list[str] | None = None):
        """若已有该表索引，则确保目标记录已被增量追加；若缺依赖则直接跳过。"""
        if not VECTOR_SIMILARITY_AVAILABLE:
            return  # 回退路径下不做索引维护
        pair = self.vector_indexes.get(table)  # 返回table表的元组 (index, records)
        if not pair or pair[0] is None:
            return  # 没有已载入索引就不动，build_vector_index 会重建
        index, records = pair
        pk_name = TABLE_PK_MAP[table]
        if any(str(r[pk_name]) == str(target_id) for r in records):
            return  # 已存在向量索引，直接返回

        parts = [str(row[c]) for c in text_cols if row.get(c)]  # 拼成一个单一的字符串，供后续向量化使用
        joined = " ".join(parts).strip()
        if not joined:
            return

        vec = self.model.encode([joined])[0].astype(np.float32, copy=False)
        faiss.normalize_L2(vec.reshape(1, -1))
        index.add(vec.reshape(1, -1))  # index 是一个 FAISS 向量索引对象，这里直接添加新向量
        # 只向内存 records 追加一条字典行，字段用于后续 LLM 细筛无需改动
        new_row = {pk_name: target_id}  # 一条用于内存维护的记录字典，用来和索引里的向量一一对应，包含主键和需要的文本字段
        for c in text_cols:
            new_row[c] = row.get(c)
        records.append(new_row)
        self.vector_indexes[table] = (index, records)

    def alreadyExist(self, table: str, target_id: int):
        """判断目标记录是否已在索引中"""
        pair = self.vector_indexes.get(table)  # 返回table表的元组 (index, records)
        if not pair or pair[0] is None:
            return  # 没有已载入索引就不动，build_vector_index 会重建
        index, records = pair
        pk_name = TABLE_PK_MAP[table]
        if any(str(r[pk_name]) == str(target_id) for r in records):
            return True  # 已存在向量索引，直接返回
        return False

    def check_duplicates(self, target_id: int, target_type: str) -> Dict[str, Any]:
        result = {"code": 100, "msg": "success", "bizType": None, "bizContent": {"similarDemands": []}}

        target_record = self.db.get_record_by_id(target_type, target_id)
        if not target_record:
            return {"code": 404, "msg": f"No record found in {target_type} with id={target_id}"}
        target_text_cols = self.db.get_text_columns(target_type)

        # 构建所有表的向量索引（如果尚未构建且未从磁盘加载、或者有新的记录被添加）
        if VECTOR_SIMILARITY_AVAILABLE:
            for table in TABLE_PK_MAP.keys():
                if table not in self.vector_indexes or self.vector_indexes[table][0] is None:
                    print(f"正在为表 {table} 构建向量索引...")
                    self.build_vector_index(table)
            # 增量更新所有表的索引
            updated = self.builder.update_all_indexes_incremental()
            self.vector_indexes.update(updated)

        top_candidates = []
        column_table = {}
        for table in TABLE_PK_MAP.keys():
            if table == target_type:
                common_cols = target_text_cols
                column_table[table] = common_cols
            else:
                candidate_text_cols = self.db.get_text_columns(table)
                common_cols = set(target_text_cols) & set(candidate_text_cols)
                column_table[table] = common_cols

            if not common_cols:
                continue

            if VECTOR_SIMILARITY_AVAILABLE:
                # 使用向量相似度检索替代RapidFuzz
                index, records = self.vector_indexes[table]
                if index is None or not records:
                    continue

                # 准备目标文本
                target_texts = [str(target_record[col]) for col in common_cols if target_record.get(col)]
                target_combined_text = ' '.join(target_texts)
                
                # 向量化目标文本
                target_embedding = self.model.encode([target_combined_text])
                faiss.normalize_L2(target_embedding)
                
                # 搜索最相似的6条记录（多搜索一条，后面会移除目标数据本身）
                search_count = min(6, len(records))
                scores, indices = index.search(target_embedding.astype(np.float32), search_count)
                
                # 收集候选结果
                scored_candidates = []
                for i, idx in enumerate(indices[0]):
                    if idx < len(records):  # 确保索引有效
                        # 如果是目标数据本身，跳过（相似度最高的那条）
                        if table == target_type and records[idx][TABLE_PK_MAP[table]] == target_id:
                            continue
                        scored_candidates.append((float(scores[0][i]) * 100, records[idx], table))
                
                # 合并到top_candidates中，并确保最多只有5个候选者
                top_candidates.extend(scored_candidates[:5])
            else:
                # 原有逻辑：使用RapidFuzz
                candidates = self.db.get_all_records(table)

                # 1️⃣ 先用快速相似度筛选前 5 条
                scored_candidates = []
                for candidate in candidates:
                    # 跳过目标数据本身
                    if table == target_type and candidate[TABLE_PK_MAP[table]] == target_id:
                        continue
                        
                    rough_scores = []
                    for col in common_cols:
                        if target_record.get(col) and candidate.get(col):
                            rough_scores.append(self.rough_similarity(target_record[col], candidate[col]))
                    if rough_scores:
                        avg_score = sum(rough_scores) / len(rough_scores)
                        scored_candidates.append((avg_score, candidate, table))

                # 获取前5个最相似的候选者
                scored_candidates = sorted(scored_candidates, key=lambda x: x[0], reverse=True)[:5]
                top_candidates.extend(scored_candidates)

        # 按相似度排序并取前5个
        top_candidates = sorted(top_candidates, key=lambda x: x[0], reverse=True)[:5]

        # 2️⃣ 再调用 LLM 做精细比对
        for _, candidate, table in top_candidates:
            alike_fields = {}
            scores = []
            for col in column_table[table]:
                target_val = target_record.get(col)
                candidate_val = candidate.get(col)
                if target_val and candidate_val:
                    cmp_result = self.llm.compare_texts(str(target_val), str(candidate_val), col)
                    score = cmp_result.get("score", 0)
                    if score > 0:
                        alike_fields[col] = {
                            "target_content": target_val,
                            "candidate_content": candidate_val,
                            "score": score,
                            "reason": cmp_result.get("reason", "无")
                        }
                    scores.append(cmp_result.get("score", 0))

            if scores:
                avg_score = sum(scores) / len(scores)
                result["bizContent"]["similarDemands"].append({
                    "type": table,
                    "id": candidate[TABLE_PK_MAP[table]],
                    "score": avg_score,
                    "alikeFields": alike_fields
                })

        return result