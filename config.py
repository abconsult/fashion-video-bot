import os


class Config:
    # Telegram
    TELEGRAM_TOKEN: str = os.environ.get("TELEGRAM_TOKEN", "")

    # ProTalk API (OpenAI-compatible)
    PROTALK_API_KEY: str = os.environ.get("PROTALK_API_KEY", "")
    PROTALK_BOT_ID: int = int(os.environ.get("PROTALK_BOT_ID", "0"))
    PROTALK_BOT_TOKEN: str = os.environ.get("PROTALK_BOT_TOKEN", "")
    PROTALK_MODEL_NAME: str = os.environ.get("PROTALK_MODEL_NAME", "gpt-4o-mini")

    # Upstash Redis
    UPSTASH_REDIS_REST_URL: str = os.environ.get("UPSTASH_REDIS_REST_URL", "")
    UPSTASH_REDIS_REST_TOKEN: str = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")

    # remove.bg
    REMOVE_BG_API_KEY: str = os.environ.get("REMOVE_BG_API_KEY", "")

    # Fashn.ai virtual try-on
    FASHN_API_KEY: str = os.environ.get("FASHN_API_KEY", "")

    # Kling AI
    KLING_API_KEY: str = os.environ.get("KLING_API_KEY", "")
    KLING_API_SECRET: str = os.environ.get("KLING_API_SECRET", "")

    # Vercel / App
    VERCEL_URL: str = os.environ.get("VERCEL_URL", "")
    CRON_SECRET: str = os.environ.get("CRON_SECRET", "")


config = Config()
