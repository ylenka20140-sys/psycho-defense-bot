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

# ===== ВСЕ ТЕСТЫ =====
TESTS = {
    "emotional": {
        "name": "Ваше эмоциональное реагирование",
        "description": "Тест на определение индивидуального стиля совладания с эмоциями",
        "triggers": ["тест", "эмоции", "эмоциональное реагирование"],
        "answer_scale": 4,
        "questions": [
            {"id": 1, "text": "Когда я злюсь, я говорю «всё нормально», хотя внутри всё кипит", "scales": [1]},
            {"id": 2, "text": "Я скорее промолчу, чем вступлю в конфликт, даже если меня обидели", "scales": [1]},
            {"id": 3, "text": "Если на меня накричали, я потом срываюсь на том, кто слабее", "scales": [2]},
            {"id": 4, "text": "Я могу кричать, бить посуду или хлопать дверью, когда меня довели", "scales": [2]},
            {"id": 5, "text": "Я долго ношу обиду в себе и прокручиваю в голове, что надо было ответить", "scales": [3]},
            {"id": 6, "text": "После ссоры я не могу уснуть, потому что мысленно продолжаю спор", "scales": [3]},
            {"id": 7, "text": "Я убеждён, что злиться — это плохо и стыдно", "scales": [1]},
            {"id": 8, "text": "Я стараюсь вообще не попадать в ситуации, где возможен конфликт", "scales": [4]},
            {"id": 9, "text": "Когда я тревожусь, я начинаю есть, даже если не голоден", "scales": [5]},
            {"id": 10, "text": "От тревоги у меня пропадает аппетит", "scales": [5]},
            {"id": 11, "text": "Чтобы успокоиться, мне нужно выпить, покурить или принять что-то", "scales": [5]},
            {"id": 12, "text": "Я загружаю себя делами, чтобы не чувствовать тревогу", "scales": [6]},
            {"id": 13, "text": "Я часами сижу в телефоне/сериалах/играх, чтобы убежать от неприятных мыслей", "scales": [4]},
            {"id": 14, "text": "Я фантазирую о другой жизни, где у меня всё хорошо", "scales": [4]},
            {"id": 15, "text": "Я постоянно проверяю и перепроверяю всё, чтобы не случилось ничего плохого", "scales": [6]},
            {"id": 16, "text": "Мне нужно, чтобы всё было предсказуемо, иначе я не могу расслабиться", "scales": [6]},
            {"id": 17, "text": "Когда что-то идёт не так, я виню в этом только себя", "scales": [7]},
            {"id": 18, "text": "Я называю себя глупым/никчёмным, когда ошибаюсь", "scales": [7]},
            {"id": 19, "text": "Я говорю себе «да ерунда, не стоит расстраиваться», чтобы не плакать", "scales": [1]},
            {"id": 20, "text": "Я обесцениваю свои проблемы: «кому-то хуже, чем мне»", "scales": [1]},
            {"id": 21, "text": "Я ухожу в работу с головой, чтобы не чувствовать боль/грусть", "scales": [6]},
            {"id": 22, "text": "Я могу сутками лежать и ничего не делать, когда мне плохо", "scales": [4]},
            {"id": 23, "text": "Я заедаю грусть или наоборот — не могу есть совсем", "scales": [5]},
            {"id": 24, "text": "Мне сложно просить помощи, я должен справляться сам", "scales": [6]},
        ],
        "scales": {
            1: {"name": "Подавитель", "term": "Вытеснение (репрессия)", "description": "«Я не чувствую» / «Я справлюсь сам». Эмоции замораживаются.", "price": "Психосоматика, эмоциональная глухота.", "motto": "«Если я не признаю чувство — его нет».", "advice": "Учиться замечать телесные сигналы и называть эмоции."},
            2: {"name": "Взрыватель", "term": "Отреагирование / Замещение", "description": "Эмоция мгновенно выплёскивается.", "price": "Разрушенные отношения.", "motto": "«Лучше выпустить пар».", "advice": "Отслеживать гнев и делать паузу."},
            3: {"name": "Мыслитель", "term": "Руминация", "description": "Вместо чувств — анализ.", "price": "Истощение, бессонница.", "motto": "«Если я пойму — станет легче».", "advice": "Переключаться на тело."},
            4: {"name": "Убегающий", "term": "Избегание", "description": "Уход от реальности.", "price": "Проблемы копятся.", "motto": "«Не вижу проблему — её нет».", "advice": "10 минут наедине с собой."},
            5: {"name": "Заглушающий", "term": "Химический копинг", "description": "Тело как контейнер для эмоций.", "price": "Зависимость.", "motto": "«Изменю химию тела».", "advice": "Вести дневник эмоций."},
            6: {"name": "Контролёр", "term": "Гиперконтроль", "description": "Тотальный контроль.", "price": "Выгорание.", "motto": "«Всё контролирую».", "advice": "Отпускать мелочи."},
            7: {"name": "Самонаказывающий", "term": "Аутоагрессия", "description": "Агрессия на себя.", "price": "Депрессия.", "motto": "«Накажу себя сам».", "advice": "Говорить с собой как с другом."}
        }
    },
    "defense": {
        "name": "Диагностика психологических защит",
        "description": "Определение ведущих защитных механизмов личности",
        "triggers": ["защита", "защиты", "психологические защиты"],
        "answer_scale": 5,
        "questions": [
            {"id": 1, "text": "Когда задача кажется слишком сложной, я просто её не делаю", "scales": [1]},
            {"id": 2, "text": "Если что-то расстраивает, я этого избегаю", "scales": [1]},
            {"id": 3, "text": "Когда настроение плохое, я отдаляюсь от людей и бросаю дела", "scales": [1]},
            {"id": 4, "text": "Когда тревожно, мне нужно, чтобы кто-то поддержал", "scales": [2]},
            {"id": 5, "text": "Я постоянно всё перепроверяю", "scales": [2]},
            {"id": 6, "text": "У меня есть свои ритуалы, которые снимают страх", "scales": [2]},
            {"id": 7, "text": "Я поступаю импульсивно, как велит настроение", "scales": [3]},
            {"id": 8, "text": "Когда я расстраиваюсь, я теряю самоконтроль", "scales": [3]},
            {"id": 9, "text": "Я делаю что-то на эмоциях, даже если потом пожалею", "scales": [3]},
            {"id": 10, "text": "Мне невыносимо грустить или огорчаться", "scales": [4]},
            {"id": 11, "text": "Я не выношу физические ощущения стресса", "scales": [4]},
            {"id": 12, "text": "Физические симптомы стресса пугают меня", "scales": [4]},
            {"id": 13, "text": "Я стараюсь не замечать свои эмоции, когда грустно", "scales": [5]},
            {"id": 14, "text": "Я обычно отгоняю неприятные чувства", "scales": [5]},
            {"id": 15, "text": "Когда мне плохо, я заставляю себя перестать это чувствовать", "scales": [5]},
            {"id": 16, "text": "Когда приходят грустные мысли, я пытаюсь от них избавиться", "scales": [6]},
            {"id": 17, "text": "Я отгоняю тяжёлые воспоминания", "scales": [6]},
            {"id": 18, "text": "Мне нужно блокировать болезненные мысли", "scales": [6]},
            {"id": 19, "text": "В стрессе я мыслю крайностями", "scales": [7]},
            {"id": 20, "text": "В сложной ситуации я тороплюсь с выводами", "scales": [7]},
            {"id": 21, "text": "Я уверен(а), что знаю, о чём думают другие", "scales": [7]},
            {"id": 22, "text": "Если что-то идёт не так, я виню себя", "scales": [8]},
            {"id": 23, "text": "Я критикую себя за свои ошибки", "scales": [8]},
            {"id": 24, "text": "Я виню себя, даже когда не виноват(а)", "scales": [8]},
            {"id": 25, "text": "Я осуждаю других за их поведение", "scales": [9]},
            {"id": 26, "text": "Я критикую других за их ошибки", "scales": [9]},
            {"id": 27, "text": "Если что-то не выходит, виноваты окружающие", "scales": [9]},
            {"id": 28, "text": "Я прокручиваю в голове всё плохое из будущего", "scales": [10]},
            {"id": 29, "text": "Я зацикливаюсь на самом страшном сценарии", "scales": [10]},
            {"id": 30, "text": "Я предполагаю худшее и преувеличиваю", "scales": [10]},
            {"id": 31, "text": "Я зацикливаюсь на неприятных событиях прошлого", "scales": [11]},
            {"id": 32, "text": "Я постоянно прокручиваю неприятные события", "scales": [11]},
            {"id": 33, "text": "Я подолгу анализирую события прошлого", "scales": [11]},
        ],
        "scales": {
            1: {"name": "Избегание", "term": "Уход от проблем", "description": "Психика защищается через уход.", "price": "Проблемы накапливаются.", "motto": "«Подумаю завтра».", "advice": "Правило 5 минут."},
            2: {"name": "Ритуализация", "term": "Поиск опоры", "description": "Опора в повторениях.", "price": "Отнимает силы.", "motto": "«Проверю 3 раза».", "advice": "Сделай ритуал короче."},
            3: {"name": "Эмоциональная реактивность", "term": "Импульсивность", "description": "Эмоции берут верх.", "price": "Разрушенные отношения.", "motto": "«Чувствую — действую».", "advice": "5 глубоких вдохов."},
            4: {"name": "Интолерантность к стрессу", "term": "Непереносимость дискомфорта", "description": "Напряжение невыносимо.", "price": "Ограничение жизни.", "motto": "«Лишь бы прекратилось».", "advice": "Внимание в стопы."},
            5: {"name": "Подавление эмоций", "term": "Замораживание", "description": "Чувства выключаются.", "price": "Психосоматика.", "motto": "«Я не чувствую».", "advice": "Пиши о чувствах."},
            6: {"name": "Избегание мыслей", "term": "Блокировка", "description": "Не думать о боли.", "price": "Мысли сильнее.", "motto": "«Не буду думать».", "advice": "Мысль на облаке."},
            7: {"name": "Когнитивные искажения", "term": "Крайности", "description": "Мышление крайностями.", "price": "Искажение реальности.", "motto": "«Всё или ничего».", "advice": "3 объяснения."},
            8: {"name": "Самообвинение", "term": "Аутоагрессия", "description": "Вина во всём.", "price": "Депрессия.", "motto": "«Это из-за меня».", "advice": "Раздели ответственность."},
            9: {"name": "Экстернализация", "term": "Проекция", "description": "Причины в других.", "price": "Позиция жертвы.", "motto": "«Они виноваты».", "advice": "Что я могу сделать?"},
            10: {"name": "Катастрофизация", "term": "Преувеличение", "description": "Страшные сценарии.", "price": "Тревога.", "motto": "«А что если...»", "advice": "15 минут тревоги."},
            11: {"name": "Руминация", "term": "Пережёвывание", "description": "Прокручивание прошлого.", "price": "Силы уходят.", "motto": "«Почему так?»", "advice": "Что теперь?"}
        }
    },
    "thinking": {
        "name": "Диагностика когнитивных искажений",
        "description": "Определение «ловушек» мышления",
        "triggers": ["мышление", "искажения", "когнитивные искажения"],
        "answer_scale": 5,
        "questions": [
            {"id": 1, "text": "Я часто мыслю крайностями: «или идеально, или никак»", "scales": [1]},
            {"id": 2, "text": "Любая моя ошибка кажется мне тотальным провалом", "scales": [1]},
            {"id": 3, "text": "В людях я вижу либо только хорошее, либо только плохое", "scales": [1]},
            {"id": 4, "text": "Я часто прокручиваю в голове худшие сценарии", "scales": [2]},
            {"id": 5, "text": "Я сильно преувеличиваю масштаб проблем", "scales": [2]},
            {"id": 6, "text": "Мне кажется, что если что-то пойдёт не так, это будет катастрофа", "scales": [2]},
            {"id": 7, "text": "Я часто думаю, что знаю, о чём думают другие", "scales": [3]},
            {"id": 8, "text": "Я уверен(а), что окружающие осуждают меня", "scales": [3]},
            {"id": 9, "text": "Я предполагаю, что другие плохого мнения обо мне", "scales": [3]},
            {"id": 10, "text": "Из одной неудачи я делаю вывод, что ничего не получается", "scales": [4]},
            {"id": 11, "text": "Если что-то не так в одном месте, так будет везде", "scales": [4]},
            {"id": 12, "text": "Я делаю глобальные выводы из единичных случаев", "scales": [4]},
            {"id": 13, "text": "У меня много жёстких правил о том, как должны поступать другие", "scales": [5]},
            {"id": 14, "text": "Я часто говорю «я должен» и чувствую вину", "scales": [5]},
            {"id": 15, "text": "Когда люди не соответствуют ожиданиям, я раздражаюсь", "scales": [5]},
            {"id": 16, "text": "Я не замечаю свои успехи — обесцениваю их", "scales": [6]},
            {"id": 17, "text": "Хорошие события кажутся мне случайными", "scales": [6]},
            {"id": 18, "text": "Я концентрируюсь на негативе", "scales": [6]},
            {"id": 19, "text": "Я считаю, что мои чувства всегда отражают реальность", "scales": [7]},
            {"id": 20, "text": "Если я боюсь, значит есть опасность", "scales": [7]},
            {"id": 21, "text": "Если я чувствую вину, значит виновата", "scales": [7]},
            {"id": 22, "text": "Я беру на себя ответственность за настроение других", "scales": [8]},
            {"id": 23, "text": "Мне кажется, люди расстраиваются из-за меня", "scales": [8]},
            {"id": 24, "text": "Я чувствую ответственность за всё вокруг", "scales": [8]},
            {"id": 25, "text": "Я называю себя негативными словами", "scales": [9]},
            {"id": 26, "text": "Я навешиваю ярлыки на других", "scales": [9]},
            {"id": 27, "text": "Я определяю человека одним поступком", "scales": [9]},
        ],
        "scales": {
            1: {"name": "Черно-белое мышление", "term": "Крайности", "description": "Мир в крайностях.", "price": "Ошибка = провал.", "motto": "«Всё или ничего».", "advice": "Найди средний вариант."},
            2: {"name": "Катастрофизация", "term": "Преувеличение", "description": "Преувеличение масштаба.", "price": "Тревога.", "motto": "«А что если...»", "advice": "Что самое страшное?"},
            3: {"name": "Чтение мыслей", "term": "Домысливание", "description": "Знаю мысли других.", "price": "Обиды.", "motto": "«Я знаю...»", "advice": "Спроси прямо."},
            4: {"name": "Чрезмерное обобщение", "term": "Глобализация", "description": "Из одного — всё.", "price": "Низкая самооценка.", "motto": "«Никогда...»", "advice": "Найди исключение."},
            5: {"name": "Долженствование", "term": "Жёсткие правила", "description": "Всё должно быть так.", "price": "Злость.", "motto": "«Должны...»", "advice": "«Предпочитаю» вместо «должен»."},
            6: {"name": "Обесценивание позитива", "term": "Фильтрация", "description": "Не замечаю хорошее.", "price": "Потеря радости.", "motto": "«Это случайно».", "advice": "3 хорошие вещи в день."},
            7: {"name": "Эмоциональное обоснование", "term": "Чувства = реальность", "description": "Чувства как факты.", "price": "Тревога управляет.", "motto": "«Боюсь = опасно».", "advice": "Раздели чувства и факты."},
            8: {"name": "Персонализация", "term": "Всё из-за меня", "description": "Ответственность за всё.", "price": "Вина.", "motto": "«Я виноват(а)».", "advice": "Это про меня?"},
            9: {"name": "Навешивание ярлыков", "term": "Стереотипизация", "description": "Одно слово = человек.", "price": "Нет изменений.", "motto": "«Я дура».", "advice": "Ярлык → описание."}
        }
    },
}

# ===== ФУНКЦИИ =====

def find_test_by_trigger(text):
    """Находит тест по триггеру"""
    text = text.lower().strip()
    for test_id, test_data in TESTS.items():
        for trigger in test_data["triggers"]:
            if text == trigger or text.startswith(trigger):
                return test_id
    return None

def get_questions(test_id):
    """Получает вопросы теста"""
    return TESTS[test_id]["questions"]

def get_scales(test_id):
    """Получает шкалы теста"""
    return TESTS[test_id]["scales"]

def get_answer_scale(test_id):
    """Получает шкалу ответов"""
    return TESTS[test_id].get("answer_scale", 4)

def create_answer_keyboard(test_id):
    """Создает клавиатуру"""
    answer_scale = get_answer_scale(test_id)
    keyboard = VkKeyboard(one_time=False)
    
    if answer_scale == 5:
        keyboard.add_button("1 - Почти никогда", color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button("2 - Редко", color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button("3 - Иногда", color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button("4 - Часто", color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button("5 - Очень часто", color=VkKeyboardColor.SECONDARY)
    else:
        keyboard.add_button("1 - Совсем не про меня", color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button("2 - Иногда бывает", color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button("3 - Часто бывает", color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button("4 - Это точно про меня", color=VkKeyboardColor.SECONDARY)
    
    return keyboard

def check_subscription(user_id):
    """Проверка подписки"""
    try:
        if user_id in ADMIN_IDS:
            return True
        response = vk.groups.isMember(group_id=GROUP_ID, user_id=user_id)
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
    try:
        user_id = event.user_id
        text = event.text.lower().strip()
        logger.info(f"Получено сообщение от {user_id}: {text}")
        
        is_subscribed = check_subscription(user_id)
        
        if not is_subscribed:
            if text == "✅ проверить подписку":
                if check_subscription(user_id):
                    send_message(
                        user_id,
                        "✅ Отлично! Вы подписаны!\n\n"
                        "Доступные тесты:\n"
                        "• «Тест» - эмоциональное реагирование\n"
                        "• «Защита» - психологические защиты\n"
                        "• «Мышление» - когнитивные искажения\n\n"
                        "Напишите название теста."
                    )
                else:
                    send_message(user_id, "❌ Вы ещё не подписались.", create_subscription_keyboard())
            else:
                send_message(
                    user_id,
                    "👋 Здравствуйте!\n\nДля прохождения тестов необходимо подписаться на группу.",
                    create_subscription_keyboard()
                )
            return
        
        test_id = find_test_by_trigger(text)
        
        if test_id:
            test_data = TESTS[test_id]
            user_states[user_id] = {"state": "waiting_start", "test_id": test_id}
            
            welcome_text = (
                f"👋 Здравствуйте!\n\n"
                f"Это тест «{test_data['name']}»\n"
                f"{test_data['description']}\n\n"
                f"⚠️ Важно: нет правильных и неправильных ответов.\n\n"
                f"📝 Тест состоит из {len(test_data['questions'])} вопросов.\n\n"
                f"Нажмите кнопку ниже, чтобы начать тест."
            )
            send_message(user_id, welcome_text, create_start_keyboard())
        
        elif text == "🚀 начать тест":
            user_data = user_states.get(user_id, {})
            test_id = user_data.get("test_id", "emotional")
            user_states[user_id] = {
                "state": "taking_test",
                "test_id": test_id,
                "current_question": 0,
                "answers": []
            }
            show_question(user_id)
        
        elif text == "🔄 пройти тест снова":
            user_data = user_states.get(user_id, {})
            test_id = user_data.get("test_id", "emotional")
            user_states[user_id] = {
                "state": "taking_test",
                "test_id": test_id,
                "current_question": 0,
                "answers": []
            }
            show_question(user_id)
        
        elif user_id in user_states and user_states[user_id].get("state") == "taking_test":
            process_answer(user_id, text)
        
        elif text in ["/admin", "админ", "статистика"] and user_id in ADMIN_IDS:
            show_stats(user_id)
        
        elif text in ["/help", "помощь", "help"]:
            help_text = "🤖 Доступные тесты:\n\n"
            for tid, tdata in TESTS.items():
                help_text += f"• «{tdata['triggers'][0]}» - {tdata['name']}\n"
            help_text += "\nНапишите название теста для начала."
            send_message(user_id, help_text)
        
        else:
            tests_list = "Доступные тесты:\n\n"
            for tid, tdata in TESTS.items():
                tests_list += f"• «{tdata['triggers'][0]}» - {tdata['name']}\n"
            tests_list += "\nНапишите название теста для начала."
            send_message(user_id, tests_list)
            
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")

def show_question(user_id):
    """Показ вопроса"""
    try:
        user_data = user_states.get(user_id, {})
        test_id = user_data.get("test_id", "emotional")
        current = user_data.get("current_question", 0)
        questions = get_questions(test_id)
        
        if current < len(questions):
            question = questions[current]
            text = f"📋 Вопрос {current + 1} из {len(questions)}\n\n"
            text += question["text"]
            send_message(user_id, text, create_answer_keyboard(test_id))
        else:
            finish_test(user_id)
    except Exception as e:
        logger.error(f"Ошибка показа вопроса: {e}")

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
        elif text.startswith("5"):
            answer = 5
        
        if answer is None:
            send_message(user_id, "Выберите ответ от 1 до 5")
            return
        
        user_data = user_states.get(user_id, {})
        
        if "answers" not in user_data:
            user_data["answers"] = []
        if "current_question" not in user_data:
            user_data["current_question"] = 0
        
        user_data["answers"].append(answer)
        user_data["current_question"] += 1
        user_states[user_id] = user_data
        
        show_question(user_id)
    except Exception as e:
        logger.error(f"Ошибка обработки ответа: {e}")

def finish_test(user_id):
    """Завершение теста"""
    try:
        user_data = user_states.get(user_id, {})
        test_id = user_data.get("test_id", "emotional")
        answers = user_data.get("answers", [])
        questions = get_questions(test_id)
        
        if len(answers) == len(questions):
            results = calculate_results(answers, test_id)
            message = format_result_message(results, test_id)
            send_message(user_id, message)
            
            keyboard = VkKeyboard(one_time=False)
            keyboard.add_button("🔄 Пройти тест снова", color=VkKeyboardColor.POSITIVE)
            send_message(user_id, "Хотите пройти тест ещё раз?", keyboard)
        
        user_states[user_id] = {"state": "idle"}
    except Exception as e:
        logger.error(f"Ошибка завершения теста: {e}")

def calculate_results(answers, test_id):
    """Подсчет результатов"""
    scales = get_scales(test_id)
    questions = get_questions(test_id)
    scale_scores = {scale_id: 0 for scale_id in scales.keys()}
    
    for i, answer in enumerate(answers):
        if i < len(questions):
            question = questions[i]
            for scale in question["scales"]:
                if scale in scale_scores:
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

def format_result_message(results, test_id):
    """Форматирование результата"""
    scales = get_scales(test_id)
    test_data = TESTS[test_id]
    dominant = scales[results["dominant_type"]]
    
    message = f"""
🎯 Ваш результат: {test_data['name
