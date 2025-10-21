from telegram.ext import Application
from data.config import BOT_TOKEN
from bot.parser.itproger_parser import ITProgerParser
import logging

logger = logging.getLogger(__name__)

class ITProgerBot:
    def __init__(self):
        self.parser = ITProgerParser()
        self.user_data = {}
        self.article_cache = {}

    def _get_short_hash(self, url):
        return hashlib.md5(url.encode()).hexdigest()[:10]

async def post_init(application: Application):
    application.bot_data['bot'] = ITProgerBot()
    logger.info("Бот успешно запущен!")

def create_application():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    return application
