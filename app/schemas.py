from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# -------- Product --------
class ProductOut(BaseModel):
    janCode: str
    name: str
    priceExclTax: int
    taxRate: int
    priceInclTax: int


# -------- Session (Step0) --------
class StartSessionIn(BaseModel):
    clerkCode: str = Field(min_length=1, max_length=5)
    storeCode: str = Field(default="30")


class SessionOut(BaseModel):
    id: str
    clerkCode: str
    storeCode: str
    isActive: bool
    startedAt: datetime
    endedAt: Optional[datetime] = None


# -------- Cart --------
class CartItemIn(BaseModel):
    janCode: str
    quantity: int = Field(ge=1, default=1)


class CartItemOut(BaseModel):
    id: str
    janCode: str
    name: str
    priceExclTax: int
    taxRate: int
    priceInclTax: int
    quantity: int
    subTotalExclTax: int
    subTotalInclTax: int


class CartOut(BaseModel):
    id: str
    items: list[CartItemOut]
    totalExclTax: int
    totalInclTax: int


class PurchaseOut(BaseModel):
    id: str
    totalExclTax: int
    totalInclTax: int
    createdAt: datetime

