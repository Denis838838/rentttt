from bot import start_bot
from database import init_db

if __name__ == "__main__":
    print("🚀 Запуск приложения...")
    init_db()  # Создание таблиц в БД
    start_bot()  # Запуск Telegram-бота
