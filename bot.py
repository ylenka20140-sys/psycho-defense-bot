import os
import json
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from aiohttp import web
from vkbottle import Bot, Keyboard, KeyboardButtonColor, Text
from vkbottle.bot import Message
from vkbottle import BaseStateGroup

# ===== НАСТРОЙКИ =====
VK_TOKEN = "vk1.a.a_3dITwtsV9pQscXoUm1fgSpAtJDYBCaFkPZ30GRn4KqdpreBbX_9TP_e5oKJ7Kq5VSu_b1wKtNjcadpGDpN8AOxuipt34XEIvsW8KohkWGBO2Xtp7X5EK2H4e4ScGGWnRAWOx0726cjUYPWwtVX-wK_39mIA_nM0SCyvKhr6KgNbGZeqnTDp4ru_hSXj9jTeHkpBG1xPcYkNoanCMfY-g"
GROUP_ID = 240718452  # ID вашей группы
ADMIN_IDS = [111655732]  # ID администраторов (можно несколько)
VK_COMMUNITY_URL = "https://vk.com/club240718452"
STATS_FILE = "stats.json"
PORT = int(os.environ.get("PORT", 10000))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=VK_TOKEN, group_id=GROUP_ID)

# Определение состояний
class TestStates(BaseStateGroup):
    TAKING_TEST = "taking_test"
    WAITING_START = "waiting_start"

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
        "description": "Вместо того чтобы чувствовать, человек начинает бесконечно анализировать. «Почему я так отреагировал?», «Что это говорит о моём детстве?»",
        "price": "Истощение мозга, бессонница, жизнь «в голове», потеря контакта с телом и реальностью.",
        "motto": "«Если я всё пойму, мне станет легче».",
        "advice": "Переключаться с мыслей на тело. Спросить себя: «Где я это чувствую физически?» Ограничивать время на обдумывание (например, 15 минут в день)."
    },
    4: {
        "name": "Убегающий",
        "term": "Избегание / Эскапизм",
        "description": "Любой способ уйти от реальности: сериалы, игры, сон, фантазии, соцсети.",
        "price": "Проблемы копятся, жизнь проходит мимо, чувство «я не живу, а существую».",
        "motto": "«Если я не вижу проблему — её не существует».",
        "advice": "Начать с малого: 10 минут в день оставаться наедине с собой без отвлечений. Записывать, от чего именно вы убегаете."
    },
    5: {
        "name": "Заглушающий",
        "term": "Химический / Пищевой копинг",
        "description": "Тело используется как контейнер для эмоций. Еда, алкоголь, никотин, вещества — всё, что даёт быстрый физический эффект.",
        "price": "Зависимость, разрушение здоровья, стыд, чувство потери контроля.",
        "motto": "«Если я изменю химию тела, я перестану чувствовать».",
        "advice": "Вести дневник: записывать, какая эмоция предшествовала импульсу. Искать замену: прогулка, душ, звонок другу. Не стесняться просить поддержки."
    },
    6: {
        "name": "Контролёр",
        "term": "Гиперконтроль / Перфекционизм",
        "description": "Попытка устранить тревогу через тотальный контроль: всё должно быть идеально, по плану, предсказуемо.",
        "price": "Истощение, выгорание, раздражение на людей, которые «не соответствуют», одиночество.",
        "motto": "«Если я всё контролирую, со мной не случится ничего плохого».",
        "advice": "Тренироваться отпускать: начать с мелочей, которые не критичны. Позволять другим делать ошибки. Помнить: неопределённость — часть жизни."
    },
    7: {
        "name": "Самонаказывающий",
        "term": "Аутоагрессия",
        "description": "Вся агрессия направляется не на обидчика, а на себя: критика, обвинения, самоуничижение.",
        "price": "Депрессия, хроническое чувство вины, низкая самооценка, психосоматика.",
        "motto": "«Лучше я сам себя накажу, чем признаю, что мир несправедлив».",
        "advice": "Начать с простого: говорить с собой так, как говорили бы с другом. Отслеживать самообвинения и переформулировать их в нейтральные фразы."
    }
}

# Функции для работы со статистикой
def load_stats():
    """Загрузка статистики из файла"""
    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": [], "total_tests": 0, "scale_stats": {str(i): 0 for i in range(1, 8)}}

def save_stats(stats):
    """Сохранение статистики в файл"""
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def update_stats(user_id: int, username: str, dominant_type: int, secondary_type: Optional[int], scores: Dict[int, int]):
    """Обновление статистики"""
    stats = load_stats()
    
    # Обновление общей статистики
    stats["total_tests"] += 1
    stats["scale_stats"][str(dominant_type)] = stats["scale_stats"].get(str(dominant_type), 0) + 1
    
    # Добавление информации о пользователе
    user_found = False
    for user in stats["users"]:
        if user["id"] == user_id:
            user["tests_completed"] += 1
            user["last_test_date"] = datetime.now().isoformat()
            user["dominant_types"].append(dominant_type)
            user["last_scores"] = scores
            user_found = True
            break
    
    if not user_found:
        stats["users"].append({
            "id": user_id,
            "username": username,
            "tests_completed": 1,
            "first_test_date": datetime.now().isoformat(),
            "last_test_date": datetime.now().isoformat(),
            "dominant_types": [dominant_type],
            "last_scores": scores
        })
    
    save_stats(stats)

# Функция для подсчета результатов
def calculate_results(answers: List[int]) -> Dict:
    """
    Подсчет результатов теста
    
    Args:
        answers: список ответов (1-4) для каждого из 24 вопросов
    
    Returns:
        Словарь с результатами
    """
    # Инициализация баллов по шкалам
    scale_scores = {i: 0 for i in range(1, 8)}
    
    # Подсчет баллов
    for i, answer in enumerate(answers):
        question = QUESTIONS[i]
        for scale in question["scales"]:
            scale_scores[scale] += answer
    
    # Находим доминирующий тип
    dominant_type = max(scale_scores, key=scale_scores.get)
    dominant_score = scale_scores[dominant_type]
    
    # Находим дополнительный тип (второй по величине)
    sorted_scales = sorted(scale_scores.items(), key=lambda x: x[1], reverse=True)
    secondary_type = None
    secondary_score = 0
    
    if len(sorted_scales) > 1:
        second_scale, second_score = sorted_scales[1]
        # Проверяем порог 70%
        if second_score >= dominant_score * 0.7:
            secondary_type = second_scale
            secondary_score = second_score
    
    return {
        "scores": scale_scores,
        "dominant_type": dominant_type,
        "dominant_score": dominant_score,
        "secondary_type": secondary_type,
        "secondary_score": secondary_score if secondary_type else 0
    }

# Функция для формирования текста результата
def format_result_message(results: Dict) -> str:
    """Формирование сообщения с результатами"""
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

📈 Балл по доминирующему типу: {results['dominant_score']}
"""
    
    if results["secondary_type"]:
        secondary = SCALES[results["secondary_type"]]
        message += f"""
🔹 Дополнительный тип: {secondary['name']}
📊 Термин: {secondary['term']}
Балл: {results['secondary_score']}

Кратко: {secondary['description']}
"""
    
    message += f"""
💡 Важное пояснение:
Большинство людей используют 2–3 стиля одновременно. Тревожный сигнал — когда один стиль становится единственным.

💬 Хотите получить персональные рекомендации?
Как справляться именно с вашим типом защиты — напишите нам в сообщество:

👉 {VK_COMMUNITY_URL}
"""
    
    return message

# Функция для создания клавиатуры с ответами
def create_answer_keyboard():
    """Создание клавиатуры с вариантами ответов"""
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("1 - Совсем не про меня"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("2 - Иногда бывает"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("3 - Часто бывает"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("4 - Это точно про меня"), color=KeyboardButtonColor.SECONDARY)
    return keyboard

# Функция для создания клавиатуры старта
def create_start_keyboard():
    """Создание клавиатуры для начала теста"""
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("🚀 Начать тест"), color=KeyboardButtonColor.POSITIVE)
    return keyboard

# Обработчик команды "Начать" или "Старт"
@bot.on.private_message(text=["начать", "старт", "start", "/start", "привет"])
async def start_handler(message: Message):
    """Обработчик команды старт"""
    users_info = await bot.api.users.get(message.from_id)
    user_name = users_info[0].first_name if users_info else "друг"
    
    welcome_text = f"""
👋 Здравствуйте, {user_name}!

Это тест «Ваше эмоциональное реагирование»
Тест на определение индивидуального стиля совладания с эмоциями

Он поможет вам узнать ваш индивидуальный стиль эмоционального реагирования: как вы привыкли обращаться со злостью, тревогой, грустью и виной.

⚠️ Важно: нет правильных и неправильных ответов. Будьте честны с собой.

📝 Тест состоит из 24 вопросов и займёт около 5–7 минут.

В конце вы получите развёрнутое описание вашего доминирующего типа реагирования.

Нажмите кнопку ниже, чтобы начать тест.
    """
    
    await message.answer(welcome_text, keyboard=create_start_keyboard())
    await bot.state_dispenser.set(message.from_id, TestStates.WAITING_START)

# Обработчик нажатия "Начать тест"
@bot.on.private_message(text="🚀 Начать тест")
async def start_test_handler(message: Message):
    """Начало теста"""
    await bot.state_dispenser.set(
        message.from_id, 
        TestStates.TAKING_TEST,
        current_question=0,
        answers=[]
    )
    await show_question(message)

# Функция для показа вопроса
async def show_question(message: Message):
    """Показ текущего вопроса"""
    ctx = await bot.state_dispenser.get(message.from_id)
    current_question = ctx.get("current_question", 0)
    
    if current_question < len(QUESTIONS):
        question = QUESTIONS[current_question]
        
        # Формируем текст вопроса
        block_names = {
            "A": "Реакция на злость и конфликт",
            "B": "Реакция на тревогу и страх",
            "C": "Реакция на грусть, вину и неудачи"
        }
        
        question_text = f"""
📋 Вопрос {current_question + 1} из {len(QUESTIONS)}

📌 {block_names[question['block']]}

{question['text']}
        """
        
        await message.answer(question_text, keyboard=create_answer_keyboard())
    else:
        # Тест завершен
        await finish_test(message)

# Обработчик ответов на вопросы
@bot.on.private_message(state=TestStates.TAKING_TEST)
async def process_answer(message: Message):
    """Обработка ответа на вопрос"""
    text = message.text
    
    # Определяем номер ответа
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
        await message.answer("Пожалуйста, выберите один из вариантов ответа (1-4)")
        return
    
    ctx = await bot.state_dispenser.get(message.from_id)
    answers = ctx.get("answers", [])
    current_question = ctx.get("current_question", 0)
    
    # Добавляем ответ
    answers.append(answer)
    current_question += 1
    
    # Обновляем состояние
    await bot.state_dispenser.set(
        message.from_id, 
        TestStates.TAKING_TEST,
        current_question=current_question,
        answers=answers
    )
    
    # Показываем следующий вопрос
    await show_question(message)

# Функция для завершения теста
async def finish_test(message: Message):
    """Завершение теста и показ результатов"""
    ctx = await bot.state_dispenser.get(message.from_id)
    answers = ctx.get("answers", [])
    
    if len(answers) != len(QUESTIONS):
        await message.answer("Произошла ошибка. Пожалуйста, начните тест заново.")
        await bot.state_dispenser.delete(message.from_id)
        return
    
    # Подсчет результатов
    results = calculate_results(answers)
    
    # Получаем информацию о пользователе
    user_info = await bot.api.users.get(message.from_id)
    if user_info:
        username = f"{user_info[0].first_name} {user_info[0].last_name}"
    else:
        username = f"Пользователь {message.from_id}"
    
    # Обновляем статистику
    update_stats(
        user_id=message.from_id,
        username=username,
        dominant_type=results["dominant_type"],
        secondary_type=results["secondary_type"],
        scores=results["scores"]
    )
    
    # Формируем сообщение с результатами
    result_message = format_result_message(results)
    
    await message.answer(result_message)
    
    # Добавляем кнопку для повторного прохождения
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("🔄 Пройти тест снова"), color=KeyboardButtonColor.POSITIVE)
    
    await message.answer("Если хотите пройти тест ещё раз, нажмите кнопку ниже:", keyboard=keyboard)
    
    await bot.state_dispenser.delete(message.from_id)

# Обработчик команды "Пройти тест снова"
@bot.on.private_message(text="🔄 Пройти тест снова")
async def restart_test_handler(message: Message):
    """Перезапуск теста"""
    await start_test_handler(message)

# Обработчик команды администратора
@bot.on.private_message(text=["/admin", "админ", "статистика"])
async def admin_handler(message: Message):
    """Админ-панель для просмотра статистики"""
    if message.from_id not in ADMIN_IDS:
        await message.answer("У вас нет доступа к админ-панели.")
        return
    
    stats = load_stats()
    
    admin_text = f"""
📊 Статистика теста

Общая информация:
• Всего пройдено тестов: {stats['total_tests']}
• Всего пользователей: {len(stats['users'])}

Распределение по типам:
"""
    
    # Статистика по типам
    for scale_id, scale_data in SCALES.items():
        count = stats['scale_stats'].get(str(scale_id), 0)
        percentage = (count / stats['total_tests'] * 100) if stats['total_tests'] > 0 else 0
        admin_text += f"• {scale_data['name']}: {count} ({percentage:.1f}%)\n"
    
    # Последние пользователи
    if stats['users']:
        admin_text += "\nПоследние пользователи:\n"
        for user in stats['users'][-10:]:  # Последние 10 пользователей
            admin_text += f"• {user['username']}: {user['tests_completed']} тест(ов)\n"
    
    await message.answer(admin_text)

# Обработчик команды помощи
@bot.on.private_message(text=["/help", "помощь", "help"])
async def help_handler(message: Message):
    """Справка по командам"""
    help_text = """
🤖 Доступные команды:

• Начать / start / привет - Начать тест
• Помощь / help - Показать справку
• Статистика / admin - Статистика (только для админов)

📝 О тесте:
Тест «Ваше эмоциональное реагирование» поможет определить ваш индивидуальный стиль совладания с эмоциями.

⏱ Время прохождения: 5-7 минут
📋 Количество вопросов: 24

💬 Обратная связь:
Если у вас есть вопросы или предложения, напишите нам в сообщество ВКонтакте.
    """
    
    await message.answer(help_text)

# Обработчик для неизвестных сообщений
@bot.on.private_message()
async def handle_unknown(message: Message):
    """Обработка неизвестных сообщений"""
    await message.answer(
        "Используйте команду «Начать» для начала теста или «Помощь» для получения справки.",
        keyboard=create_start_keyboard()
    )

# ===== HTTP СЕРВЕР ДЛЯ RENDER =====
async def handle_health(request):
    """Обработчик для проверки работоспособности"""
    return web.Response(text="Bot is running")

async def main():
    """Запуск HTTP сервера и бота"""
    # Создаем HTTP сервер
    app = web.Application()
    app.router.add_get('/', handle_health)
    app.router.add_get('/health', handle_health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logger.info(f"HTTP сервер запущен на порту {PORT}")
    logger.info("VK бот запущен")
    
    # Запускаем бота
    await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
