import pymysql
from pymysql.cursors import DictCursor

from .config import Config


def get_conn():
    # autocommit pour simplifier l’usage côté scripts
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=DictCursor,
        autocommit=True,
        charset="utf8mb4",
    )


def fetch_one(query: str, params: tuple | dict | None = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchone()


def fetch_all(query: str, params: tuple | dict | None = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchall()


def execute(query: str, params: tuple | dict | None = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())

