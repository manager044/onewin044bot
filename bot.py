import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
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

class GetLinkState(StatesGroup):
    waiting_for_domain = State()

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

# /getlink
@dp.message_handler(lambda message: message.text == "🔗 Получить ссылку")
@dp.message_handler(commands=["getlink"])
async def cmd_getlink(message: types.Message):
    await message.answer("Отправьте домен, например: https://example.com\n\n(или /cancel для отмены)")
    await GetLinkState.waiting_for_domain.set()

@dp.message_handler(state=GetLinkState.waiting_for_domain)
async def process_domain(message: types.Message, state: FSMContext):
    domain = message.text.strip().rstrip("/")
    db = load_db()
    if not db:
        await message.answer("База данных пуста.")
    else:
        links = [f"{name} - {domain}{tail}" for name, tail in db.items()]
        await message.answer("\n".join(links))
    await state.finish()

# /deleteland
@dp.message_handler(lambda message: message.text == "🗑 Удалить ленд")
@dp.message_handler(commands=["deleteland"])
async def cmd_deleteland(message: types.Message):
    db = load_db()
    if not db:
        await message.answer("Нет добавленных лендов.")
        return

    kb = InlineKeyboardMarkup()
    for name in db.keys():
        kb.add(InlineKeyboardButton(text=name, callback_data=f"delete:{name}"))
    await message.answer("Выберите ленд для удаления:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("delete:"))
async def process_delete(callback_query: types.CallbackQuery):
    land_name = callback_query.data.split(":")[1]
    db = load_db()
    if land_name in db:
        del db[land_name]
        save_db(db)
        await bot.answer_callback_query(callback_query.id, text=f"Удалено: {land_name}")
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=f"✅ Ленд '{land_name}' удалён.")
    else:
        await bot.answer_callback_query(callback_query.id, text="Ленд не найден.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
