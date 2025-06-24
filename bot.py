import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

TOKEN = "7974469546:AAE1GfJKvHlMxTz1_PTwkKsZcLsQZBsywh8"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

DB_PATH = "data/lands.json"

# FSM
class AddLandState(StatesGroup):
    waiting_for_name = State()
    waiting_for_tail = State()

# Utils
def load_db():
    try:
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_PATH, 'w') as f:
        json.dump(data, f, indent=2)

# /start
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("➕ Добавить ленд"), KeyboardButton("🔗 Получить ссылку"))
    kb.add(KeyboardButton("🗑 Удалить ленд"))
    await message.answer("Выберите действие:", reply_markup=kb)

# /addland
@dp.message_handler(lambda message: message.text == "➕ Добавить ленд")
@dp.message_handler(commands=["addland"])
async def cmd_addland(message: types.Message):
    await message.answer("Как называется ленд?\n\n(или /cancel для отмены)")
    await AddLandState.waiting_for_name.set()

@dp.message_handler(commands=["cancel"], state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Действие отменено.", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(state=AddLandState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(land_name=message.text)
    await message.answer("Отправь мне хвост лендинга\n\n(или /cancel для отмены)")
    await AddLandState.waiting_for_tail.set()

@dp.message_handler(state=AddLandState.waiting_for_tail)
async def process_tail(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    land_name = user_data["land_name"]
    land_tail = message.text

    db = load_db()
    db[land_name] = land_tail
    save_db(db)

    await message.answer(f"✅ Ленд \"{land_name}\" успешно добавлен.", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
