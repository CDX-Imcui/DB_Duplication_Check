# DB-Duplication-Check-3-vecdb

该项目用于检测数据库中的重复条目，结合向量数据库进行相似性比对。

## 功能特性

- 数据库连接与查询
- 重复检测逻辑
- LLM辅助检测（可选）
- 提供REST API接口
- 向量相似度检索（替代传统的文本相似度计算）

## 技术架构

- FastAPI：构建API服务
- PyMySQL：连接MySQL数据库
- FAISS：向量相似度计算
- Sentence Transformers：文本向量化
- 通义千问API：语义相似度分析

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用说明

### 1. 配置环境变量

复制 [.env.example](file:///C:/PycharmProject/DB-Duplication-Check-3-vecdb/.env) 文件为 [.env](file:///C:/PycharmProject/DB-Duplication-Check-3-vecdb/.env) 并填写相应配置：

```bash
cp .env.example .env
```

配置项包括：
- 数据库连接信息
- 通义大模型API密钥
- 签名密钥

### 2. 构建向量索引（可选但推荐）

为了提高API响应速度，建议预先构建向量索引：

```bash
python vector_index_builder.py
```

该脚本会：
- 连接数据库
- 读取所有表的文本数据
- 使用Sentence-BERT将文本转换为向量
- 使用FAISS构建向量索引
- 将索引保存到本地磁盘（vector_indexes目录）

### 3. 向量索引增量更新

当数据库中的数据发生变化时，可以使用增量更新功能来更新向量索引，而无需重建整个索引：

```bash
# 增量更新所有表的向量索引
python -c "from vector_index_builder import VectorIndexBuilder; from db_client import DBClient; import os; db = DBClient(os.getenv('DB_HOST'), int(os.getenv('DB_PORT', 3306)), os.getenv('DB_USER'), os.getenv('DB_PASSWORD'), os.getenv('DB_NAME')); builder = VectorIndexBuilder(db); builder.update_all_indexes_incremental()"
```

或者在代码中使用：
```python
from vector_index_builder import VectorIndexBuilder
from db_client import DBClient
import os

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

# 或者增量更新单个表的索引
builder.update_index_incremental("demandProposal")
```

### 4. 启动API服务

有两种方式启动服务：

#### 开发模式
```bash
python start_server.py --mode dev
```
或者
```bash
uvicorn api:app --reload
```

#### 生产模式（多Worker部署）
```bash
python start_server.py --mode prod
```

在Unix/Linux/macOS系统上，生产模式使用Gunicorn配合多个Uvicorn worker。
在Windows系统上，生产模式使用Uvicorn的多worker模式。

你也可以直接使用以下命令：
```bash
# Unix/Linux/macOS
gunicorn -c gunicorn.conf.py api:app

# Windows
uvicorn api:app --workers 4
```

生产模式使用多Worker部署，可以显著提高并发处理能力。

### 5. 调用API

向API发送POST请求进行重复检测：

```json
{
  "data": {
    "bizType": "demandDuplication",
    "bizContent": {
      "id": 123,
      "type": "demandProposal"
    }
  },
  "sign": "签名"
}
```

## 向量索引管理

### 索引存储

向量索引默认存储在 `vector_indexes` 目录中：
- FAISS索引文件：`{table}_index.faiss`
- 记录数据文件：`{table}_records.pkl`

### 索引更新

当数据库数据发生变化时，需要重新构建向量索引：

```bash
python vector_index_builder.py
```

建议定期执行此操作以确保索引与数据库数据同步。

对于增量数据更新，使用增量更新功能：
```bash
# 增量更新所有索引
python -c "from vector_index_builder import VectorIndexBuilder; from db_client import DBClient; import os; from dotenv import load_dotenv; load_dotenv(); db = DBClient(os.getenv('DB_HOST'), int(os.getenv('DB_PORT', 3306)), os.getenv('DB_USER'), os.getenv('DB_PASSWORD'), os.getenv('DB_NAME')); builder = VectorIndexBuilder(db); builder.update_all_indexes_incremental()"
```

## 性能优化

1. 使用预构建的向量索引可以显著提高API响应速度
2. FAISS向量检索比传统的文本相似度计算更准确
3. 系统具有回退机制，如果未安装向量计算依赖则会使用RapidFuzz
4. 生产模式使用多Worker部署，提高并发处理能力
5. 支持向量索引的增量更新，避免重建整个索引