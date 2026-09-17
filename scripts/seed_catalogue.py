"""Fill an empty store with a demo catalogue.

    python -m scripts.seed_catalogue --products 2000

Products are generated from per-category templates with a fixed random seed, so
two runs with the same arguments produce the same catalogue. They are inserted
in round-robin category order: the AI endpoints read the first hundred products
by id, and that hundred should span every category rather than one.
"""

import argparse
import asyncio
import random
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, insert, select

import database.database as db_module
from core.enum import ProductStatus
from models.models import Category, Product
from utils import cache

BATCH_SIZE = 500


@dataclass(frozen=True)
class Template:
    category: str
    image_tag: str
    brands: tuple[str, ...]
    lines: tuple[str, ...]  # lines[i] is made by brands[i]
    price_range: tuple[int, int]
    colors: tuple[str, ...]
    uses: tuple[str, ...]
    features: tuple[str, ...]


TEMPLATES = (
    Template(
        "Laptops", "laptop",
        ("Lenovo", "Dell", "HP", "Asus", "Acer", "Apple", "MSI"),
        ("ThinkPad", "XPS", "Pavilion", "ZenBook", "Swift", "MacBook Air", "Prestige"),
        (499, 2899),
        ("silver", "black", "gray", "white"),
        ("A light laptop for study and travel", "A workhorse for developers",
         "A quiet machine for office work", "A gaming-ready laptop"),
        ("a 14-inch IPS display", "16 GB of RAM", "a 1 TB SSD", "all-day battery life",
         "a backlit keyboard", "Thunderbolt 4 ports", "a 120 Hz screen"),
    ),
    Template(
        "Smartphones", "smartphone",
        ("Samsung", "Apple", "Google", "Xiaomi", "OnePlus", "Motorola", "Nothing"),
        ("Galaxy", "iPhone", "Pixel", "Redmi Note", "Nord", "Edge", "Phone"),
        (199, 1499),
        ("black", "blue", "white", "green", "purple"),
        ("A flagship phone for photos", "An affordable everyday phone",
         "A compact phone that fits one hand", "A phone built for long battery life"),
        ("a 50 MP main camera", "a 5000 mAh battery", "an OLED display", "5G support",
         "fast wired charging", "an IP68 rating", "two days of battery"),
    ),
    Template(
        "Headphones", "headphones",
        ("Sony", "Bose", "Sennheiser", "JBL", "Audio-Technica", "Beats", "Marshall"),
        ("WH", "QuietComfort", "Momentum", "Tune", "ATH", "Studio", "Major"),
        (39, 449),
        ("black", "white", "silver", "blue"),
        ("Over-ear headphones for long flights", "Wireless earbuds for the gym",
         "Studio headphones for mixing", "Everyday headphones for commuting"),
        ("active noise cancelling", "30 hours of playback", "a folding design",
         "Bluetooth 5.3", "a built-in microphone", "sweat resistance"),
    ),
    Template(
        "Smartwatches", "smartwatch",
        ("Apple", "Samsung", "Garmin", "Amazfit", "Fitbit", "Huawei"),
        ("Watch", "Galaxy Watch", "Forerunner", "GTR", "Versa", "Watch GT"),
        (79, 899),
        ("black", "silver", "rose gold", "green"),
        ("A running watch with GPS", "A smartwatch for notifications and payments",
         "A fitness tracker for sleep and heart rate", "A rugged watch for hiking"),
        ("built-in GPS", "a heart-rate sensor", "sleep tracking", "a week of battery",
         "water resistance to 50 m", "contactless payments"),
    ),
    Template(
        "Tablets", "tablet",
        ("Apple", "Samsung", "Lenovo", "Xiaomi", "Amazon"),
        ("iPad", "Galaxy Tab", "Tab P", "Pad", "Fire HD"),
        (129, 1299),
        ("gray", "silver", "blue", "black"),
        ("A tablet for reading and video", "A drawing tablet with a stylus",
         "A tablet for kids", "A tablet that replaces a laptop"),
        ("an 11-inch display", "stylus support", "a keyboard cover", "stereo speakers",
         "a 120 Hz screen", "LTE connectivity"),
    ),
    Template(
        "Cameras", "camera",
        ("Canon", "Nikon", "Sony", "Fujifilm", "Panasonic", "GoPro"),
        ("EOS R", "Z", "Alpha", "X-T", "Lumix", "Hero"),
        (299, 3499),
        ("black", "silver"),
        ("A mirrorless camera for travel", "An action camera for sports",
         "A camera for vlogging", "A full-frame camera for professionals"),
        ("4K video", "in-body stabilisation", "a flip-out screen", "a 24 MP sensor",
         "weather sealing", "fast autofocus"),
    ),
    Template(
        "Keyboards", "keyboard",
        ("Logitech", "Keychron", "Razer", "Corsair", "SteelSeries", "HyperX"),
        ("MX Keys", "K", "BlackWidow", "K70", "Apex", "Alloy"),
        (29, 249),
        ("black", "white", "gray"),
        ("A mechanical keyboard for typing", "A quiet keyboard for the office",
         "A gaming keyboard with RGB", "A compact keyboard for travel"),
        ("hot-swappable switches", "wireless connection", "RGB backlight",
         "a 75% layout", "multi-device pairing", "a detachable cable"),
    ),
    Template(
        "Monitors", "monitor",
        ("LG", "Dell", "Samsung", "Asus", "BenQ", "AOC"),
        ("UltraGear", "UltraSharp", "Odyssey", "ProArt", "PD", "Gaming"),
        (119, 1599),
        ("black", "white", "silver"),
        ("A 4K monitor for designers", "A fast monitor for gaming",
         "An ultrawide monitor for coding", "An office monitor that is easy on the eyes"),
        ("a 27-inch panel", "144 Hz refresh rate", "USB-C with charging",
         "factory colour calibration", "a height-adjustable stand", "HDR support"),
    ),
    Template(
        "Speakers", "speaker",
        ("JBL", "Bose", "Sonos", "Marshall", "Ultimate Ears", "Anker"),
        ("Flip", "SoundLink", "Era", "Emberton", "Boom", "Soundcore"),
        (29, 699),
        ("black", "blue", "red", "gray"),
        ("A waterproof speaker for the beach", "A smart speaker for the living room",
         "A portable speaker for parties", "A bookshelf speaker for music at home"),
        ("20 hours of playback", "waterproofing", "voice assistant support",
         "multi-room audio", "deep bass", "Wi-Fi streaming"),
    ),
    Template(
        "Gaming Consoles", "console",
        ("Sony", "Microsoft", "Nintendo", "Valve", "Asus"),
        ("PlayStation", "Xbox Series", "Switch", "Steam Deck", "ROG Ally"),
        (249, 799),
        ("white", "black"),
        ("A home console for the family", "A handheld console for travel",
         "A console for 4K gaming", "A portable PC for gaming"),
        ("a 1 TB drive", "4K output", "two controllers", "a 7-inch screen",
         "backwards compatibility", "online multiplayer"),
    ),
)


def build_products(count: int, seed: int) -> list[dict]:
    """Generate products as rows, in round-robin category order.

    `category` holds the category name; the caller swaps it for an id.
    """
    rng = random.Random(seed)
    rows = []

    for index in range(count):
        template = TEMPLATES[index % len(TEMPLATES)]
        maker = rng.randrange(len(template.brands))
        brand, line = template.brands[maker], template.lines[maker]
        model = rng.randint(2, 99)
        low, high = template.price_range
        features = rng.sample(template.features, 2)

        rows.append({
            "name": f"{brand} {line} {model}",
            "price": Decimal(rng.randint(low, high)) - Decimal("0.01"),
            "color": rng.choice(template.colors),
            "status": ProductStatus.accept,
            "image_url": f"https://loremflickr.com/600/600/{template.image_tag}?lock={index + 1}",
            "description": f"{rng.choice(template.uses)} with {features[0]} and {features[1]}.",
            "quantity": 0 if rng.random() < 0.05 else rng.randint(1, 200),
            "category": template.category,
        })

    return rows


async def ensure_categories(session) -> dict[str, int]:
    """Create the demo categories that are missing and return every id by name."""
    names = [template.category for template in TEMPLATES]
    found = await session.execute(select(Category.name).where(Category.name.in_(names)))
    existing = set(found.scalars())

    missing = [{"name": name} for name in names if name not in existing]
    if missing:
        await session.execute(insert(Category), missing)

    result = await session.execute(select(Category.name, Category.id).where(Category.name.in_(names)))
    return dict(result.all())


async def seed(count: int, seed_value: int, append: bool) -> int:
    """Insert the demo catalogue and return how many products were added."""
    async with db_module.async_session_maker() as session:
        existing = await session.scalar(select(func.count()).select_from(Product))
        if existing and not append:
            raise SystemExit(
                f"The store already has {existing} products. Pass --append to add more."
            )

        category_ids = await ensure_categories(session)
        rows = build_products(count, seed_value)
        for row in rows:
            row["category_id"] = category_ids[row.pop("category")]

        for start in range(0, len(rows), BATCH_SIZE):
            await session.execute(insert(Product), rows[start:start + BATCH_SIZE])
        await session.commit()

    # The storefront and the AI answers are cached per catalogue version.
    await cache.invalidate("product")
    await cache.invalidate("category")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill the store with a demo catalogue")
    parser.add_argument("--products", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42, help="same seed, same catalogue")
    parser.add_argument("--append", action="store_true", help="add to a non-empty store")
    args = parser.parse_args()

    async def run() -> int:
        try:
            return await seed(args.products, args.seed, args.append)
        finally:
            await db_module.async_engine.dispose()

    added = asyncio.run(run())
    print(f"Added {added} products across {len(TEMPLATES)} categories.")


if __name__ == "__main__":
    main()
