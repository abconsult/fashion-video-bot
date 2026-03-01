from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def approval_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения промпта перед генерацией."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить и продолжить", callback_data="prompt_approve"),
        ],
        [
            InlineKeyboardButton("✏️ Редактировать промпт", callback_data="prompt_edit")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для отмены текущего действия."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отмена", callback_data="action_cancel")]
    ])
