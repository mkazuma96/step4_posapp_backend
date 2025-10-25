#!/bin/bash

# バーチャル環境の有効化
if [ -d "antenv" ]; then
    source antenv/bin/activate
fi

# データベースの初期化（必要に応じて）
# python -m app.seed

# GunicornでUvicorn workerを使ってFastAPIアプリケーションを起動
gunicorn --bind=0.0.0.0:8000 --workers=4 --worker-class=uvicorn.workers.UvicornWorker --timeout=600 --access-logfile '-' --error-logfile '-' app.main:app

