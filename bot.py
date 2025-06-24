
import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

logging.basicConfig(level=logging.INFO)
TOKEN = "7974469546:AAE1GfJKvHlMxTz1_PTwkKsZcLsQZBsywh8"

# Состояния
ASK_NAME, ASK_TAIL = range(2)
WAIT_DOMAIN = range(1)
DELETE_SELECT = range(1)

# Подключение к базе
conn = sqlite3.connect("lands.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS lands (name TEXT, tail TEXT)")
conn.commit()

temp_data = {}

# Кнопки
main_keyboard = ReplyKeyboardMarkup(
    [["/addland", "/getlink"], ["/deleteland"]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать! Выберите действие:",
        reply_markup=main_keyboard
    )

# Добавление ленда
async def addland_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Как называется ленд?")
    return ASK_NAME

async def addland_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    temp_data[user_id] = {"name": update.message.text}
    await update.message.reply_text("Отправь мне хвост лендинга.")
    return ASK_TAIL

async def addland_tail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tail = update.message.text
    name = temp_data[user_id]["name"]
    cursor.execute("INSERT INTO lands (name, tail) VALUES (?, ?)", (name, tail))
    conn.commit()
    await update.message.reply_text(f"Ленд `{name}` успешно сохранён ✅", parse_mode="Markdown", reply_markup=main_keyboard)
    return ConversationHandler.END

# Получение ссылок
async def getlink_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправьте домен (например: 1wpnwn.top)")
    return WAIT_DOMAIN

async def getlink_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    domain = update.message.text.strip().rstrip("/")
    if not domain.startswith("http"):
        domain = "https://" + domain

    cursor.execute("SELECT name, tail FROM lands")
    lands = cursor.fetchall()

    if not lands:
        await update.message.reply_text("База пуста. Добавьте ленды через /addland.", reply_markup=main_keyboard)
        return ConversationHandler.END

    messages = [f"`{name}`\n`{domain}{tail}`" for name, tail in lands]
    await update.message.reply_text("\n\n".join(messages), parse_mode="MarkdownV2", reply_markup=main_keyboard)
    return ConversationHandler.END

# Удаление ленда
async def deleteland_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT rowid, name FROM lands")
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("База пуста, нечего удалять.", reply_markup=main_keyboard)
        return ConversationHandler.END

    msg = "Выберите номер ленда для удаления:\n"
    for i, (rowid, name) in enumerate(rows, start=1):
        msg += f"{i}. {name}\n"

    context.user_data["deletelist"] = rows
    await update.message.reply_text(msg)
    return DELETE_SELECT

async def deleteland_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        num = int(update.message.text.strip())
        row = context.user_data["deletelist"][num - 1]
        cursor.execute("DELETE FROM lands WHERE rowid = ?", (row[0],))
        conn.commit()
        await update.message.reply_text(f"Ленд `{row[1]}` удалён ✅", parse_mode="Markdown", reply_markup=main_keyboard)
    except:
        await update.message.reply_text("Некорректный номер. Попробуйте ещё раз или /cancel")
        return DELETE_SELECT

    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=main_keyboard)
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("addland", addland_start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, addland_name)],
            ASK_TAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, addland_tail)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("getlink", getlink_start)],
        states={
            WAIT_DOMAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, getlink_domain)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("deleteland", deleteland_start)],
        states={
            DELETE_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, deleteland_confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.run_polling()

if __name__ == "__main__":
    main()
