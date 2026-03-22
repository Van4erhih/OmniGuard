import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
from agent.core import Agent

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
OWNER_IDS = [8423224687]
USERS_FILE = "users.json"

logging.basicConfig(level=logging.INFO)

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)

def get_user_role(user_id):
    if user_id in OWNER_IDS:
        return "owner"
    users = load_users()
    user_id = str(user_id)

    if user_id in users:
        return users[user_id]["role"]

    return "free"

bot = Bot(token=TOKEN)
dp = Dispatcher()
agent = Agent()

@dp.message(Command("start"))
async def start_handler(message: Message):
    welcome_text = (
        "🛡️ OmniGuard\n\n"
        "Интеллектуальный AI-ассистент для задач, анализа информации  "
        "и автоматизации повседневной работы.\n\n"
        "Что я умею:\n"
        "• Анализировать информацию\n"
        "• Помогать в обучении\n"
        "• Решать повседневные задачи\n"
        "• Давать структурированные ответы\n\n"
        "Просто напишите ваш запрос..."
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@dp.message()
async def handle_message(message: Message):
    status_message = None
    animation_task = None
    try:
        print(f"📩 Новое сообщение: {message.text}")

        await bot.send_chat_action(message.chat.id, "typing")
        status_message = await message.answer("🤔 Анализирую запрос...")

        async def animate():
            dots = ["", ".", "..", "..."]
            i = 0
            while True:
                await asyncio.sleep(0.8)
                await status_message.edit_text(
                    f"🤔 Анализирую запрос{dots[i % 4]}"
                )
                i += 1

        animation_task = asyncio.create_task(animate())

        response = await asyncio.to_thread(
            agent.run,
            message.from_user.id,
            message.text
        )

        animation_task.cancel()

        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=status_message.message_id
        )

        await message.answer(response)

        print("✅ Ответ отправлен\n")

    except Exception as e:
        print("BOT ERROR:", e)

        if animation_task:
            animation_task.cancel()

        if status_message:
            await status_message.edit_text(
                "Не удалось обработать запрос.\nПопробуй иначе."
            )

async def main():
    print("🛡️ OmniGuard запущен и работает...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())