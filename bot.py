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

# ===== ТРИГГЕРЫ ДЛЯ ТЕСТОВ =====
# Сейчас только один тест, но можно добавить больше
TEST_TRIGGERS = {
    "emotional": ["тест", "тест на эмоции", "эмоциональное реагирование"],
    # Добавьте новые тесты здесь:
    # "depression": ["депрессия", "тест на депрессию"],
    # "anxiety": ["тревога", "тест на тревожность"],
}

# Определение вопросов
QUESTIONS = [
    # Блок A: Реакция на злость и конфликт (вопросы 1-8)
    {"id": 1, "block": "A", "text": "Когда я злюсь, я говорю «всё нормально», хотя внутри всё кипит", "scales": [1]},
    {"id": 2, "block": "A", "text": "Я скорее промолчу, чем вступлю в конфликт, даже если меня обидели", "scales": [1]},
    {"id": 3, "block": "A", "text": "Если на меня накричали, я потом срываюсь на том, кто слабее (ребёнок, животное, подчинённый)", "scales": [2]},
    {"id": 4, "block": "A", "text": "Я могу кричать, бить посуду или хлопать дверью, когда меня довели", "scales": [2]},
    {"id": 5, "block": "A", "text": "Я долго ношу обиду в себе и прокручиваю в голове, что надо было ответить", "scales": [3]},
    {"id": 6, "block": "A", "text": "После ссоры я не могу уснуть, потому что мысленно продолжаю спор", "scales": [3]},
    {"id": 7, "block": "A", "text": "Я убеждён, что злиться — это плохо и стыдно", "scales": [1]},
    {"id": 8, "block": "A", "text": "Я стараюсь вообще не попадать в ситуации, где возможен конфликт", "scales": [4]},
    
    # Блок B: Реакция на тревогу и страх (вопросы 9-16)
    {"id": 9, "block": "B", "text": "Когда я тревожусь, я начинаю есть, даже если не голоден", "scales": [5]},
    {"id": 10, "block": "B", "text": "От тревоги у меня пропадает аппетит", "scales": [5]},
    {"id": 11, "block": "B", "text": "Чтобы успокоиться, мне нужно выпить, покурить или принять что-то", "scales": [5]},
    {"id": 12, "block": "B", "text": "Я загружаю себя делами, чтобы не чувствовать тревогу", "scales": [6]},
    {"id": 13, "block": "B", "text": "Я часами сижу в телефоне/сериалах/играх, чтобы убежать от неприятных мыслей", "scales": [4]},
    {"id": 14, "block": "B", "text": "Я фантазирую о другой жизни, где у меня всё хорошо", "scales": [4]},
    {"id": 15, "block": "B", "text": "Я постоянно проверяю и перепроверяю всё, чтобы не случилось ничего плохого", "scales": [6]},
    {"id": 16, "block": "B", "text": "Мне нужно, чтобы всё было предсказуемо, иначе я не могу расслабиться", "scales": [6]},
    
    # Блок C: Реакция на грусть, вину и неудачи (вопросы 17-24)
    {"id": 17, "block": "C", "text": "Когда что-то идёт не так, я виню в этом только себя", "scales": [7]},
    {"id": 18, "block": "C", "text": "Я называю себя глупым/никчёмным, когда ошибаюсь", "scales": [7]},
    {"id": 19, "block": "C", "text": "Я говорю себе «да ерунда, не стоит расстраиваться», чтобы не плакать", "scales": [1]},
    {"id": 20, "block": "C", "text": "Я обесцениваю свои проблемы: «кому-то хуже, чем мне»", "scales": [1]},
    {"id": 21, "block": "C", "text": "Я ухожу в работу с головой, чтобы не чувствовать боль/грусть", "scales": [6]},
    {"id": 22, "block": "C", "text": "Я могу сутками лежать и ничего не делать, когда мне плохо", "scales": [4]},
    {"id": 23, "block": "C", "text": "Я заедаю грусть или наоборот — не могу есть совсем", "scales": [5]},
    {"id": 24, "block": "C", "text": "Мне сложно просить помощи, я должен справляться сам", "scales": [6]},
]

# Описание шкал
SCALES = {
    1: {
        "name": "Подавитель",
        "term": "Вытеснение (репрессия)",
        "description": "«Я не чувствую» / «Я справлюсь сам». Эмоции замораживаются, человек выглядит спокойным, но внутри — вулкан.",
        "price": "Психосоматика (головные боли, давление, панические атаки «на ровном месте»), эмоциональная глухота к близким.",
        "motto": "«Если я не признаю чувство — его нет».",
        "advice": "Учиться замечать телесные сигналы (зажимы, дыхание) и называть эмоции словами. Начните с фразы: «Мне сейчас неприятно, и это нормально»."
    },
    2: {
        "name": "Взрыватель",
        "term": "Отреагирование / Замещение",
        "description": "Эмоция не удерживается внутри, а мгновенно выплёскивается на того, кто под рукой.",
        "price": "Разрушенные отношения, чувство вины после вспышек, репутация «истерика» или «агрессора».",
        "motto": "«Лучше выпустить пар, чем лопнуть».",
        "advice": "Отслеживать первые признаки нарастающего гнева (сжатые кулаки, жар, учащённое дыхание) и делать паузу. Задайте себе вопрос: «На кого я на самом деле злюсь?»"
    },
    3: {
        "name": "Мыслитель",
        "term": "Руминация / Интеллектуализация",
        "description": "Вместо того чтобы чувствовать, человек начинает бесконечно анализировать.",
        "price": "Истощение мозга, бессонница, жизнь «в голове», потеря контакта с телом и реальностью.",
        "motto": "«Если я всё пойму, мне станет легче».",
        "advice": "Переключаться с мыслей на тело. Спросить себя: «Где я это чувствую физически?»"
    },
    4: {
        "name": "Убегающий",
        "term": "Избегание / Эскапизм",
        "description": "Любой способ уйти от реальности: сериалы, игры, сон, фантазии, соцсети.",
        "price": "Проблемы копятся, жизнь проходит мимо.",
        "motto": "«Если я не вижу проблему — её не существует».",
        "advice": "Начать с малого: 10 минут в день оставаться наедине с собой."
    },
    5: {
        "name": "Заглушающий",
        "term": "Химический / Пищевой копинг",
        "description": "Тело используется как контейнер для эмоций.",
        "price": "Зависимость, разрушение здоровья, стыд.",
        "motto": "«Если я изменю химию тела, я перестану чувствовать».",
        "advice": "Вести дневник: записывать, какая эмоция предшествовала импульсу."
    },
    6: {
        "name": "Контролёр",
        "term": "Гиперконтроль / Перфекционизм",
        "description": "Попытка устранить тревогу через тотальный контроль.",
        "price": "Истощение, выгорание, одиночество.",
        "motto": "«Если я всё контролирую, со мной не случится ничего плохого».",
        "advice": "Тренироваться отпускать: начать с мелочей."
    },
    7: {
        "name": "Самонаказывающий",
        "term": "Аутоагрессия",
        "description": "Вся агрессия направляется на себя.",
        "price": "Депрессия, низкая самооценка.",
        "motto": "«Лучше я сам себя накажу».",
        "advice": "Говорить с собой так, как с другом."
    }
}

def check_subscription(user_id):
    """Проверка подписки на группу"""
    try:
        if user_id in ADMIN_IDS:
            return True
        
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
    
    keyboard.add_openlink_button(
        label="📢 Подписаться на группу",
        link=f"https://vk.com/club{GROUP_ID}"
    )
    keyboard.add_line()
    
    keyboard.add_button("✅ Проверить подписку", color=VkKeyboardColor.POSITIVE)
    
    return keyboard

def create_start_keyboard():
    """Клавиатура для старта"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("🚀 Начать тест", color=VkKeyboardColor.POSITIVE)
    return keyboard

def create_answer_keyboard():
    """Клавиатура с вариантами ответов"""
    keyboard = VkKeyboard(one_time=False)
    
    keyboard.add_button("1 - Совсем не про меня", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("2 - Иногда бывает", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("3 - Часто бывает", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("4 - Это точно про меня", color=VkKeyboardColor.SECONDARY)
    
    return keyboard

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

def find_test_by_trigger(text):
    """Находит тест по триггеру"""
    text = text.lower().strip()
    
    for test_id, triggers in TEST_TRIGGERS.items():
        for trigger in triggers:
            if text == trigger or text.startswith(trigger):
                return test_id
    
    return None

def process_message(event):
    """Обработка входящего сообщения"""
    try:
        user_id = event.user_id
        text = event.text.lower().strip()
        
        logger.info(f"Получено сообщение от {user_id}: {text}")
        
        # Проверяем подписку ПЕРВЫМ ДЕЛОМ
        is_subscribed = check_subscription(user_id)
        
        # Если не подписан
        if not is_subscribed:
            if text == "✅ проверить подписку":
                if check_subscription(user_id):
                    send_message(
                        user_id,
                        "✅ Отлично! Вы подписаны!\n\n"
                        "Теперь вы можете пройти тест.\n"
                        "Напишите «Тест» чтобы начать.",
                        create_start_keyboard()
                    )
                else:
                    send_message(
                        user_id,
                        "❌ Вы ещё не подписались на группу.\n\n"
                        "Пожалуйста, подпишитесь и нажмите «Проверить подписку» снова.",
                        create_subscription_keyboard()
                    )
            else:
                subscription_text = (
                    "👋 Здравствуйте!\n\n"
                    "Для прохождения теста необходимо подписаться на нашу группу.\n\n"
                    "1️⃣ Нажмите «Подписаться на группу»\n"
                    "2️⃣ Подпишитесь\n"
                    "3️⃣ Вернитесь и нажмите «Проверить подписку»"
                )
                
                send_message(user_id, subscription_text, create_subscription_keyboard())
            
            return
        
        # Если подписан, проверяем триггеры тестов
        test_id = find_test_by_trigger(text)
        
        if test_id:
            # Запускаем тест
            user_states[user_id] = {
                "state": "waiting_start",
                "test_id": test_id
            }
            
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
        
        elif text == "🚀 начать тест":
            user_states[user_id] = {
                "state": "taking_test",
                "current_question": 0,
                "answers": []
            }
            show_question(user_id)
        
        elif text == "🔄 пройти тест снова":
            user_states[user_id] = {
                "state": "taking_test",
                "current_question": 0,
                "answers": []
            }
            show_question(user_id)
        
        elif user_id in user_states and user_states[user_id].get("state") == "taking_test":
            process_answer(user_id, text)
        
        elif text in ["/admin", "админ", "статистика"] and user_id in ADMIN_IDS:
            show_stats(user_id)
        
        elif text in ["/help", "помощь", "help"]:
            help_text = (
                "🤖 Доступные команды:\n\n"
                "• Тест - начать тест на эмоциональное реагирование\n"
                "• Помощь - показать справку\n"
                "• Статистика - статистика (для админов)"
            )
            send_message(user_id, help_text)
        
        else:
            # Неизвестная команда
            send_message(
                user_id,
                "Напишите «Тест» чтобы начать тест на эмоциональное реагирование."
            )
            
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")

def show_question(user_id):
    """Показ вопроса"""
    try:
        if user_id not in user_states:
            user_states[user_id] = {
                "state": "taking_test",
                "current_question": 0,
                "answers": []
            }
        
        user_data = user_states[user_id]
        current = user_data.get("current_question", 0)
        
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
            
            send_message(user_id, text, create_answer_keyboard())
        else:
            finish_test(user_id)
            
    except Exception as e:
        logger.error(f"Ошибка показа вопроса: {e}")
        send_message(user_id, "Произошла ошибка. Напишите «Тест» для перезапуска.")

def process_answer(user_id, text):
    """Обработка ответа"""
    try:
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
        
        if user_id not in user_states:
            user_states[user_id] = {
                "state": "taking_test",
                "current_question": 0,
                "answers": []
            }
        
        user_data = user_states[user_id]
        
        if "answers" not in user_data:
            user_data["answers"] = []
        if "current_question" not in user_data:
            user_data["current_question"] = 0
        
        user_data["answers"].append(answer)
        user_data["current_question"] += 1
        
        show_question(user_id)
        
    except Exception as e:
        logger.error(f"Ошибка обработки ответа: {e}")
        send_message(user_id, "Произошла ошибка. Напишите «Тест» для перезапуска.")

def finish_test(user_id):
    """Завершение теста"""
    try:
        user_data = user_states.get(user_id, {})
        answers = user_data.get("answers", [])
        
        if len(answers) == len(QUESTIONS):
            results = calculate_results(answers)
            message = format_result_message(results)
            send_message(user_id, message)
            
            # Сохраняем статистику
            user_info = vk.users.get(user_ids=user_id)
            if user_info:
                username = f"{user_info[0]['first_name']} {user_info[0]['last_name']}"
            else:
                username = f"Пользователь {user_id}"
            
            update_stats(user_id, username, results["dominant_type"], results["scores"])
            
            keyboard = VkKeyboard(one_time=False)
            keyboard.add_button("🔄 Пройти тест снова", color=VkKeyboardColor.POSITIVE)
            
            send_message(user_id, "Хотите пройти тест ещё раз?", keyboard)
        
        user_states[user_id] = {"state": "idle"}
        
    except Exception as e:
        logger.error(f"Ошибка завершения теста: {e}")

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

def update_stats(user_id, username, dominant_type, scores):
    """Обновление статистики"""
    try:
        stats = load_stats()
        
        stats["total_tests"] += 1
        
        if "scale_stats" not in stats:
            stats["scale_stats"] = {}
        
        if str(dominant_type) not in stats["scale_stats"]:
            stats["scale_stats"][str(dominant_type)] = 0
        
        stats["scale_stats"][str(dominant_type)] += 1
        
        if "users" not in stats:
            stats["users"] = []
        
        stats["users"].append({
            "id": user_id,
            "username": username,
            "dominant_type": dominant_type,
            "date": datetime.now().isoformat()
        })
        
        save_stats(stats)
        
    except Exception as e:
        logger.error(f"Ошибка обновления статистики: {e}")

def load_stats():
    """Загрузка статистики"""
    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": [], "total_tests": 0, "scale_stats": {}}

def save_stats(stats):
    """Сохранение статистики"""
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения статистики: {e}")

def show_stats(user_id):
    """Показ статистики"""
    try:
        stats = load_stats()
        
        text = f"📊 Статистика:\n\n"
        text += f"Всего тестов: {stats.get('total_tests', 0)}\n"
        text += f"Всего пользователей: {len(stats.get('users', []))}\n"
        
        if 'scale_stats' in stats and stats['scale_stats']:
            text += "\nРаспределение по типам:\n"
            for scale_id, count in stats['scale_stats'].items():
                if count > 0:
                    scale_name = SCALES.get(int(scale_id), {}).get('name', f'Тип {scale_id}')
                    text += f"• {scale_name}: {count}\n"
        
        send_message(user_id, text)
        
    except Exception as e:
        logger.error(f"Ошибка показа статистики: {e}")
        send_message(user_id, "Ошибка загрузки статистики")

def run_longpoll():
    """Запуск Long Poll в отдельном потоке"""
    logger.info("VK бот запущен")
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                try:
                    process_message(event)
                except Exception as e:
                    logger.error(f"Ошибка обработки сообщения: {e}")
    except Exception as e:
        logger.error(f"Ошибка Long Poll: {e}")

async def handle_health(request):
    """HTTP для Render"""
    return web.Response(text="Bot is running")

async def main():
    """Запуск HTTP сервера и бота"""
    longpoll_thread = threading.Thread(target=run_longpoll, daemon=True)
    longpoll_thread.start()
    
    app = web.Application()
    app.router.add_get('/', handle_health)
    app.router.add_get('/health', handle_health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logger.info(f"HTTP сервер запущен на порту {PORT}")
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
