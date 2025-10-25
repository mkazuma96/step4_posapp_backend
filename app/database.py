from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os import getenv
from typing import Dict, Any
from dotenv import load_dotenv

# .env（ローカル）を読み込む。Azure では App Service の構成で設定するため不要だが、
# ここに置いておいても影響はない。
load_dotenv()


# DB接続URLを環境変数から取得（未設定ならSQLiteを使用）
# 例: mysql+pymysql://user:pass@host:3306/pos?charset=utf8mb4
DATABASE_URL = getenv("DATABASE_URL", "sqlite:///./pos.db")

# SQLite の場合のみ同一スレッド制約を回避
connect_args: Dict[str, Any] = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif DATABASE_URL.startswith("mysql+pymysql"):
    # Azure Database for MySQL は既定で SSL/TLS 必須。
    # certifi のルートCAバンドルを使って検証を有効化する。
    try:
        import certifi  # type: ignore

        connect_args = {"ssl": {"ca": certifi.where()}}
    except Exception:
        # certifi が無い場合でも動くように、空のconnect_argsでフォールバック
        connect_args = {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI 依存関係: リクエスト毎のDBセッションを提供する"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


