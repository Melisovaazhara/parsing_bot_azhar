import logging
from loader import create_application

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    """Основная функция запуска бота"""
    application = create_application()
    
    logger.info("Запуск бота...")
    application.run_polling()

if __name__ == '__main__':
    main()
