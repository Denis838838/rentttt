#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import threading
import logging
from fastapi import FastAPI
import uvicorn
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler
)

# --------------------- Логирование и конфигурация Telegram-бота ---------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация бота
BOT_TOKEN = "7738966029:AAGMjMt-gg3R37p7DX3PTAoDtwOhmCrx_uM"  # Твой токен
ADMIN_CHAT_ID = 1013161349  # Твой chat_id (админ)

# Прочие переменные и клавиатуры (код, который ты уже написал)
tenant_buttons = [
    ["История оплаты", "История встреч"],
    ["История счётчиков", "Правила квартиры"]
]
tenant_markup = ReplyKeyboardMarkup(tenant_buttons, resize_keyboard=True, one_time_keyboard=False)

admin_buttons = [
    ["Список жильцов", "История оплат (все)"],
    ["Добавить жильца", "Удалить жильца"],
    ["Обновить жильца", "Уведомить жильцов"],
    ["Правила квартиры (ред.)"]
]
admin_markup = ReplyKeyboardMarkup(admin_buttons, resize_keyboard=True, one_time_keyboard=False)

RULES = (
    "1. Соблюдать тишину после 22:00.\n"
    "2. Не забывать вовремя оплачивать счета.\n"
    "3. Содержать квартиру в чистоте.\n"
    "4. При возникновении проблем — сообщите хозяину.\n"
)

TENANTS = {}  # Зарегистрированные жильцы

def get_user_role(user_id: int) -> str:
    if user_id == ADMIN_CHAT_ID:
        return "admin"
    elif user_id in TENANTS:
        return "tenant"
    else:
        return "none"

def start_command(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    role = get_user_role(user_id)
    first_name = update.effective_user.first_name or "Гость"

    if role == "admin":
        text = f"Здравствуйте, {first_name} (админ)!\nВыберите действие:"
        update.message.reply_text(text, reply_markup=admin_markup)
    elif role == "tenant":
        text = f"Привет, {first_name}!\nЯ бот для арендаторов.\nВот ваше меню:"
        update.message.reply_text(text, reply_markup=tenant_markup)
    else:
        update.message.reply_text("У вас нет доступа к этому боту. Обратитесь к администратору.")

# Здесь располагается остальной код для обработки сообщений и ConversationHandler  
# (то, что ты уже реализовал: handle_tenant_text, handle_admin_text, функции для управления жильцами и т.д.)
# Например, добавим простой MessageHandler, как в твоем коде:
def default_message_handler(update: Update, context: CallbackContext) -> None:
    if get_user_role(update.effective_user.id) == "admin":
        handle_admin_text(update, context)
    else:
        handle_tenant_text(update, context)

# Здесь должен быть код ConversationHandler (tenant_management_conv) и его состояния, как в твоем примере.
# Для краткости он опущен, но его нужно оставить без изменений.

# --------------------- Функция запуска Telegram-бота ---------------------
def run_telegram_bot():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start_command))
    # Добавляем обработчик для управления жильцами (ConversationHandler)
    dp.add_handler(tenant_management_conv)
    # Обработчик для текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, default_message_handler))

    updater.start_polling()
    logger.info("Бот запущен. Ожидание обновлений...")
    updater.idle()

# --------------------- Функция запуска веб-сервера для Railway ---------------------
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Приложение работает (бот запущен)"}

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

# --------------------- Главная функция ---------------------
def main():
    # Запускаем веб-сервер в отдельном потоке, чтобы Railway считал контейнер активным
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # Запускаем Telegram-бота (long polling)
    run_telegram_bot()

if __name__ == "__main__":
    main()
