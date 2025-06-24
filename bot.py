
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import sqlite3

logging.basicConfig(level=logging.INFO)
TOKEN = "7974469546:AAE1GfJKvHlMxTz1_PTwkKsZcLsQZBsywh8"

ASK_NAME, ASK_TAIL = range(2)
WAIT_DOMAIN = range(1)
DELETE_SELECT = range(1)

main_keyboard = ReplyKeyboardMarkup([
    ['/addland', '/getlink'],
    ['/deleteland']
], resize_keyboard=True)

conn = sqlite3.connect("lands.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS lands (name TEXT, tail TEXT)")
conn.commit()

temp_data = {}

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Выберите действие:", reply_markup=main_keyboard)

def addland_start(update: Update, context: CallbackContext):
    update.message.reply_text("Как называется ленд?")
    return ASK_NAME

def addland_name(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    temp_data[user_id] = {"name": update.message.text}
    update.message.reply_text("Отправь мне хвост лендинга.")
    return ASK_TAIL

def addland_tail(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    tail = update.message.text
    name = temp_data[user_id]["name"]
    cursor.execute("INSERT INTO lands (name, tail) VALUES (?, ?)", (name, tail))
    conn.commit()
    update.message.reply_text(f"`{name}` успешно сохранён ✅", parse_mode="Markdown", reply_markup=main_keyboard)
    return ConversationHandler.END

def getlink_start(update: Update, context: CallbackContext):
    update.message.reply_text("Отправьте домен (например: 1wpnwn.top)")
    return WAIT_DOMAIN

def getlink_domain(update: Update, context: CallbackContext):
    domain = update.message.text.strip().rstrip("/")
    if not domain.startswith("http"):
        domain = "https://" + domain

    cursor.execute("SELECT name, tail FROM lands")
    lands = cursor.fetchall()

    if not lands:
        update.message.reply_text("База пуста. Добавьте ленды через /addland.", reply_markup=main_keyboard)
        return ConversationHandler.END

    messages = [f"`{name}`\n`{domain}{tail}`" for name, tail in lands]
    update.message.reply_text("\n\n".join(messages), parse_mode="MarkdownV2", reply_markup=main_keyboard)
    return ConversationHandler.END

def deleteland_start(update: Update, context: CallbackContext):
    cursor.execute("SELECT rowid, name FROM lands")
    rows = cursor.fetchall()

    if not rows:
        update.message.reply_text("База пуста, нечего удалять.", reply_markup=main_keyboard)
        return ConversationHandler.END

    msg = "Выберите номер ленда для удаления:\n"
    for i, (rowid, name) in enumerate(rows, start=1):
        msg += f"{i}. {name}\n"

    context.user_data["deletelist"] = rows
    update.message.reply_text(msg)
    return DELETE_SELECT

# ... (предыдущий код остаётся без изменений до функции deleteland_confirm)

def deleteland_confirm(update: Update, context: CallbackContext):
    try:
        num = int(update.message.text.strip())
        row = context.user_data["deletelist"][num - 1]
        cursor.execute("DELETE FROM lands WHERE rowid = ?", (row[0],))
        conn.commit()
        update.message.reply_text(f"`{row[1]}` удалён ✅", parse_mode="Markdown", reply_markup=main_keyboard)
    except Exception as e:
        update.message.reply_text("Некорректный номер. Попробуйте ещё раз или /cancel")
        return DELETE_SELECT
    return ConversationHandler.END

# остальной код тот же

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Действие отменено.", reply_markup=main_keyboard)
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler("addland", addland_start)],
        states={
            ASK_NAME: [MessageHandler(Filters.text & ~Filters.command, addland_name)],
            ASK_TAIL: [MessageHandler(Filters.text & ~Filters.command, addland_tail)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler("getlink", getlink_start)],
        states={
            WAIT_DOMAIN: [MessageHandler(Filters.text & ~Filters.command, getlink_domain)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler("deleteland", deleteland_start)],
        states={
            DELETE_SELECT: [MessageHandler(Filters.text & ~Filters.command, deleteland_confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
