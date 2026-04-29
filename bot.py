import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "7658695918:AAFd7MKHYqLwMQiPDOVH0GhJFwtwOEc4rP0"
# 📁 файл с пользователями
FILE_NAME = "users.json"

# загрузка пользователей
def load_users():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# сохранение пользователей
def save_users(data):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# загружаем при старте
users_db = load_users()
bot = Bot(token=TOKEN)
dp = Dispatcher()

users = ["Серёжа", "Женя", "Юлик", "Саша", "Ростик", "Арик"]

def get_today_user():
    from datetime import date

    users_list = list(users_db.keys())

    if not users_list:
        return None

    start_day = 1  # можно потом поменять

    day = date.today().toordinal() - start_day

    index = (day // 3) % len(users_list)

    user_id = users_list[index]
    return users_db[user_id]["name"]
    

@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    name = message.from_user.first_name

    users_db[user_id] = {
        "name": name,
        "username": username
    }

    save_users(users_db)

    # 👇 ВСЁ должно быть с одинаковыми отступами (4 пробела)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Дежурство")],
            [KeyboardButton(text="📊 Очередь"), KeyboardButton(text="🔜 Следующий")]
        ],
        resize_keyboard=True
    )

    await message.answer(
    f"👋 Привет, {name}!\n\n"
    "Этот бот помогает следить за дежурствами 🧹\n\n"
    "👇 Используй кнопки ниже",
    reply_markup=keyboard
)

@dp.message(Command("today"))
async def today(message: types.Message):
    user = get_today_user()

    if not user:
        await message.answer("Нет пользователей 😢")
        return

    await message.answer(f"Сегодня дежурит: {user}")
    
# 🔹 Обрабатываем ВСЕ сообщения (включая кнопку)

@dp.message(Command("next"))
async def next_duty(message: types.Message):
    from datetime import date

    users_list = list(users_db.keys())

    if not users_list:
        await message.answer("Нет пользователей 😢")
        return

    day = date.today().toordinal()

    current_index = (day // 3) % len(users_list)
    next_index = (current_index + 1) % len(users_list)

    next_user_id = users_list[next_index]
    name = users_db[next_user_id]["name"]

    await message.answer(f"🔜 Следующий дежурный: {name}")

@dp.message(Command("queue"))
async def queue(message: types.Message):
    from datetime import date

    # список пользователей
    users_list = list(users_db.keys())

    if not users_list:
        await message.answer("Нет пользователей 😢")
        return

    # текущий день
    day = date.today().toordinal()

    # текущий дежурный
    current_index = (day // 3) % len(users_list)
    current_user_id = users_list[current_index]
    current_name = users_db[current_user_id]["name"]

    # следующий дежурный
    next_index = (current_index + 1) % len(users_list)
    next_user_id = users_list[next_index]
    next_name = users_db[next_user_id]["name"]

    # собираем текст
    text = "🧹 Дежурства\n\n"
    text += f"🟢 Сейчас: {current_name}\n"
    text += f"🔜 Следующий: {next_name}\n\n"
    text += "📊 Очередь:\n"

    # список всех
    for i, user_id in enumerate(users_list):
        name = users_db[user_id]["name"]

        # подсветка текущего
        if user_id == current_user_id:
            text += f"{i+1}. {name} 👈\n"
        else:
            text += f"{i+1}. {name}\n"

    await message.answer(text)
@dp.message()
async def duty(message: types.Message):

    # пропускаем команды
    if message.text.startswith("/"):
        return

    from datetime import date

    users_list = list(users_db.keys())

    if not users_list:
        await message.answer("Нет пользователей 😢")
        return

    day = date.today().toordinal()
    current_index = (day // 3) % len(users_list)
    current_user_id = users_list[current_index]

    # 📅 Дежурство
    if message.text == "📅 Дежурство":
        if str(message.from_user.id) == current_user_id:
            await message.answer("🧹 Сегодня дежуришь ТЫ 😎")
        else:
            name = users_db[current_user_id]["name"]
            await message.answer(f"🧹 Сегодня дежурит: {name}")

    # 📊 Очередь
    elif message.text == "📊 Очередь":
        next_index = (current_index + 1) % len(users_list)
        next_user_id = users_list[next_index]
        next_name = users_db[next_user_id]["name"]

        text = "🧹 Дежурства\n\n"
        text += f"🟢 Сейчас: {users_db[current_user_id]['name']}\n"
        text += f"🔜 Следующий: {next_name}\n\n"
        text += "📊 Очередь:\n"

        for i, user_id in enumerate(users_list):
            name = users_db[user_id]["name"]
            if user_id == current_user_id:
                text += f"{i+1}. {name} 👈\n"
            else:
                text += f"{i+1}. {name}\n"

        await message.answer(text)

    # 🔜 Следующий
    elif message.text == "🔜 Следующий":
        next_index = (current_index + 1) % len(users_list)
        next_user_id = users_list[next_index]
        name = users_db[next_user_id]["name"]

        await message.answer(f"🔜 Следующий дежурный: {name}")

    else:
        await message.answer("Выбери кнопку 👇")


# 🔔 УВЕДОМЛЕНИЯ
async def send_daily_notifications():
    from datetime import date

    users_list = list(users_db.keys())

    if not users_list:
        return

    day = date.today().toordinal()
    index = (day // 3) % len(users_list)

    current_user_id = users_list[index]

    try:
        await bot.send_message(current_user_id, "🧹 Сегодня ты дежурный!")
    except:
        print("Не удалось отправить сообщение (пользователь не запустил бота)")


# 👇 ВОТ ТУТ У ТЕБЯ УЖЕ ЕСТЬ
async def main():
    scheduler = AsyncIOScheduler()

    # ⏰ каждый день в 11:00
    scheduler.add_job(
    send_daily_notifications,
    "cron",
    hour=11,
    minute=0,
    timezone="Europe/Vienna"
)


    scheduler.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
