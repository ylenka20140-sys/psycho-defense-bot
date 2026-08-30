import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from aiohttp import web
import asyncio
import threading

# ===== НАСТРОЙКИ =====
VK_TOKEN = os.environ.get("VK_TOKEN", "vk1.a.a_3dITwtsV9pQscXoUm1fgSpAtJDYBCaFkPZ30GRn4KqdpreBbX_9TP_e5oKJ7Kq5VSu_b1wKtNjcadpGDpN8AOxuipt34XEIvsW8KohkWGBO2Xtp7X5EK2H4e4ScGGWnRAWOx0726cjUYPWwtVX-wK_39mIA_nM0SCyvKhr6KgNbGZeqnTDp4ru_hSXj9jTeHkpBG1xPcYkNoanCMfY-g")
GROUP_ID = int(os.environ.get("GROUP_ID", "240718452"))
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "111655732").split(",")]
VK_COMMUNITY_URL = os.environ.get("VK_COMMUNITY_URL", "https://vk.com/club240718452")
STATS_FILE = "stats.json"
PORT = int(os.environ.get("PORT", "10000"))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация VK API
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

# Хранилище состояний пользователей
user_states = {}

# Определение вопросов (оставьте без изменений)
QUESTIONS = [
    # ... все 24 вопроса ...
]

# Описание шкал (оставьте без изменений)
SCALES = {
    # ... все 7 шкал ...
}

def check_subscription(user_id):
    """Проверка подписки на группу"""
    try:
        response = vk.groups.isMember(
            group_id=GROUP_ID,
            user_id=user_id
        )
        return response == 1
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

def create_subscription_keyboard():
    """Клавиатура для подписки"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("✅ Подписаться", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("🔄 Проверить подписку", color=VkKeyboardColor.PRIMARY)
    return keyboard

def create_keyboard(buttons_text, one_time=False):
    """Создание клавиатуры"""
    keyboard = VkKeyboard(one_time=one_time)
    
    for i, text in enumerate(buttons_text):
        if i > 0:
            keyboard.add_line()
        keyboard.add_button(text, color=VkKeyboardColor.SECONDARY)
    
    return keyboard

def create_start_keyboard():
    """Клавиатура для старта"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("🚀 Начать тест", color=VkKeyboardColor.POSITIVE)
    return keyboard

def calculate_results(answers):
    """Подсчет результатов"""
    scale_scores = {i: 0 for i in range(1, 8)}
    
    for i, answer in enumerate(answers):
        question = QUESTIONS[i]
        for scale in question["scales"]:
            scale_scores[scale] += answer
    
    dominant_type = max(scale_scores, key=scale_scores.get)
    dominant_score = scale_scores[dominant_type]
    
    sorted_scales = sorted(scale_scores.items(), key=lambda x: x[1], reverse=True)
    secondary_type = None
    secondary_score = 0
    
    if len(sorted_scales) > 1:
        second_scale, second_score = sorted_scales[1]
        if second_score >= dominant_score * 0.7:
            secondary_type = second_scale
            secondary_score = second_score
    
    return {
        "scores": scale_scores,
        "dominant_type": dominant_type,
        "dominant_score": dominant_score,
        "secondary_type": secondary_type,
        "secondary_score": secondary_score
    }

def format_result_message(results):
    """Форматирование результата"""
    dominant = SCALES[results["dominant_type"]]
    
    message = f"""
🎯 Ваш результат

{dominant['name']}
📊 Термин: {dominant['term']}

Как проявляется:
{dominant['description']}

Цена такого стиля:
{dominant['price']}

Скрытый девиз:
{dominant['motto']}

Что делать:
{dominant['advice']}

📈 Балл: {results['dominant_score']}
"""
    
    if results["secondary_type"]:
        secondary = SCALES[results["secondary_type"]]
        message += f"""
🔹 Дополнительный тип: {secondary['name']}
📊 Термин: {secondary['term']}
"""
    
    message += f"""
💬 Хотите получить персональные рекомендации?
👉 {VK_COMMUNITY_URL}
"""
    
    return message

def send_message(user_id, text, keyboard=None):
    """Отправка сообщения"""
    try:
        params = {
            'user_id': user_id,
            'message': text,
            'random_id': 0
        }
        
        if keyboard:
            params['keyboard'] = keyboard.get_keyboard()
        
        vk.messages.send(**params)
        logger.info(f"Сообщение отправлено пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")

def process_message(event):
    """Обработка входящего сообщения"""
    user_id = event.user_id
    text = event.text.lower().strip()
    
    logger.info(f"Получено сообщение от {user_id}: {text}")
    
    # Проверка подписки (кроме админов)
    is_subscribed = check_subscription(user_id) if user_id not in ADMIN_IDS else True
    
    # Если не подписан и не админ
    if not is_subscribed:
        # Проверяем команду "проверить подписку"
        if text == "🔄 проверить подписку":
            if check_subscription(user_id):
                send_message(
                    user_id,
                    "✅ Спасибо за подписку! Теперь вы можете пройти тест.",
                    create_start_keyboard()
                )
                user_states[user_id] = {"state": "subscribed"}
            else:
                send_message(
                    user_id,
                    "❌ Вы ещё не подписались. Пожалуйста, подпишитесь на группу.",
                    create_subscription_keyboard()
                )
        else:
            # Предлагаем подписаться
            subscription_text = (
                "👋 Здравствуйте!\n\n"
                "Для прохождения теста необходимо подписаться на нашу группу.\n\n"
                "Подпишитесь и нажмите «Проверить подписку»."
            )
            send_message(user_id, subscription_text, create_subscription_keyboard())
        
        return
    
    # Команды старта (включая "тест" в любом регистре)
    if text in ["начать", "старт", "start", "/start", "привет", "тест"]:
        user_states[user_id] = {"state": "waiting_start"}
        
        welcome_text = (
            "👋 Здравствуйте!\n\n"
            "Это тест «Ваше эмоциональное реагирование»\n"
            "Тест на определение индивидуального стиля совладания с эмоциями\n\n"
            "Он поможет вам узнать ваш индивидуальный стиль эмоционального реагирования.\n\n"
            "⚠️ Важно: нет правильных и неправильных ответов.\n\n"
            "📝 Тест состоит из 24 вопросов и займёт около 5–7 минут.\n\n"
            "Нажмите кнопку ниже, чтобы начать тест."
        )
        
        send_message(user_id, welcome_text, create_start_keyboard())
    
    # Начало теста
    elif text == "🚀 начать тест":
        user_states[user_id] = {
            "state": "taking_test",
            "current_question": 0,
            "answers": []
        }
        show_question(user_id)
    
    # Повторное прохождение
    elif text == "🔄 пройти тест снова":
        user_states[user_id] = {
            "state": "taking_test",
            "current_question": 0,
            "answers": []
        }
        show_question(user_id)
    
    # Ответы на вопросы
    elif user_id in user_states and user_states[user_id].get("state") == "taking_test":
        process_answer(user_id, text)
    
    # Админ-панель
    elif text in ["/admin", "админ", "статистика"] and user_id in ADMIN_IDS:
        show_stats(user_id)
    
    # Помощь
    elif text in ["/help", "помощь", "help"]:
        help_text = (
            "🤖 Доступные команды:\n\n"
            "• Начать / Привет / Тест - начать тест\n"
            "• Помощь - показать справку\n"
            "• Статистика - статистика (для админов)"
        )
        send_message(user_id, help_text)
    
    # Неизвестная команда
    else:
        send_message(
            user_id,
            "Используйте «Начать», «Привет» или «Тест» для начала теста.",
            create_start_keyboard()
        )

def show_question(user_id):
    """Показ вопроса"""
    user_data = user_states[user_id]
    current = user_data["current_question"]
    
    if current < len(QUESTIONS):
        question = QUESTIONS[current]
        
        block_names = {
            "A": "Реакция на злость и конфликт",
            "B": "Реакция на тревогу и страх",
            "C": "Реакция на грусть, вину и неудачи"
        }
        
        text = f"📋 Вопрос {current + 1} из {len(QUESTIONS)}\n\n"
        text += f"📌 {block_names[question['block']]}\n\n"
        text += question["text"]
        
        keyboard = create_keyboard([
            "1 - Совсем не про меня",
            "2 - Иногда бывает",
            "3 - Часто бывает",
            "4 - Это точно про меня"
        ])
        
        send_message(user_id, text, keyboard)
    else:
        finish_test(user_id)

def process_answer(user_id, text):
    """Обработка ответа"""
    answer = None
    if text.startswith("1"):
        answer = 1
    elif text.startswith("2"):
        answer = 2
    elif text.startswith("3"):
        answer = 3
    elif text.startswith("4"):
        answer = 4
    
    if answer is None:
        send_message(user_id, "Выберите ответ от 1 до 4")
        return
    
    user_data = user_states[user_id]
    user_data["answers"].append(answer)
    user_data["current_question"] += 1
    
    show_question(user_id)

def finish_test(user_id):
    """Завершение теста"""
    user_data = user_states[user_id]
    answers = user_data["answers"]
    
    if len(answers) == len(QUESTIONS):
        results = calculate_results(answers)
        message = format_result_message(results)
        send_message(user_id, message)
        
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button("🔄 Пройти тест снова", color=VkKeyboardColor.POSITIVE)
        
        send_message(user_id, "Хотите пройти тест ещё раз?", keyboard)
    
    user_states[user_id] = {"state": "idle"}

def show_stats(user_id):
    """Показ статистики"""
    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            stats = json.load(f)
    except FileNotFoundError:
        stats = {"users": [], "total_tests": 0, "scale_stats": {}}
    
    text = f"📊 Статистика:\n\nВсего тестов: {stats.get('total_tests', 0)}\n"
    
    if 'scale_stats' in stats and stats['scale_stats']:
        text += "\nРаспределение по типам:\n"
        for scale_id, count in stats['scale_stats'].items():
            if count > 0:
                scale_name = SCALES.get(int(scale_id), {}).get('name', f'Тип {scale_id}')
                text += f"• {scale_name}: {count}\n"
    
    send_message(user_id, text)

def run_longpoll():
    """Запуск Long Poll в отдельном потоке"""
    logger.info("VK бот запущен")
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            try:
                process_message(event)
            except Exception as e:
                logger.error(f"Ошибка обработки сообщения: {e}")

async def handle_health(request):
    """HTTP для Render"""
    return web.Response(text="Bot is running")

async def main():
    """Запуск HTTP сервера и бота"""
    # Запускаем Long Poll в отдельном потоке
    longpoll_thread = threading.Thread(target=run_longpoll, daemon=True)
    longpoll_thread.start()
    
    # HTTP сервер для Render
    app = web.Application()
    app.router.add_get('/', handle_health)
    app.router.add_get('/health', handle_health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logger.info(f"HTTP сервер запущен на порту {PORT}")
    
    # Держим сервер запущенным
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
