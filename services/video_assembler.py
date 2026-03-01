import httpx
import cloudinary
import cloudinary.uploader
import urllib.parse
from typing import Optional
from config import config

# Инициализируем Cloudinary
if config.CLOUDINARY_URL:
    cloudinary.config(url=config.CLOUDINARY_URL)


async def assemble_final_video(
    video_url: str,
    product_name: str,
    product_price: str,
    caption: Optional[str] = None,
) -> bytes:
    """
    Накладывает текст (название и цена) на видео, используя Cloudinary Transformations.
    Возвращает байты готового видео для отправки в Telegram.
    
    Если Cloudinary не настроен, возвращает исходное видео.
    """
    if not config.CLOUDINARY_URL:
        print("[Video Assembler] CLOUDINARY_URL is missing, falling back to original video.")
        return await _download_file(video_url)

    try:
        # 1. Загружаем сырое видео в Cloudinary (или берем по URL напрямую, если поддерживается)
        # Так как видео уже где-то хостится (Kling), используем upload с параметром resource_type="video"
        upload_result = cloudinary.uploader.upload(
            video_url,
            resource_type="video",
            folder="fashion_bot_videos"
        )
        public_id = upload_result["public_id"]

        # 2. Формируем трансформации для текста
        # Документация Cloudinary: https://cloudinary.com/documentation/video_manipulation_and_delivery#adding_text_captions
        title_text = (product_name or "Новая коллекция")[:40]
        encoded_title = urllib.parse.quote(title_text)
        
        transformations = [
            {"width": 1080, "height": 1920, "crop": "fill"}
        ]
        
        # Слой для названия товара
        transformations.append({
            "overlay": {
                "font_family": "Arial",
                "font_size": 48,
                "font_weight": "bold",
                "text": encoded_title
            },
            "color": "white",
            "gravity": "south",
            "y": 200,
            "effect": "shadow"
        })

        # Слой для цены
        if product_price:
            encoded_price = urllib.parse.quote(f"Цена: {product_price}")
            transformations.append({
                "overlay": {
                    "font_family": "Arial",
                    "font_size": 36,
                    "font_weight": "bold",
                    "text": encoded_price
                },
                "color": "yellow",
                "gravity": "south",
                "y": 140,
                "effect": "shadow"
            })

        # 3. Генерируем URL с наложенным текстом
        final_video_url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            resource_type="video",
            transformation=transformations,
            format="mp4"
        )
        
        print(f"[Video Assembler] Generated Cloudinary URL: {final_video_url}")

        # 4. Скачиваем готовое видео для отправки в Telegram
        return await _download_file(final_video_url)

    except Exception as e:
        print(f"[Video Assembler] Cloudinary processing failed: {e}")
        # В случае любой ошибки отдаем оригинальное видео, чтобы пайплайн не падал
        return await _download_file(video_url)


async def _download_file(url: str) -> bytes:
    """Вспомогательная функция для скачивания файла в память."""
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content
