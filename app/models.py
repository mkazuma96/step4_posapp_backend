from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    # JANコードを主キーとして扱う
    jan_code: Mapped[str] = mapped_column(String(14), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    price_excluding_tax: Mapped[int] = mapped_column(Integer, nullable=False)
    tax_rate_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=10)


class ClerkSession(Base):
    __tablename__ = "clerk_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    clerk_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    store_code: Mapped[str] = mapped_column(String(10), nullable=False, default="30")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    clerk_session_id: Mapped[str] = mapped_column(String(36), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cart_id: Mapped[str] = mapped_column(String(36), nullable=False)
    jan_code: Mapped[str] = mapped_column(String(14), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    clerk_session_id: Mapped[str] = mapped_column(String(36), nullable=False)
    total_excl_tax: Mapped[int] = mapped_column(Integer, nullable=False)
    total_incl_tax: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_id: Mapped[str] = mapped_column(String(36), nullable=False)
    jan_code: Mapped[str] = mapped_column(String(14), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_excl_tax: Mapped[int] = mapped_column(Integer, nullable=False)
    price_incl_tax: Mapped[int] = mapped_column(Integer, nullable=False)


