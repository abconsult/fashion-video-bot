from telegram import Update
from telegram.ext import ContextTypes
from services.scraper import is_supported_url
from storage.redis_client import get_state, set_state, push_job
from .prompt_handler import handle_prompt_edit_input

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик всех текстовых сообщений.
    Если состояние пользователя WAITING_PROMPT_EDIT, текст считается новым промптом.
    Иначе — проверяем, является ли текст поддерживаемой ссылкой.
    """
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    
    # 1. Проверяем, не ожидаем ли мы ввода нового промпта
    state_data = get_state(chat_id)
    if state_data.get("state") == "WAITING_PROMPT_EDIT":
        return await handle_prompt_edit_input(update, context, state_data)

    # 2. Если мы здесь, значит ожидаем ссылку на товар
    if not is_supported_url(text):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Извините, я поддерживаю только ссылки с Wildberries (пока).\n"
                 "Пожалуйста, отправьте корректную ссылку на товар."
        )
        return

    # 3. Ссылка корректна. Формируем job и отправляем в пайплайн.
    await context.bot.send_message(
        chat_id=chat_id,
        text="⏳ Ссылка принята! Начинаю сбор данных и удаление фона..."
    )
    
    # Формируем job. Структуру ожидают функции pipeline.py
    job = {
        "chat_id": chat_id,
        "step": "SCRAPING_PHOTO",
        "product_url": text
    }
    
    # Записываем состояние и пушим в очередь (cron подхватит)
    set_state(chat_id, "SCRAPING_PHOTO", job)
    push_job(job)
