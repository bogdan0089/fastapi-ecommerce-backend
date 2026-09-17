import pytest
from sqlalchemy import func, select

import database.database as db_module
from core.enum import ProductStatus
from models.models import Product
from scripts.seed_catalogue import TEMPLATES, build_products, seed


def test_every_brand_has_its_own_line():
    for template in TEMPLATES:
        assert len(template.brands) == len(template.lines), template.category


def test_same_seed_builds_the_same_catalogue():
    assert build_products(50, seed=7) == build_products(50, seed=7)


def test_first_products_cover_every_category():
    rows = build_products(len(TEMPLATES), seed=1)

    assert {row["category"] for row in rows} == {template.category for template in TEMPLATES}


def test_product_names_pair_a_brand_with_its_line():
    pairs = {
        (template.category, brand, line)
        for template in TEMPLATES
        for brand, line in zip(template.brands, template.lines, strict=True)
    }

    for row in build_products(200, seed=3):
        assert any(
            row["category"] == category and row["name"].startswith(f"{brand} {line} ")
            for category, brand, line in pairs
        ), row["name"]


async def _product_count() -> int:
    async with db_module.async_session_maker() as session:
        return await session.scalar(select(func.count()).select_from(Product))


async def test_seed_adds_accepted_products():
    before = await _product_count()

    added = await seed(30, seed_value=11, append=True)

    assert added == 30
    assert await _product_count() == before + 30
    async with db_module.async_session_maker() as session:
        statuses = await session.scalars(
            select(Product.status).order_by(Product.id.desc()).limit(30)
        )
        assert set(statuses) == {ProductStatus.accept}


async def test_seed_refuses_a_store_that_already_has_products():
    await seed(1, seed_value=12, append=True)

    with pytest.raises(SystemExit):
        await seed(5, seed_value=13, append=False)
