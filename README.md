## Simple POS Backend (FastAPI + SQLite)

### セットアップ

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 開発起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 主なAPI

- POST `/api/session:start`  担当者セッション開始 `{ clerkCode, storeCode? }`
- GET  `/api/session`        現在のアクティブセッション取得
- POST `/api/session:end`    セッション終了
- GET  `/api/products`       商品一覧 (q: 部分一致検索)
- GET  `/api/products/{jan}` JAN指定で取得

初回起動時にテーブル作成と商品マスタ10件を自動シードします。

### カートAPI（最小）

- GET  `/api/cart` 現在のカートを取得（アクティブセッション必須）
- POST `/api/cart/items` { janCode, quantity? } を追加（同一JANは数量加算）
- DELETE `/api/cart/items/{itemId}` 指定アイテムを削除

レスポンス `CartOut` には、`items`（商品名や税込価格、数量、小計）と `totalExclTax`/`totalInclTax` が含まれます。


