from __future__ import annotations

from sqlalchemy.orm import Session

from .models import Product


PRODUCTS = [
    ("4901001000012", "シャープペンシル 0.5mm", 150),
    ("4901001000029", "ボールペン 黒 1.0mm", 120),
    ("4901001000036", "消しゴム スタンダード", 100),
    ("4901001000043", "ノート A5 横罫 50枚", 180),
    ("4901001000050", "修正テープ 5mm×6m", 250),
    ("4901001000067", "油性マーカー 黒", 200),
    ("4901001000074", "クリアファイル タイプA", 80),
    ("4901001000081", "クリアファイル タイプB", 100),
    ("4901001000098", "クリアファイル タイプC", 120),
    ("4901001000104", "筆箱", 600),
]


def seed_products(db: Session, tax_rate_percent: int = 10) -> None:
    """商品マスタをアップサートで反映する。既存は上書き更新。"""
    for jan, name, price in PRODUCTS:
        existing = db.get(Product, jan)
        if existing:
            existing.name = name
            existing.price_excluding_tax = price
            existing.tax_rate_percent = tax_rate_percent
        else:
            db.add(
                Product(
                    jan_code=jan,
                    name=name,
                    price_excluding_tax=price,
                    tax_rate_percent=tax_rate_percent,
                )
            )
    db.commit()


