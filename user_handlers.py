from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards.reply import get_main_keyboard
from bot.keyboards.inline import get_article_keyboard
import html
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
👋 Привет, {user.first_name}!

🤖 Я бот для чтения IT статей с itproger.com/news

📚 Доступные команды:
/news - Последние статьи
/next - Следующая страница
/prev - Предыдущая страница

🎛️ Используй кнопки ниже для навигации!
    """
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard()
    )

async def show_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot = context.bot_data['bot']
    bot.user_data[user_id] = {'current_page': 1}

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action='typing'
    )
    await _send_articles(update, context, page=1)

async def next_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot = context.bot_data['bot']
    
    if user_id not in bot.user_data:
        bot.user_data[user_id] = {'current_page': 1}
    
    current_page = bot.user_data[user_id]['current_page']
    next_page = current_page + 1

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action='typing'
    )
    await _send_articles(update, context, page=next_page)

async def prev_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot = context.bot_data['bot']
    
    if user_id not in bot.user_data:
        bot.user_data[user_id] = {'current_page': 1}
    
    current_page = bot.user_data[user_id]['current_page']
    prev_page = max(1, current_page - 1)

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action='typing'
    )
    await _send_articles(update, context, page=prev_page)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 Доступные команды:
/start - Запуск бота и вывод приветственного сообщения.
/news - Отображение последних статей с первой страницы.
/next - Переход к следующей странице статей.
/prev - Переход к предыдущей странице статей.
/help - Вывод справки о командах бота.

🎛️ Используйте кнопки навигации для перемещения по страницам и просмотра полных текстов статей.
    """
    await update.message.reply_text(help_text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📰 Последние новости":
        await show_news(update, context)
    elif text == "➡️ Следующая страница":
        await next_page(update, context)
    elif text == "⬅️ Предыдущая страница":
        await prev_page(update, context)
    elif text == "ℹ️ Помощь":
        await help_command(update, context)
    else:
        await update.message.reply_text("Я не понимаю эту команду. Используйте кнопки или команды из меню.")

async def _send_articles(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    bot = context.bot_data['bot']
    user_id = update.effective_user.id
    bot.user_data[user_id] = {'current_page': page}

    articles = bot.parser.get_articles(page)

    if not articles:
        await update.message.reply_text(
            "❌ Не удалось загрузить статьи. Попробуйте позже."
        )
        return

    cache_key = f"{user_id}_{page}"
    bot.article_cache[cache_key] = articles

    for i, article in enumerate(articles, 1):
        message_text = _format_article_message(article, i, page)
        article_hash = bot._get_short_hash(article['link'])
        bot.article_cache[article_hash] = article['link']

        is_last = (i == len(articles))
        reply_markup = get_article_keyboard(article_hash, article['link'], page, is_last)

        try:
            if article.get('image_url') and article['image_url'].startswith('http'):
                await update.message.reply_photo(
                    photo=article['image_url'],
                    caption=message_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    message_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Ошибка отправки статьи: {e}")
            await update.message.reply_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

def _format_article_message(article, index, page):
    title = html.escape(article['title'])
    description = html.escape(article['description'])

    return f"""
📰 <b>{title}</b>

📝 {description}

📄 Страница: {page} | Статья: {index}
    """
