from telegram import Update
from telegram.ext import ContextTypes
from storage.redis_client import get_state, set_state, push_job
from bot.keyboards import cancel_keyboard

async def handle_prompt_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопок под промптом (Одобрить / Редактировать).
    """
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    action = query.data  # prompt_approve или prompt_edit
    
    state_data = get_state(chat_id)
    if state_data.get("state") != "WAITING_APPROVAL":
        await query.edit_message_text("⚠️ Эта кнопка больше не актуальна. Пожалуйста, отправьте новую ссылку.")
        return

    if action == "prompt_edit":
        # Переводим в состояние ожидания текста
        set_state(chat_id, "WAITING_PROMPT_EDIT", state_data)
        await query.edit_message_text(
            f"Текущий промпт:\n`{state_data.get('prompt', '')}`\n\n"
            "Отправьте мне *новый текст промпта* в ответном сообщении.",
            parse_mode="Markdown",
            reply_markup=cancel_keyboard()
        )
    elif action == "prompt_approve":
        # Промпт подтвержден. Двигаем пайплайн на примерку (Fashn.ai).
        await query.edit_message_text("✅ Промпт подтвержден! Запускаю процесс виртуальной примерки...")
        
        # Перекладываем job в очередь для шага GENERATING_TRYON
        job = state_data
        job["step"] = "GENERATING_TRYON"
        
        set_state(chat_id, "GENERATING_TRYON", job)
        push_job(job)

async def handle_prompt_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, state_data: dict):
    """
    Обработка текстового сообщения, когда пользователь редактирует промпт.
    """
    chat_id = update.effective_chat.id
    new_prompt = update.message.text.strip()
    
    await context.bot.send_message(
        chat_id=chat_id,
        text="✅ Новый промпт принят! Запускаю процесс виртуальной примерки..."
    )
    
    # Обновляем промпт в задаче и переходим к примерке
    job = state_data
    job["prompt"] = new_prompt
    job["step"] = "GENERATING_TRYON"
    
    set_state(chat_id, "GENERATING_TRYON", job)
    push_job(job)
