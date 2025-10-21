from telegram import ReplyKeyboardMarkup

def get_main_keyboard():
    """Возвращает основную reply клавиатуру"""
    keyboard = [
        ["📰 Последние новости"],
        ["➡️ Следующая страница", "⬅️ Предыдущая страница"],
        ["ℹ️ Помощь"]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )
