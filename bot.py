import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "7658695918:AAGcL-28T2Gn7WtMopzbYKlElJtzglKXNKQ"
# 📁 файл с пользователями
FILE_NAME = "users.json"

ADMIN_ID = "651360759"

 # пользевати
ALLOWED_USERS = [
    "651360759",   # Женя
    "5930028202",  # Серёжа
    "973686093",   # Аристарх
    "1349941724",  # Юлик
    "1088291620",  # Ростик
    "1835127811"   # Саша
]
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

    # 🔒 ПРОВЕРКА ДОБАВЛЕНА
    if user_id not in ALLOWED_USERS:
        await message.answer(
        f"🚫 Нет доступа\n\nТвой ID: {user_id}"
        )

        # 👑 админу сообщение
        await bot.send_message(
            ADMIN_ID,
            f"🚨 Новый пользователь хочет доступ:\n\nID: {user_id}\nUsername: @{username}"
         )

        return

    # ✅ добавляем ТОЛЬКО разрешённых
    if user_id not in users_db:
        users_db[user_id] = {
            "name": name,
            "username": username
        }

    save_users(users_db)

    # 👤 обычная клавиатура
    keyboard = [
        [KeyboardButton(text="📅 Дежурство")],
        [KeyboardButton(text="📊 Очередь"), KeyboardButton(text="🔜 Следующий")]
    ]

    # 👑 если админ — добавляем кнопку
    if user_id == ADMIN_ID:
        keyboard.append([KeyboardButton(text="👑 Админ панель")])

    markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    await message.answer(
        f"👋 Привет, {name}!\n\nИспользуй кнопки ниже 👇",
        reply_markup=markup
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
    days_left = 3 - (day % 3)

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
    days_left = 3 - (day % 3)
    if days_left == 1:
        days_text = "остался 1 день"
    else:
        days_text = f"осталось {days_left} дня"

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
    days_left = 3 - (day % 3)
    text += f"🟢 Сейчас: {current_name} ({days_text})\n"
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

@dp.message(Command("remove"))
async def remove_user(message: types.Message):
    if str(message.from_user.id) != ADMIN_ID:
        await message.answer("❌ Нет доступа")
        return

    try:
        user_id = message.text.split()[1]

        if user_id in users_db:
            del users_db[user_id]
            save_users(users_db)
            await message.answer("✅ Пользователь удалён")
        else:
            await message.answer("❌ Не найден")

    except:
        await message.answer("⚠ Используй: /remove ID")
@dp.message()
async def duty(message: types.Message):

    # 🔒 доступ нового польщывателя 
    if str(message.from_user.id) not in ALLOWED_USERS:
        await message.answer("🚫 Нет доступа")
        return

    # пропускаем команды
    if message.text.startswith("/"):
        return

    from datetime import date

    users_list = list(users_db.keys())

    if not users_list:
        await message.answer("Нет пользователей 😢")
        return

    day = date.today().toordinal()
    days_left = 3 - (day % 3)
    current_index = (day // 3) % len(users_list)
    current_user_id = users_list[current_index]

    # 👑 Админ панель
    if message.text == "👑 Админ панель":
        if str(message.from_user.id) != ADMIN_ID:
            await message.answer("❌ У тебя нет доступа")
            return

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📋 Список пользователей")],
                [KeyboardButton(text="❌ Удалить пользователя")],
                [KeyboardButton(text="⬅️ Назад")]
            ],
            resize_keyboard=True
        )

        await message.answer("👑 Админ панель", reply_markup=keyboard)

    # 📋 Список пользователей
    elif message.text == "📋 Список пользователей":
        if str(message.from_user.id) != ADMIN_ID:
            return

        text = "👥 Пользователи:\n\n"

        for user_id, data in users_db.items():
            text += f"{data['name']} | ID: {user_id}\n"

        await message.answer(text)

    # ❌ Удаление
    elif message.text.startswith("❌"):
        if str(message.from_user.id) != ADMIN_ID:
            return

        await message.answer("Введи ID пользователя:\n/remove ID")

    # ⬅️ Назад
    elif message.text == "⬅️ Назад":

        user_id = str(message.from_user.id)

        keyboard = [
            [KeyboardButton(text="📅 Дежурство")],
            [KeyboardButton(text="📊 Очередь"), KeyboardButton(text="🔜 Следующий")]
        ]

        # 👑 если админ — добавляем кнопку обратно
        if user_id == ADMIN_ID:
            keyboard.append([KeyboardButton(text="👑 Админ панель")])

        markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

        await message.answer("Главное меню 👇", reply_markup=markup)

    # 📅 Дежурство
    elif message.text == "📅 Дежурство":
        if str(message.from_user.id) == current_user_id:
            days_left = 3 - (day % 3)
            await message.answer("🧹 Сегодня дежуришь ТЫ 😎")
        else:
            name = users_db[current_user_id]["name"]
            days_left = 3 - (day % 3)
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
        days_left = 3 - (day % 3)

        if days_left == 1:
            days_text = "остался 1 день"
        else:
            days_text = f"осталось {days_left} дня"

        await bot.send_message(
            current_user_id,
            f"🧹 Сегодня ты дежурный!\n⏳ {days_text}"
        )

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
