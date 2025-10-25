from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import engine, get_db
from .models import Base, ClerkSession, Product, Cart, CartItem, Purchase, PurchaseItem
from .schemas import ProductOut, SessionOut, StartSessionIn, CartItemIn, CartOut, CartItemOut, PurchaseOut
from .seed import seed_products


app = FastAPI(title="Simple POS Backend", version="0.1.0")

# CORS (ローカル開発用 & Azure)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://app-002-gen10-step3-1-py-oshima57.azurewebsites.net",
        "https://app-002-gen10-step3-1-node-oshima57.azurewebsites.net",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # テーブル作成と初回シード
    Base.metadata.create_all(bind=engine)
    with next(get_db()) as db:
        seed_products(db)


# ---------- Step0: 担当者/店番 セッションAPI ----------
@app.post("/api/session:start", response_model=SessionOut)
def start_session(payload: StartSessionIn, db: Session = Depends(get_db)):
    # 担当者コード 1-5 のみ許可
    if payload.clerkCode not in {"1", "2", "3", "4", "5"}:
        raise HTTPException(status_code=400, detail="clerkCode must be 1-5")
    # 既存アクティブを全て終了（簡易運用: 1デバイス1セッション想定）
    active = (
        db.query(ClerkSession)
        .filter(ClerkSession.is_active.is_(True))
        .all()
    )
    for s in active:
        s.is_active = False
        s.ended_at = datetime.utcnow()
    # 新規開始
    session = ClerkSession(clerk_code=payload.clerkCode, store_code=payload.storeCode)
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionOut(
        id=session.id,
        clerkCode=session.clerk_code,
        storeCode=session.store_code,
        isActive=session.is_active,
        startedAt=session.started_at,
        endedAt=session.ended_at,
    )


@app.get("/api/session", response_model=SessionOut)
def get_active_session(db: Session = Depends(get_db)):
    session = (
        db.query(ClerkSession)
        .filter(ClerkSession.is_active.is_(True))
        .order_by(ClerkSession.started_at.desc())
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")
    return SessionOut(
        id=session.id,
        clerkCode=session.clerk_code,
        storeCode=session.store_code,
        isActive=session.is_active,
        startedAt=session.started_at,
        endedAt=session.ended_at,
    )


@app.post("/api/session:end", response_model=SessionOut)
def end_session(db: Session = Depends(get_db)):
    session = (
        db.query(ClerkSession)
        .filter(ClerkSession.is_active.is_(True))
        .order_by(ClerkSession.started_at.desc())
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")
    session.is_active = False
    session.ended_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return SessionOut(
        id=session.id,
        clerkCode=session.clerk_code,
        storeCode=session.store_code,
        isActive=session.is_active,
        startedAt=session.started_at,
        endedAt=session.ended_at,
    )


# ---------- 商品API（一覧/検索/JAN指定） ----------
def to_product_out(p: Product) -> ProductOut:
    price_incl = int(round(p.price_excluding_tax * (1 + p.tax_rate_percent / 100)))
    return ProductOut(
        janCode=p.jan_code,
        name=p.name,
        priceExclTax=p.price_excluding_tax,
        taxRate=p.tax_rate_percent,
        priceInclTax=price_incl,
    )


@app.get("/api/products", response_model=List[ProductOut])
def list_products(q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Product)
    if q:
        like = f"%{q}%"
        query = query.filter(Product.name.like(like))
    products = query.order_by(Product.name.asc()).limit(50).all()
    return [to_product_out(p) for p in products]


@app.get("/api/products/{jan_code}", response_model=ProductOut)
def get_product(jan_code: str, db: Session = Depends(get_db)):
    product = db.get(Product, jan_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return to_product_out(product)


# ---------- カートAPI ----------
def calc_price_incl(price_excl: int, tax_rate: int) -> int:
    return int(round(price_excl * (1 + tax_rate / 100)))


def ensure_active_session(db: Session) -> ClerkSession:
    session = (
        db.query(ClerkSession)
        .filter(ClerkSession.is_active.is_(True))
        .order_by(ClerkSession.started_at.desc())
        .first()
    )
    if not session:
        raise HTTPException(status_code=400, detail="Please start session first")
    return session


def ensure_active_cart(db: Session, clerk_session_id: str) -> Cart:
    cart = (
        db.query(Cart)
        .filter(Cart.clerk_session_id == clerk_session_id, Cart.is_active.is_(True))
        .order_by(Cart.created_at.desc())
        .first()
    )
    if not cart:
        cart = Cart(clerk_session_id=clerk_session_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def build_cart_out(db: Session, cart: Cart) -> CartOut:
    items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
    item_outs: list[CartItemOut] = []
    total_excl = 0
    total_incl = 0
    for it in items:
        prod = db.get(Product, it.jan_code)
        if not prod:
            # 不整合はスキップ
            continue
        price_incl = calc_price_incl(prod.price_excluding_tax, prod.tax_rate_percent)
        sub_excl = prod.price_excluding_tax * it.quantity
        sub_incl = price_incl * it.quantity
        total_excl += sub_excl
        total_incl += sub_incl
        item_outs.append(
            CartItemOut(
                id=it.id,
                janCode=it.jan_code,
                name=prod.name,
                priceExclTax=prod.price_excluding_tax,
                taxRate=prod.tax_rate_percent,
                priceInclTax=price_incl,
                quantity=it.quantity,
                subTotalExclTax=sub_excl,
                subTotalInclTax=sub_incl,
            )
        )
    return CartOut(id=cart.id, items=item_outs, totalExclTax=total_excl, totalInclTax=total_incl)


@app.get("/api/cart", response_model=CartOut)
def get_cart(db: Session = Depends(get_db)):
    session = ensure_active_session(db)
    cart = ensure_active_cart(db, session.id)
    return build_cart_out(db, cart)


@app.post("/api/cart/items", response_model=CartOut)
def add_item(payload: CartItemIn, db: Session = Depends(get_db)):
    session = ensure_active_session(db)
    cart = ensure_active_cart(db, session.id)
    # 同一JANは数量加算
    existing = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.jan_code == payload.janCode)
        .first()
    )
    if existing:
        existing.quantity += payload.quantity
    else:
        # 商品存在チェック
        prod = db.get(Product, payload.janCode)
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")
        db.add(CartItem(cart_id=cart.id, jan_code=payload.janCode, quantity=payload.quantity))
    db.commit()
    return build_cart_out(db, cart)


@app.delete("/api/cart/items/{item_id}", response_model=CartOut)
def remove_item(item_id: str, db: Session = Depends(get_db)):
    session = ensure_active_session(db)
    cart = ensure_active_cart(db, session.id)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()
    return build_cart_out(db, cart)


# すべてのカートアイテムを削除（カート空にする）
@app.post("/api/cart:clear", response_model=CartOut)
def clear_cart(db: Session = Depends(get_db)):
    session = ensure_active_session(db)
    cart = ensure_active_cart(db, session.id)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    return build_cart_out(db, cart)

# ---------- 購入API ----------
@app.post("/api/purchase", response_model=PurchaseOut)
def create_purchase(db: Session = Depends(get_db)):
    session = ensure_active_session(db)
    cart = ensure_active_cart(db, session.id)
    cart_view = build_cart_out(db, cart)
    if len(cart_view.items) == 0:
        raise HTTPException(status_code=400, detail="Cart is empty")

    purchase = Purchase(
        clerk_session_id=session.id,
        total_excl_tax=cart_view.totalExclTax,
        total_incl_tax=cart_view.totalInclTax,
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    # 明細保存
    for it in cart_view.items:
        db.add(
            PurchaseItem(
                purchase_id=purchase.id,
                jan_code=it.janCode,
                quantity=it.quantity,
                price_excl_tax=it.priceExclTax,
                price_incl_tax=it.priceInclTax,
            )
        )

    # カートを締める
    cart.is_active = False
    db.commit()

    return PurchaseOut(
        id=purchase.id,
        totalExclTax=purchase.total_excl_tax,
        totalInclTax=purchase.total_incl_tax,
        createdAt=purchase.created_at,
    )


