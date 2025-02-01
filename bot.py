import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Инициализация бота
updater = Updater(token=BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Команда /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Привет! Я бот для арендаторов. Используйте /help для списка команд.")

# Обработчик неизвестных сообщений
def unknown(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Извините, я не понимаю эту команду.")

# Добавляем обработчики команд
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.command, unknown))

# Запуск бота
def main():
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
