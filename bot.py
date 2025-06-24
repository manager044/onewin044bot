import logging
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import os

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

user_state = {}
temp_data = {}

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("/addland"), KeyboardButton("/getlink"))
    kb.add(KeyboardButton("/deleteland"))
    await message.answer("Выберите действие:", reply_markup=kb)

@dp.message_handler(commands=["addland"])
async def addland_step1(message: types.Message):
    user_state[message.from_user.id] = "waiting_for_name"
    await message.answer("Как называется ленд?", reply_markup=cancel_button())

@dp.message_handler(lambda message: user_state.get(message.from_user.id) == "waiting_for_name")
async def addland_step2(message: types.Message):
    if message.text == "❌ Отмена":
        return await cancel_flow(message)

    temp_data[message.from_user.id] = {"name": message.text}
    user_state[message.from_user.id] = "waiting_for_tail"
    await message.answer("Отправь мне хвост лендинга", reply_markup=cancel_button())

@dp.message_handler(lambda message: user_state.get(message.from_user.id) == "waiting_for_tail")
async def addland_step3(message: types.Message):
    if message.text == "❌ Отмена":
        return await cancel_flow(message)

    tail = message.text
    name = temp_data[message.from_user.id]["name"]

    data = load_data()
    data[name] = tail
    save_data(data)

    user_state.pop(message.from_user.id)
    temp_data.pop(message.from_user.id)
    await message.answer(f"Ленд '{name}' добавлен ✅", reply_markup=ReplyKeyboardRemove())

@dp.message_handler(commands=["getlink"])
async def getlink(message: types.Message):
    user_state[message.from_user.id] = "waiting_for_domain"
    await message.answer("Отправьте домен:", reply_markup=cancel_button())

@dp.message_handler(lambda message: user_state.get(message.from_user.id) == "waiting_for_domain")
async def send_links(message: types.Message):
    if message.text == "❌ Отмена":
        return await cancel_flow(message)

    domain = message.text.rstrip("/")
    data = load_data()

    if not data:
        await message.answer("База пуста.")
    else:
        reply = "\n\n".join(
            [f"{name} - {domain}{tail}" for name, tail in data.items()]
        )
        await message.answer(reply)

    user_state.pop(message.from_user.id)

@dp.message_handler(commands=["deleteland"])
async def deleteland(message: types.Message):
    data = load_data()
    if not data:
        return await message.answer("Нет сохранённых лендов.")

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for name in data:
        kb.add(KeyboardButton(name))
    kb.add(KeyboardButton("❌ Отмена"))

    user_state[message.from_user.id] = "deleting"
    await message.answer("Выберите ленд для удаления:", reply_markup=kb)

@dp.message_handler(lambda message: user_state.get(message.from_user.id) == "deleting")
async def handle_delete(message: types.Message):
    if message.text == "❌ Отмена":
        return await cancel_flow(message)

    data = load_data()
    name = message.text
    if name in data:
        del data[name]
        save_data(data)
        await message.answer(f"Ленд '{name}' удалён ✅", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Такого ленда нет.")
    user_state.pop(message.from_user.id)

def cancel_button():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("❌ Отмена"))
    return kb

async def cancel_flow(message):
    user_state.pop(message.from_user.id, None)
    temp_data.pop(message.from_user.id, None)
    await message.answer("Действие отменено.", reply_markup=ReplyKeyboardRemove())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)