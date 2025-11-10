import pymysql
from typing import List, Dict, Any

TABLE_PK_MAP = {
    "demandProposal": "idDemandProposal",
    "demandPlan": "idDemandPlan",
    "demandCollection": "idDemandCollection",
}

class DBClient:
    def __init__(self, host: str, port: int, user: str, password: str, db: str):
        self.conn = pymysql.connect(
            host=host, port=port, user=user, password=password, db=db,
            read_timeout=600,  # <-- 增加这个
            write_timeout=600,  # <-- 增加这个
            autocommit=True  # 开启自动提交，避免长事务旧快照
        )


    def get_text_columns(self, table: str) -> List[str]:
        """获取某表的 text 类型列"""
        sql = """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        AND DATA_TYPE IN ('text')
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (self.conn.db.decode(), table))
            return [row[0] for row in cur.fetchall()]

    def get_record_by_id(self, table: str, record_id: int) -> Dict[str, Any]:
        """根据主键获取一条记录（只取 text 字段）"""
        pk = TABLE_PK_MAP[table]
        text_cols = self.get_text_columns(table)
        cols = ",".join(text_cols)
        sql = f"SELECT {pk}, {cols} FROM {table} WHERE {pk} = %s"
        self.conn.ping(reconnect=True)  # 保证连接有效
        with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(sql, (record_id,))
            print("SQL:", sql)
            return cur.fetchone()

    def get_all_records(self, table: str) -> List[Dict[str, Any]]:
        """获取所有记录（只取 text 字段）"""
        pk = TABLE_PK_MAP[table]
        text_cols = self.get_text_columns(table)
        cols = ",".join(text_cols)
        sql = f"SELECT {pk}, {cols} FROM {table}"
        with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(sql)
            return cur.fetchall()
