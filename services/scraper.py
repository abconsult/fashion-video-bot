import re
import httpx
from typing import Optional

SUPPORTED_DOMAINS = [
    "wildberries.ru",
    "amazon.com",
    "amazon.co.uk",
    "amazon.de",
    "ozon.ru",
]


def is_supported_url(url: str) -> bool:
    return any(domain in url for domain in SUPPORTED_DOMAINS)


async def fetch_product_data(url: str) -> dict:
    """
    Парсит страницу товара и возвращает фото, название, цену.
    Returns dict: {image_url, product_name, product_price}
    """
    if "wildberries.ru" in url:
        return await _scrape_wildberries(url)
    elif "amazon" in url:
        return await _scrape_amazon(url)
    elif "ozon.ru" in url:
        return await _scrape_ozon(url)
    raise ValueError(f"Unsupported marketplace: {url}")


async def _scrape_wildberries(url: str) -> dict:
    """Парсит карточку товара Wildberries через публичное API."""
    match = re.search(r"/catalog/(\d+)/", url)
    if not match:
        raise ValueError("Не удалось извлечь артикул из URL Wildberries")

    article = match.group(1)
    api_url = (
        f"https://card.wb.ru/cards/v1/detail?"
        f"appType=1&curr=rub&dest=-1257786&nm={article}"
    )

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(api_url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        data = resp.json()

    products = data.get("data", {}).get("products", [])
    if not products:
        raise ValueError("Товар не найден на Wildberries")

    product = products[0]
    name = product.get("name", "Товар")
    brand = product.get("brand", "")
    price = product.get("salePriceU", 0) // 100

    vol = int(article) // 100000
    part = int(article) // 1000
    basket = _wb_basket(vol)
    image_url = (
        f"https://basket-{basket:02d}.wbbasket.ru/"
        f"vol{vol}/part{part}/{article}/images/big/1.webp"
    )

    return {
        "image_url": image_url,
        "product_name": f"{brand} {name}".strip(),
        "product_price": f"{price} ₽",
        "article": article,
    }


def _wb_basket(vol: int) -> int:
    """Wildberries CDN basket number by vol."""
    thresholds = [
        (143, 1), (287, 2), (431, 3), (719, 4), (1007, 5),
        (1061, 6), (1115, 7), (1169, 8), (1313, 9), (1601, 10),
        (1655, 11), (1919, 12), (2045, 13), (2189, 14), (2405, 15),
        (2621, 16), (2837, 17),
    ]
    for threshold, basket in thresholds:
        if vol <= threshold:
            return basket
    return 18


async def _scrape_amazon(url: str) -> dict:
    raise NotImplementedError(
        "Amazon scraping requires ScrapingBee API. "
        "Set SCRAPINGBEE_API_KEY env variable."
    )


async def _scrape_ozon(url: str) -> dict:
    raise NotImplementedError("Ozon scraping is not yet implemented.")
