import re
import httpx
from bs4 import BeautifulSoup
from typing import Optional
from config import config

SUPPORTED_DOMAINS = [
    "wildberries.ru",
    "amazon.com",
    "amazon.co.uk",
    "amazon.de",
    "ozon.ru",
    "ozon.by",
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
    elif "ozon" in url:
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
    """
    Парсит Amazon через ScrapingBee (обход капчи).
    Ищет title (id="productTitle"), price (class="a-price-whole"), image (id="landingImage").
    """
    if not config.SCRAPINGBEE_API_KEY:
        raise ValueError("Для работы Amazon требуется SCRAPINGBEE_API_KEY")

    api_url = "https://app.scrapingbee.com/api/v1/"
    params = {
        "api_key": config.SCRAPINGBEE_API_KEY,
        "url": url,
        "render_js": "false",
        "extract_rules": '{"title": "#productTitle", "price": ".a-price-whole", "image": {"selector": "#landingImage", "output": "@src"}}'
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(api_url, params=params)
        resp.raise_for_status()
        data = resp.json()

    if not data.get("image"):
        # Попробуем альтернативный селектор для фото
        params["extract_rules"] = '{"title": "#productTitle", "price": ".a-price-whole", "image": {"selector": "#imgTagWrapperId img", "output": "@src"}}'
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(api_url, params=params)
            data = resp.json()

    if not data.get("image"):
        raise ValueError("Не удалось извлечь фотографию товара с Amazon")

    title = data.get("title", "Amazon Product").strip()
    price = data.get("price", "").strip()

    return {
        "image_url": data["image"],
        "product_name": title,
        "product_price": f"${price}" if price else "",
        "article": url,
    }


async def _scrape_ozon(url: str) -> dict:
    """
    Парсит Ozon через ScrapingBee, так как Ozon блокирует обычные запросы (Cloudflare/Captcha).
    Использует BeautifulSoup для более сложного разбора DOM.
    """
    if not config.SCRAPINGBEE_API_KEY:
        raise ValueError("Для работы Ozon требуется SCRAPINGBEE_API_KEY")

    api_url = "https://app.scrapingbee.com/api/v1/"
    params = {
        "api_key": config.SCRAPINGBEE_API_KEY,
        "url": url,
        "render_js": "true",  # Для Ozon часто нужен JS
        "wait_browser": "networkidle2"
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(api_url, params=params)
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Ищем название (обычно в h1)
    title_tag = soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Ozon Product"

    # 2. Ищем картинку (ищем img теги внутри контейнеров с фото)
    image_url = ""
    # Ищем картинки с высоким разрешением, у которых есть data-src или src и alt совпадает с title (или близко)
    img_tags = soup.find_all("img")
    for img in img_tags:
        src = img.get("src", "")
        # Ozon хранит фото товаров в CDN cdn1.ozonapi.com/s3/
        if "cdn" in src and "ozonapi" in src and "wc1000" in src:
            image_url = src
            break
            
    if not image_url:
        for img in img_tags:
            src = img.get("src", "")
            if "cdn" in src and "ozonapi" in src:
                image_url = src
                break

    if not image_url:
        raise ValueError("Не удалось извлечь фотографию товара с Ozon")

    # 3. Ищем цену
    price = ""
    price_tag = soup.find("span", text=re.compile(r'₽|руб'))
    if price_tag:
        price = price_tag.text.strip()

    return {
        "image_url": image_url,
        "product_name": title,
        "product_price": price,
        "article": url,
    }
