import os
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    # Telegram
    TELEGRAM_TOKEN: str

    # ProTalk API (OpenAI-compatible)
    PROTALK_API_KEY: str
    PROTALK_BOT_ID: int = 0
    PROTALK_BOT_TOKEN: str = ""
    PROTALK_MODEL_NAME: str = "gpt-4o-mini"

    # Upstash Redis
    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: str

    # remove.bg
    REMOVE_BG_API_KEY: str

    # Fashn.ai virtual try-on
    FASHN_API_KEY: str

    # Kling AI
    KLING_API_KEY: str
    KLING_API_SECRET: str
    
    # Cloudinary (Video Assembling)
    CLOUDINARY_URL: str = ""
    
    # Scraping (Amazon, Ozon bypass)
    SCRAPINGBEE_API_KEY: str = ""

    # Vercel / App
    VERCEL_URL: str = ""
    CRON_SECRET: str

    class Config:
        # Pydantic будет искать эти переменные в .env файле для локальной разработки
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Разрешаем игнорировать лишние переменные окружения
        extra = "ignore"

# При инициализации Pydantic автоматически считает переменные из os.environ.
# Если обязательных переменных (без дефолтных значений) нет, он выбросит ошибку ValidationError
config = Config()
