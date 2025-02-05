import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from database import SessionLocal
import crud

# Подключаем переменные Railway
BOT_TOKEN = os.getenv("BOT_TOKEN", "7738966029:AAGMjMt-gg3R37p7DX3PTAoDtwOhmCrx_uM")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "1013161349"))

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Кнопки
tenant_buttons = [["История оплаты", "История встреч"], ["История счётчиков", "Правила квартиры"]]
tenant_markup = ReplyKeyboardMarkup(tenant_buttons, resize_keyboard=True)

admin_buttons = [["Список жильцов", "История оплат (все)"], ["Добавить жильца", "Удалить жильца"], ["Обновить жильца", "Уведомить жильцов"], ["Правила квартиры (ред.)"]]
admin_markup = ReplyKeyboardMarkup(admin_buttons, resize_keyboard=True)

def get_user_role(user_id: int, db) -> str:
    if user_id == ADMIN_CHAT_ID:
        return "admin"
    tenant = crud.get_tenant(db, user_id)
    return "tenant" if tenant else "none"

def start_command(update: Update, context: CallbackContext) -> None:
    db = SessionLocal()
    user_id = update.effective_user.id
    role = get_user_role(user_id, db)
    first_name = update.effective_user.first_name or "Гость"

    if role == "admin":
        update.message.reply_text(f"Здравствуйте, {first_name} (админ)!", reply_markup=admin_markup)
    elif role == "tenant":
        update.message.reply_text(f"Привет, {first_name}! Я бот для арендаторов.", reply_markup=tenant_markup)
    else:
        update.message.reply_text("У вас нет доступа. Обратитесь к администратору.")

    db.close()

def handle_tenant_text(update: Update, context: CallbackContext) -> None:
    db = SessionLocal()
    user_id = update.effective_user.id
    tenant = crud.get_tenant(db, user_id)

    if not tenant:
        update.message.reply_text("У вас нет доступа.")
        db.close()
        return

    text = update.message.text.strip()
    if text == "История оплаты":
        update.message.reply_text(f"История оплат: {tenant.get_payments()}")
    elif text == "История встреч":
        update.message.reply_text(f"История встреч: {tenant.get_meetings()}")
    elif text == "История счётчиков":
        update.message.reply_text(f"Показания счётчиков: {tenant.get_meters()}")
    elif text == "Правила квартиры":
        update.message.reply_text("1. Соблюдать тишину после 22:00.\n2. Не забывать оплачивать счета.")
    else:
        update.message.reply_text("Неизвестная команда.")
    
    db.close()

def start_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_tenant_text))

    updater.start_polling()
    updater.idle()
