from telegram import Update
from telegram.ext import ContextTypes
from storage.redis_client import clear_state

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start."""
    chat_id = update.effective_chat.id
    clear_state(chat_id)
    
    welcome_text = (
        "👗 Привет! Я AI-бот для создания фэшн-рилсов.\n\n"
        "Отправьте мне ссылку на одежду с маркетплейса (Wildberries), "
        "и я автоматически сгенерирую видео с виртуальной моделью.\n\n"
        "🔗 *Жду ссылку на товар...*"
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text=welcome_text,
        parse_mode="Markdown"
    )

async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки отмены."""
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    clear_state(chat_id)
    
    await query.edit_message_text(
        "❌ Действие отменено.\n\n"
        "Пришлите новую ссылку, если захотите создать другое видео."
    )
