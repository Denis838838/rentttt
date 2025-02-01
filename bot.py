#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler
)

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# 1. Конфигурация
# ------------------------------------------------------------------
BOT_TOKEN = "7738966029:AAGMjMt-gg3R37p7DX3PTAoDtwOhmCrx_uM"  # Ваш токен
ADMIN_CHAT_ID = 1013161349  # Ваш chat_id (админ)

# Клавиатура для жильцов
tenant_buttons = [
    ["История оплаты", "История встреч"],
    ["История счётчиков", "Правила квартиры"]
]
tenant_markup = ReplyKeyboardMarkup(tenant_buttons, resize_keyboard=True, one_time_keyboard=False)

# Клавиатура для админа
admin_buttons = [
    ["Список жильцов", "История оплат (все)"],
    ["Добавить жильца", "Удалить жильца"],
    ["Обновить жильца", "Уведомить жильцов"],
    ["Правила квартиры (ред.)"]
]
admin_markup = ReplyKeyboardMarkup(admin_buttons, resize_keyboard=True, one_time_keyboard=False)

# ------------------------------------------------------------------
# 2. Глобальные данные (в памяти)
# ------------------------------------------------------------------
RULES = (
    "1. Соблюдать тишину после 22:00.\n"
    "2. Не забывать вовремя оплачивать счета.\n"
    "3. Содержать квартиру в чистоте.\n"
    "4. При возникновении проблем — сообщите хозяину.\n"
)

TENANTS = {}  # Изначально нет зарегистрированных жильцов

# ------------------------------------------------------------------
# 3. Определение роли пользователя
# ------------------------------------------------------------------
def get_user_role(user_id: int) -> str:
    if user_id == ADMIN_CHAT_ID:
        return "admin"
    elif user_id in TENANTS:
        return "tenant"
    else:
        return "none"

# ------------------------------------------------------------------
# 4. Обработка команды /start
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# 5. Обработка кнопок для жильца
# ------------------------------------------------------------------
def handle_tenant_text(update: Update, context: CallbackContext) -> None:
    text = update.message.text.strip()
    user_id = update.effective_user.id
    data = TENANTS.get(user_id, {})

    if text == "История оплаты":
        payments = data.get("payments", [])
        msg = "\n".join(payments) if payments else "нет платежей"
        update.message.reply_text(f"Ваша история оплат:\n{msg}")
    elif text == "История встреч":
        meetings = data.get("meetings", [])
        msg = "\n".join(meetings) if meetings else "нет встреч"
        update.message.reply_text(f"Ваша история встреч:\n{msg}")
    elif text == "История счётчиков":
        meters = data.get("meters", [])
        msg = "\n".join(meters) if meters else "нет данных"
        update.message.reply_text(f"Ваша история показаний счётчиков:\n{msg}")
    elif text == "Правила квартиры":
        update.message.reply_text(RULES)
    else:
        update.message.reply_text("Неизвестная команда. Пожалуйста, используйте кнопки.")

# ------------------------------------------------------------------
# 6. Обработка кнопок для админа
# ------------------------------------------------------------------
def handle_admin_text(update: Update, context: CallbackContext) -> None:
    text = update.message.text.strip()
    user_data = context.user_data

    if user_data.get("awaiting_broadcast", False):
        msg = text
        if TENANTS:
            for tid in TENANTS:
                context.bot.send_message(chat_id=tid, text=msg)
            update.message.reply_text("Уведомление разослано всем жильцам.", reply_markup=admin_markup)
        else:
            update.message.reply_text("Нет жильцов для уведомления.", reply_markup=admin_markup)
        user_data["awaiting_broadcast"] = False
        return
    if user_data.get("awaiting_rules", False):
        global RULES
        RULES = text
        update.message.reply_text("Правила обновлены!", reply_markup=admin_markup)
        user_data["awaiting_rules"] = False
        return
    if text == "Список жильцов":
        if TENANTS:
            lines = []
            for tid, d in TENANTS.items():
                name = d.get("name", "???")
                pay_day = d.get("payment_day", "не указано")
                contract_end = d.get("contract_end", "не указано")
                lines.append(f"ID {tid}, {name}, День оплаты: {pay_day}, Договор до: {contract_end}")
            update.message.reply_text("\n".join(lines))
        else:
            update.message.reply_text("Пока нет жильцов.")
    elif text == "История оплат (все)":
        if TENANTS:
            lines = []
            for tid, d in TENANTS.items():
                name = d.get("name", "???")
                pays = d.get("payments", [])
                pays_text = "; ".join(pays) if pays else "нет платежей"
                lines.append(f"{name} (ID {tid}): {pays_text}")
            update.message.reply_text("\n".join(lines))
        else:
            update.message.reply_text("Нет жильцов.")
    elif text == "Добавить жильца":
        add_tenant_start(update, context)
    elif text == "Удалить жильца":
        remove_tenant_start(update, context)
    elif text == "Обновить жильца":
        update_tenant_start(update, context)
    elif text == "Уведомить жильцов":
        update.message.reply_text("Введите текст уведомления:", reply_markup=ReplyKeyboardRemove())
        user_data["awaiting_broadcast"] = True
    elif text == "Правила квартиры (ред.)":
        update.message.reply_text("Введите новый текст правил:", reply_markup=ReplyKeyboardRemove())
        user_data["awaiting_rules"] = True
    else:
        update.message.reply_text("Неизвестная команда (админ).")

# ------------------------------------------------------------------
# 7. ConversationHandler для управления жильцами
# ------------------------------------------------------------------
# Состояния:
(
    ADD_TENANT_ID_OR_USERNAME,
    ADD_TENANT_NAME,
    ADD_TENANT_PAYDAY,
    ADD_TENANT_CONTRACT_END,
    REMOVE_TENANT_ID,
    UPDATE_TENANT_ID,
    UPDATE_MENU,
    UPDATE_TENANT_NAME,
    UPDATE_TENANT_PAYDAY,
    UPDATE_TENANT_MEETING,
    UPDATE_TENANT_METERS,
    UPDATE_TENANT_CONTRACT_END
) = range(12)

def tenants_fallback_cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Отмена. Возвращаюсь в админ-меню.", reply_markup=admin_markup)
    return ConversationHandler.END

def tenants_fallback_admin_buttons(update: Update, context: CallbackContext) -> int:
    tenants_fallback_cancel(update, context)
    handle_admin_text(update, context)
    return ConversationHandler.END

# ----- Добавить жильца -----
def add_tenant_start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Введите chat_id жильца (число):", reply_markup=ReplyKeyboardRemove())
    return ADD_TENANT_ID_OR_USERNAME

def add_tenant_id_or_username(update: Update, context: CallbackContext) -> int:
    text = update.message.text.strip()
    try:
        tenant_id = int(text)
    except ValueError:
        update.message.reply_text("Некорректный chat_id. Попробуйте снова.")
        return ADD_TENANT_ID_OR_USERNAME
    context.user_data["new_tenant_id"] = tenant_id
    update.message.reply_text("Введите имя жильца:")
    return ADD_TENANT_NAME

def add_tenant_get_name(update: Update, context: CallbackContext) -> int:
    context.user_data["new_tenant_name"] = update.message.text.strip()
    update.message.reply_text("Введите день оплаты (например, '15'):")
    return ADD_TENANT_PAYDAY

def add_tenant_get_payday(update: Update, context: CallbackContext) -> int:
    context.user_data["new_tenant_payday"] = update.message.text.strip()
    update.message.reply_text("Введите дату окончания договора (например, '2025-12-31'):")
    return ADD_TENANT_CONTRACT_END

def add_tenant_finish(update: Update, context: CallbackContext) -> int:
    contract_end = update.message.text.strip()
    user_data = context.user_data
    tid = user_data["new_tenant_id"]
    tname = user_data["new_tenant_name"]
    payday = user_data["new_tenant_payday"]
    TENANTS[tid] = {
        "name": tname,
        "payment_day": payday,
        "meetings": [],
        "meters": [],
        "contract_end": contract_end,
        "payments": []
    }
    update.message.reply_text(f"Жилец {tname} (ID {tid}) добавлен!", reply_markup=admin_markup)
    for key in ("new_tenant_id", "new_tenant_name", "new_tenant_payday"):
        user_data.pop(key, None)
    return ConversationHandler.END

# ----- Удалить жильца -----
def remove_tenant_start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Введите chat_id жильца для удаления:", reply_markup=ReplyKeyboardRemove())
    return REMOVE_TENANT_ID

def remove_tenant_finish(update: Update, context: CallbackContext) -> int:
    try:
        tid = int(update.message.text.strip())
    except ValueError:
        update.message.reply_text("Некорректный chat_id.", reply_markup=admin_markup)
        return ConversationHandler.END
    if tid in TENANTS:
        name = TENANTS[tid]["name"]
        del TENANTS[tid]
        update.message.reply_text(f"Жилец {name} (ID {tid}) удалён.", reply_markup=admin_markup)
    else:
        update.message.reply_text("Жилец не найден.", reply_markup=admin_markup)
    return ConversationHandler.END

# ----- Обновить жильца -----
def update_tenant_start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Введите chat_id жильца для обновления:", reply_markup=ReplyKeyboardRemove())
    return UPDATE_TENANT_ID

def update_tenant_menu(update: Update, context: CallbackContext) -> int:
    text = update.message.text.strip()
    try:
        tid = int(text)
    except ValueError:
        update.message.reply_text("Некорректный chat_id.", reply_markup=admin_markup)
        return ConversationHandler.END
    if tid not in TENANTS:
        update.message.reply_text("Такого жильца нет.", reply_markup=admin_markup)
        return ConversationHandler.END
    context.user_data["update_tenant_id"] = tid
    tname = TENANTS[tid]["name"]
    buttons = [
        ["Изменить день оплаты", "Добавить встречу"],
        ["Добавить показания счётчиков", "Изменить дату окончания договора"],
        ["Отмена"]
    ]
    markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    update.message.reply_text(f"Редактируем данные: {tname} (ID {tid}). Выберите опцию:", reply_markup=markup)
    return UPDATE_MENU

def update_tenant_choice(update: Update, context: CallbackContext) -> int:
    text = update.message.text.strip()
    tid = context.user_data["update_tenant_id"]
    if text == "Изменить день оплаты":
        current = TENANTS[tid].get("payment_day", "не задано")
        update.message.reply_text(f"Сейчас: {current}\nВведите новый день оплаты:", reply_markup=ReplyKeyboardRemove())
        return UPDATE_TENANT_PAYDAY
    elif text == "Добавить встречу":
        update.message.reply_text("Введите описание встречи (например, '01.03.2025 15:00 – осмотр'):", reply_markup=ReplyKeyboardRemove())
        return UPDATE_TENANT_MEETING
    elif text == "Добавить показания счётчиков":
        update.message.reply_text("Введите текст (например, '01.02.2025 — Вода: 100м³, Электро: 200кВт⋅ч'):", reply_markup=ReplyKeyboardRemove())
        return UPDATE_TENANT_METERS
    elif text == "Изменить дату окончания договора":
        current = TENANTS[tid].get("contract_end", "не указано")
        update.message.reply_text(f"Текущая дата: {current}\nВведите новую (YYYY-MM-DD):", reply_markup=ReplyKeyboardRemove())
        return UPDATE_TENANT_CONTRACT_END
    elif text in ("Отмена", "Назад"):
        update.message.reply_text("Отмена обновления.", reply_markup=admin_markup)
        return ConversationHandler.END
    else:
        update.message.reply_text("Некорректный выбор.", reply_markup=admin_markup)
        return UPDATE_MENU

def update_tenant_payday_finish(update: Update, context: CallbackContext) -> int:
    tid = context.user_data["update_tenant_id"]
    new_val = update.message.text.strip()
    TENANTS[tid]["payment_day"] = new_val
    update.message.reply_text("День оплаты изменён.", reply_markup=admin_markup)
    return ConversationHandler.END

def update_tenant_meeting_finish(update: Update, context: CallbackContext) -> int:
    tid = context.user_data["update_tenant_id"]
    text = update.message.text.strip()
    TENANTS[tid]["meetings"].append(text)
    update.message.reply_text("Встреча добавлена.", reply_markup=admin_markup)
    return ConversationHandler.END

def update_tenant_meters_finish(update: Update, context: CallbackContext) -> int:
    tid = context.user_data["update_tenant_id"]
    text = update.message.text.strip()
    TENANTS[tid]["meters"].append(text)
    update.message.reply_text("Показания счётчиков добавлены.", reply_markup=admin_markup)
    return ConversationHandler.END

def update_tenant_contract_end_finish(update: Update, context: CallbackContext) -> int:
    tid = context.user_data["update_tenant_id"]
    text = update.message.text.strip()
    TENANTS[tid]["contract_end"] = text
    update.message.reply_text("Дата окончания договора обновлена.", reply_markup=admin_markup)
    return ConversationHandler.END

# ------------------------------------------------------------------
# 8. Сбор ConversationHandler
# ------------------------------------------------------------------
tenant_management_conv = ConversationHandler(
    entry_points=[],  # Диалоги запускаются из handle_admin_text (через вызовы add_tenant_start, remove_tenant_start и update_tenant_start)
    states={
        # Добавить жильца
        ADD_TENANT_ID_OR_USERNAME: [MessageHandler(Filters.text & ~Filters.command, add_tenant_id_or_username)],
        ADD_TENANT_NAME: [MessageHandler(Filters.text & ~Filters.command, add_tenant_get_name)],
        ADD_TENANT_PAYDAY: [MessageHandler(Filters.text & ~Filters.command, add_tenant_get_payday)],
        ADD_TENANT_CONTRACT_END: [MessageHandler(Filters.text & ~Filters.command, add_tenant_finish)],
        # Удалить жильца
        REMOVE_TENANT_ID: [MessageHandler(Filters.text & ~Filters.command, remove_tenant_finish)],
        # Обновить жильца
        UPDATE_TENANT_ID: [MessageHandler(Filters.text & ~Filters.command, update_tenant_menu)],
        UPDATE_MENU: [MessageHandler(Filters.text & ~Filters.command, update_tenant_choice)],
        UPDATE_TENANT_PAYDAY: [MessageHandler(Filters.text & ~Filters.command, update_tenant_payday_finish)],
        UPDATE_TENANT_MEETING: [MessageHandler(Filters.text & ~Filters.command, update_tenant_meeting_finish)],
        UPDATE_TENANT_METERS: [MessageHandler(Filters.text & ~Filters.command, update_tenant_meters_finish)],
        UPDATE_TENANT_CONTRACT_END: [MessageHandler(Filters.text & ~Filters.command, update_tenant_contract_end_finish)],
    },
    fallbacks=[
        CommandHandler("cancel", tenants_fallback_cancel),
        MessageHandler(Filters.regex("^(Отмена|Назад)$"), tenants_fallback_cancel),
        MessageHandler(Filters.regex("^(Список жильцов|История оплат \все\|Добавить жильца|Удалить жильца|Обновить жильца|Уведомить жильцов|Правила квартиры \ред\\.\)$"),
                       tenants_fallback_admin_buttons),
    ],
    conversation_timeout=600  # 10 минут
)

# ------------------------------------------------------------------
# 9. Главный запуск бота
# ------------------------------------------------------------------
def main():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(tenant_management_conv)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, lambda u, c: (
        handle_admin_text(u, c) if get_user_role(u.effective_user.id) == "admin" else handle_tenant_text(u, c)
    )))

    updater.start_polling()
    print("Бот запущен. Нажмите Ctrl+C для остановки.")
    updater.idle()

if __name__ == "__main__":
    main()
