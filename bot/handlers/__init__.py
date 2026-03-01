from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from .url_handler import handle_url
from .prompt_handler import handle_prompt_approval, handle_prompt_edit_input
from .start import handle_start, handle_cancel
from config import config

# Глобальный Application для использования в webhook
# Важно: для webhook-ов мы используем application.process_update(update)
application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()

# Регистрация хэндлеров
application.add_handler(CommandHandler("start", handle_start))
application.add_handler(CallbackQueryHandler(handle_cancel, pattern="^action_cancel$"))

# Хэндлеры для промпта (кнопки)
application.add_handler(CallbackQueryHandler(handle_prompt_approval, pattern="^prompt_approve$"))
application.add_handler(CallbackQueryHandler(handle_prompt_approval, pattern="^prompt_edit$"))

# Хэндлеры для текстовых сообщений (URL или новый промпт)
# Сначала проверяем, не ждем ли мы текстовый ввод промпта, затем проверяем URL
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

async def process_update(update: Update):
    """Точка входа для вебхука FastAPI, передает Update в диспетчер Telegram."""
    if not application._initialized:
        await application.initialize()
    await application.process_update(update)
