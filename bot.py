

import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CommandHandler
from config import BOT_TOKEN
from parser import ITProgerParser
import html
import hashlib
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


class ITProgerBot:
    def __init__(self):
        self.parser = ITProgerParser()
        self.user_data = {}
        self.article_cache = {}

    def _get_short_hash(self, url):
        """Создает короткий хэш для URL"""
        return hashlib.md5(url.encode()).hexdigest()[:10]

    async def start(self, update: Update, context: CommandHandler.DEFAULT_TYPE):
        """Обработчик команды /start"""
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

        reply_keyboard = [
            ["📰 Последние новости"],
            ["➡️ Следующая страница", "⬅️ Предыдущая страница"],
            ["ℹ️ Помощь"]
        ]

        await update.message.reply_text(
            welcome_text,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                resize_keyboard=True,
                input_field_placeholder="Выберите действие..."
            )
        )

    async def show_news(self, update: Update, context: CommandHandler.DEFAULT_TYPE):
        """Показывает последние новости"""
        user_id = update.effective_user.id
        self.user_data[user_id] = {'current_page': 1}

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=telegram.constants.ChatAction.TYPING
        )
        await self._send_articles(update, context, page=1)

    async def next_page(self, update: Update, context: CommandHandler.DEFAULT_TYPE):
        """Следующая страница"""
        user_id = update.effective_user.id

        if user_id not in self.user_data:
            self.user_data[user_id] = {'current_page': 1}

        current_page = self.user_data[user_id]['current_page']
        next_page = current_page + 1

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=telegram.constants.ChatAction.TYPING
        )
        await self._send_articles(update, context, page=next_page)

    async def prev_page(self, update: Update, context: CommandHandler.DEFAULT_TYPE):
        """Предыдущая страница"""
        user_id = update.effective_user.id

        if user_id not in self.user_data:
            self.user_data[user_id] = {'current_page': 1}

        current_page = self.user_data[user_id]['current_page']
        prev_page = max(1, current_page - 1)

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=telegram.constants.ChatAction.TYPING
        )
        await self._send_articles(update, context, page=prev_page)

    async def _send_articles(self, update: Update, context: CommandHandler.DEFAULT_TYPE, page: int):
        """Отправляет статьи указанной страницы"""
        user_id = update.effective_user.id
        self.user_data[user_id] = {'current_page': page}

        articles = self.parser.get_articles(page)

        if not articles:
            await update.message.reply_text(
                "❌ Не удалось загрузить статьи. Попробуйте позже."
            )
            return

        cache_key = f"{user_id}_{page}"
        self.article_cache[cache_key] = articles

        # Навигационные кнопки
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_{page}"))
        nav_buttons.append(InlineKeyboardButton("➡️ Вперед", callback_data=f"next_{page}"))

        # Отправляем статьи
        for i, article in enumerate(articles, 1):
            message_text = self._format_article_message(article, i, page)
            article_hash = self._get_short_hash(article['link'])

            # Кнопки для статьи
            article_buttons = [
                [
                    InlineKeyboardButton("📖 Полный текст", callback_data=f"full_{article_hash}"),
                    InlineKeyboardButton("🔗 Открыть статью", url=article['link'])
                ]
            ]

            # Добавляем навигацию к последней статье
            if i == len(articles):
                article_buttons.append(nav_buttons)

            self.article_cache[article_hash] = article['link']
            reply_markup = InlineKeyboardMarkup(article_buttons)

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

    def _format_article_message(self, article, index, page):
        """Форматирует сообщение со статьей"""
        title = html.escape(article['title'])
        description = html.escape(article['description'])

        return f"""
📰 <b>{title}</b>

📝 {description}

📄 Страница: {page} | Статья: {index}
        """

    async def button_handler(self, update: Update, context: CommandHandler.DEFAULT_TYPE):
        """Обработчик нажатий на инлайн кнопки"""
        query = update.callback_query
        await query.answer()

        data = query.data
        user_id = query.from_user.id

        if data.startswith('full_'):
            # Кнопка "Полный текст"
            article_hash = data[5:]
            article_url = self.article_cache.get(article_hash)

            if article_url:
                full_content = self.parser.get_full_content(article_url)

                if full_content and full_content != "Полное содержимое статьи недоступно":
                    content = html.escape(full_content)
                    # Ограничиваем длину и добавляем сообщение
                    if len(content) > 1000:
                        content = content[:1000] + "...\n\n📖 <i>Читайте полную версию на сайте</i>"
                    message = f"📖 <b>Полное содержимое:</b>\n\n{content}"
                else:
                    message = "⏳ <b>Скоро!</b>\n\nПолное содержимое статьи будет доступно в ближайшее время."

                try:
                    await query.message.reply_text(message, parse_mode='HTML')
                except Exception as e:
                    logger.error(f"Ошибка отправки полного текста: {e}")
            else:
                await query.message.reply_text("❌ Статья не найдена")

        elif data.startswith('next_'):
            # Следующая страница
            current_page = int(data[5:])
            next_page = current_page + 1
            await self._handle_navigation(query, context, next_page)

        elif data.startswith('prev_'):
            # Предыдущая страница
            current_page = int(data[5:])
            prev_page = max(1, current_page - 1)
            await self._handle_navigation(query, context, prev_page)

    async def _handle_navigation(self, query, context: CommandHandler.DEFAULT_TYPE, page: int):
        """Обрабатывает навигацию по страницам"""
        user_id = query.from_user.id
        self.user_data[user_id] = {'current_page': page}

        articles = self.parser.get_articles(page)
        if not articles:
            await query.message.reply_text("❌ Не удалось загрузить статьи для этой страницы.")
            return

        # Удаляем старое сообщение
        await query.message.delete()

        # Отправляем новые статьи
        for i, article in enumerate(articles, 1):
            message_text = self._format_article_message(article, i, page)
            article_hash = self._get_short_hash(article['link'])

            # Кнопки для статьи
            nav_buttons = []
            if page > 1:
                nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_{page}"))
            nav_buttons.append(InlineKeyboardButton("➡️ Вперед", callback_data=f"next_{page}"))

            article_buttons = [
                [
                    InlineKeyboardButton("📖 Полный текст", callback_data=f"full_{article_hash}"),
                    InlineKeyboardButton("🔗 Открыть статью", url=article['link'])
                ],
                nav_buttons
            ]

            self.article_cache[article_hash] = article['link']
            reply_markup = InlineKeyboardMarkup(article_buttons)

            try:
                if article.get('image_url') and article['image_url'].startswith('http'):
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=article['image_url'],
                        caption=message_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                else:
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=message_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Ошибка отправки статьи: {e}")
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=message_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )


async def help_command(update: Update, context: CommandHandler.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
🤖 Доступные команды:
/start - Запуск бота
/news - Последние статьи
/next - Следующая страница
/prev - Предыдущая страница
/help - Справка

🎛️ Кнопки:
📰 Последние новости - показать свежие статьи
➡️/⬅️ - навигация по страницам
📖 Полный текст - прочитать статью полностью
🔗 Открыть статью - перейти на сайт
    """
    await update.message.reply_text(help_text)


async def handle_text(update: Update, context: CommandHandler.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    text = update.message.text
    bot = context.application.handlers[0].callback

    if text == "📰 Последние новости":
        await bot.show_news(update, context)
    elif text == "➡️ Следующая страница":
        await bot.next_page(update, context)
    elif text == "⬅️ Предыдущая страница":
        await bot.prev_page(update, context)
    elif text == "ℹ️ Помощь":
        await help_command(update, context)
    else:
        await update.message.reply_text(
            "Я не понимаю эту команду. Используйте кнопки или команды из меню."
        )


async def post_init(application: Application):
    """Выполняется после инициализации бота"""
    logger.info("Бот успешно запущен!")


def main():
    """Основная функция запуска бота"""
    bot = ITProgerBot()

    application = Application.builder() \
        .token(BOT_TOKEN) \
        .post_init(post_init) \
        .build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("news", bot.show_news))
    application.add_handler(CommandHandler("next", bot.next_page))
    application.add_handler(CommandHandler("prev", bot.prev_page))
    application.add_handler(CommandHandler("help", help_command))

    # Обработчики сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(bot.button_handler))

    # Запуск бота
    logger.info("Бот запускается...")
    application.run_polling()


if __name__ == '__main__':
    main()
