import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
from agent.core import Agent
from database import (
    has_active_subscription, 
    get_subscription_status, 
    create_gift_code,
    redeem_gift_code,
    SUBSCRIPTION_PLANS
)
from payments import create_payment_link, YookassaPaymentError
from tools.marketplace_tools import MarketplaceParserTool, PriceComparisonTool
from tools.file_splitter import FileSplitter
from tools.excel_generator import ExcelGenerator

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
        "Интеллектуальный AI-ассистент для задач, анализа информации "
        "и автоматизации повседневной работы.\n\n"
        "Что я умею:\n"
        "• Анализировать информацию\n"
        "• Парсить маркетплейсы (Озон, Валберис, Яндекс Маркет)\n"
        "• Генерировать Excel отчёты\n"
        "• Решать повседневные задачи\n"
        "• Давать структурированные ответы\n\n"
        "Команды:\n"
        "/subscribe - Подписка на платные функции\n"
        "/status - Статус вашей подписки\n"
        "/redeem - Активировать подарочный код\n\n"
        "Просто напишите ваш запрос..."
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@dp.message(Command("subscribe"))
async def subscribe_handler(message: Message):
    """Показать доступные подписки"""
    plans_text = "💳 Доступные подписки OmniGuard:\n\n"
    
    for plan_key, plan_info in SUBSCRIPTION_PLANS.items():
        plans_text += f"• {plan_info['name']}: {plan_info['price']} ₽\n"
    
    plans_text += "\nВыберите план отправив его номер (например, '1'):\n"
    plans_text += "1️⃣ 1 месяц\n"
    plans_text += "2️⃣ 3 месяца\n"
    plans_text += "3️⃣ 6 месяцев\n"
    
    msg = await message.answer(plans_text)
    
    # Сохраним ID сообщения для обработки ответа
    await message.answer("Отправьте номер плана:")

@dp.message(Command("status"))
async def status_handler(message: Message):
    """Показать статус подписки"""
    status = get_subscription_status(message.from_user.id)
    
    if status["has_subscription"]:
        status_text = (
            f"✅ У вас есть подписка\n\n"
            f"План: {status['plan_name']}\n"
            f"Дней осталось: {status['days_left']}\n"
            f"Истекает: {status['end_date']}"
        )
    else:
        status_text = (
            f"❌ У вас нет активной подписки\n\n"
            f"Используйте /subscribe для активации платных функций"
        )
    
    await message.answer(status_text)

@dp.message(Command("redeem"))
async def redeem_handler(message: Message):
    """Активировать подарочный код"""
    await message.answer("Отправьте подарочный код:")

@dp.message(Command("giftcode"))
async def giftcode_handler(message: Message):
    """Команда овнера для создания подарочного кода"""
    user_id = message.from_user.id
    
    if user_id not in OWNER_IDS:
        await message.answer("❌ Только овнер может создавать подарочные коды")
        return
    
    args = message.text.split()
    if len(args) < 2:
        plans_list = ", ".join(SUBSCRIPTION_PLANS.keys())
        await message.answer(
            f"Использование: /giftcode <план>\n"
            f"Доступные планы: {plans_list}"
        )
        return
    
    plan_key = args[1]
    
    if plan_key not in SUBSCRIPTION_PLANS:
        await message.answer(f"❌ План '{plan_key}' не найден")
        return
    
    code = create_gift_code(user_id, plan_key)
    plan = SUBSCRIPTION_PLANS[plan_key]
    
    await message.answer(
        f"✅ Подарочный код создан!\n\n"
        f"План: {plan['name']}\n"
        f"Код: `{code}`\n\n"
        f"Отправьте этот код пользователю для активации",
        parse_mode="Markdown"
    )

@dp.message()
async def handle_message(message: Message):
    status_message = None
    animation_task = None
    try:
        text = message.text
        print(f"📩 Новое сообщение: {text}")
        
        user_id = message.from_user.id
        
        # Проверка на номер плана в subscribe
        if text in ['1', '2', '3']:
            plan_keys = ['month_1', 'month_3', 'month_6']
            plan_key = plan_keys[int(text) - 1]
            
            try:
                # Создаём платёж
                payment = create_payment_link(
                    user_id,
                    plan_key,
                    return_url="https://example.com/success"
                )
                
                if payment['success']:
                    await message.answer(
                        f"💳 Переход к оплате {payment['amount']} ₽\n"
                        f"План: {payment['plan_name']}\n\n"
                        f"Нажмите на ссылку ниже для оплаты:",
                        parse_mode="Markdown"
                    )
                    await message.answer(payment['payment_url'])
            except YookassaPaymentError as e:
                await message.answer(f"❌ Ошибка при создании платежа: {str(e)}")
            return
        
        # Проверка на подарочный код
        if message.text.startswith("GIFT_"):
            result = redeem_gift_code(message.text, user_id)
            
            if result['success']:
                await message.answer(
                    f"✅ Подписка активирована!\n"
                    f"План: {result['plan_name']}"
                )
            else:
                await message.answer(f"❌ {result['error']}")
            return
        
        # Проверка подписки для платных функций
        paid_keywords = ['парс', 'маркет', 'озон', 'валберис', 'яндекс', 'excel', 'отчет', 'отчёт']
        is_paid_function = any(keyword in text.lower() for keyword in paid_keywords)
        
        if is_paid_function:
            if not has_active_subscription(user_id):
                await message.answer(
                    "⚠️ Эта функция требует подписку\n\n"
                    "Используйте /subscribe для активации"
                )
                return
            
            # Обработка парсера
            if any(word in text.lower() for word in ['парс', 'найди', 'поиск', 'маркет']):
                await bot.send_chat_action(message.chat.id, "typing")
                status_message = await message.answer("🔍 Парсю маркетплейсы...")
                
                parser_tool = MarketplaceParserTool()
                response = await asyncio.to_thread(parser_tool.run, text)
                
                await message.answer(response)
                
                # Отправить файл если он был создан
                if "Файл создан:" in response:
                    import re
                    match = re.search(r"Файл создан: ([\w\-/\\\.]+\.xlsx)", response)
                    if match:
                        filepath = match.group(1)
                        if os.path.exists(filepath):
                            file_size = FileSplitter.get_file_size(filepath)
                            
                            if FileSplitter.needs_split(filepath):
                                success, parts = FileSplitter.split_file(filepath)
                                if success:
                                    split_msg = FileSplitter.get_split_message(len(parts), os.path.basename(filepath))
                                    await message.answer(split_msg)
                                    
                                    for part in parts:
                                        with open(part, 'rb') as f:
                                            await bot.send_document(
                                                message.chat.id,
                                                f,
                                                caption=f"Часть файла: {os.path.basename(part)}"
                                            )
                            else:
                                with open(filepath, 'rb') as f:
                                    await bot.send_document(
                                        message.chat.id,
                                        f,
                                        caption="Excel отчёт"
                                    )
                
                if status_message:
                    await bot.delete_message(chat_id=message.chat.id, message_id=status_message.message_id)
                
                return
            
            # Обработка сравнения цен
            if any(word in text.lower() for word in ['сравни', 'цена', 'дешевле']):
                await bot.send_chat_action(message.chat.id, "typing")
                status_message = await message.answer("💰 Сравниваю цены...")
                
                comparison_tool = PriceComparisonTool()
                response = await asyncio.to_thread(comparison_tool.run, text)
                
                await message.answer(response)
                
                if status_message:
                    await bot.delete_message(chat_id=message.chat.id, message_id=status_message.message_id)
                
                return
        
        # Обычный запрос к агенту
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
            user_id,
            text
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
            try:
                await status_message.edit_text(
                    "Не удалось обработать запрос.\nПопробуй иначе."
                )
            except:
                pass

async def main():
    print("🛡️ OmniGuard запущен и работает...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())