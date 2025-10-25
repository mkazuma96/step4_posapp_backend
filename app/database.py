from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# SQLite (ローカル) 用のシンプルな接続。ファイルは backend/app/ 直下に作成される
DATABASE_URL = "sqlite:///./pos.db"

# SQLite の同一スレッド制約を回避
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI 依存関係: リクエスト毎のDBセッションを提供する"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


