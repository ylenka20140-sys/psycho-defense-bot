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
VK_TOKEN = os.environ.get("VK_TOKEN", "8vk1.a.a_3dITwtsV9pQscXoUm1fgSpAtJDYBCaFkPZ30GRn4KqdpreBbX_9TP_e5oKJ7Kq5VSu_b1wKtNjcadpGDpN8AOxuipt34XEIvsW8KohkWGBO2Xtp7X5EK2H4e4ScGGWnRAWOx0726cjUYPWwtVX-wK_39mIA_nM0SCyvKhr6KgNbGZeqnTDp4ru_hSXj9jTeHkpBG1xPcYkNoanCMfY-g"")
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
        "name": "Ваш стиль эмоционального реагирования",
        "description": "Инструмент самодиагностики. Помогает заметить привычные способы справляться с эмоциями.",
        "triggers": ["тест", "эмоции", "эмоциональное реагирование"],
        "answer_scale": 4,
        "questions": [
            {"id": 1, "text": "Когда я злюсь, я говорю «всё нормально», хотя внутри всё кипит", "scales": [1]},
            {"id": 2, "text": "Я скорее промолчу, чем вступлю в конфликт, даже если меня обидели", "scales": [1]},
            {"id": 3, "text": "После ссоры я долго прокручиваю в голове, что надо было ответить", "scales": [6]},
            {"id": 4, "text": "Я убеждён(а), что злиться — это плохо и стыдно", "scales": [1]},
            {"id": 5, "text": "Я могу кричать, хлопать дверью или бить посуду, когда меня довели", "scales": [6]},
            {"id": 6, "text": "Если на меня накричали, я потом срываюсь на том, кто слабее", "scales": [6]},
            {"id": 7, "text": "После конфликта я не могу уснуть, потому что мысленно продолжаю спор", "scales": [6]},
            {"id": 8, "text": "Я стараюсь вообще не попадать в ситуации, где возможен конфликт", "scales": [2]},
            {"id": 9, "text": "Когда я тревожусь, я начинаю есть, даже если не голоден(на)", "scales": [4]},
            {"id": 10, "text": "Чтобы успокоиться, мне нужно выпить, покурить или принять что-то", "scales": [4]},
            {"id": 11, "text": "Я часами сижу в телефоне, сериалах или играх, чтобы убежать от неприятных мыслей", "scales": [2]},
            {"id": 12, "text": "Я фантазирую о другой жизни, где у меня всё хорошо", "scales": [2]},
            {"id": 13, "text": "Я постоянно проверяю и перепроверяю всё, чтобы не случилось ничего плохого", "scales": [3]},
            {"id": 14, "text": "Мне нужно, чтобы всё было предсказуемо, иначе я не могу расслабиться", "scales": [3]},
            {"id": 15, "text": "Я загружаю себя делами, чтобы не чувствовать тревогу", "scales": [3]},
            {"id": 16, "text": "Мне сложно просить помощи — я должен(на) справляться сам(а)", "scales": [3]},
            {"id": 17, "text": "Когда что-то идёт не так, я виню в этом только себя", "scales": [5]},
            {"id": 18, "text": "Я называю себя глупым(ой) или никчёмным(ой), когда ошибаюсь", "scales": [5]},
            {"id": 19, "text": "Я говорю себе «да ерунда, не стоит расстраиваться», чтобы не плакать", "scales": [1]},
            {"id": 20, "text": "Я обесцениваю свои проблемы: «кому-то хуже, чем мне»", "scales": [5]},
            {"id": 21, "text": "Я могу сутками лежать и ничего не делать, когда мне плохо", "scales": [2]},
            {"id": 22, "text": "Когда мне грустно, я заедаю это или наоборот — не могу есть совсем", "scales": [4]},
            {"id": 23, "text": "Я ухожу в работу с головой, чтобы не чувствовать боль или грусть", "scales": [4]},
            {"id": 24, "text": "Я стараюсь не замечать свои эмоции, когда мне плохо", "scales": [5]},
        ],
        "scales": {
            1: {"name": "Подавление", "term": "«Я не чувствую»", "description": "Вы замораживаете эмоции, говорите «всё нормально», хотя внутри буря.", "price": "Головные боли, давление, панические атаки, эмоциональная отстранённость.", "motto": "«Если я не признаю чувство — его нет».", "advice": "Начните замечать телесные сигналы. Учитесь называть эмоции словами."},
            2: {"name": "Избегание", "term": "«Я не буду об этом думать»", "description": "Любой способ уйти от реальности: сериалы, игры, сон, фантазии.", "price": "Проблемы накапливаются, жизнь проходит мимо.", "motto": "«Если я не вижу проблему — её не существует».", "advice": "10 минут в день наедине с собой. Запишите, от чего вы убегаете."},
            3: {"name": "Гиперконтроль", "term": "«Я должен всё держать под контролем»", "description": "Тревога снимается через тотальный контроль.", "price": "Истощение, выгорание, одиночество.", "motto": "«Если я всё контролирую — ничего плохого не случится».", "advice": "Тренируйтесь отпускать мелочи. Позвольте другим делать ошибки."},
            4: {"name": "Заглушение", "term": "«Я перебью это ощущение»", "description": "Тело используется как контейнер для эмоций.", "price": "Зависимости, разрушение здоровья, стыд.", "motto": "«Если я изменю химию тела — я перестану чувствовать».", "advice": "Ведите дневник эмоций. Ищите замену: прогулка, душ, звонок другу."},
            5: {"name": "Самообвинение", "term": "«Это всё из-за меня»", "description": "Вся агрессия направляется на себя.", "price": "Депрессия, хроническое чувство вины, низкая самооценка.", "motto": "«Лучше я сам(а) себя накажу».", "advice": "Говорите с собой как с другом. Переформулируйте самообвинения."},
            6: {"name": "Отреагирование", "term": "«Я взрываюсь»", "description": "Эмоции мгновенно выплёскиваются на окружающих.", "price": "Разрушенные отношения, чувство вины.", "motto": "«Лучше выпустить пар, чем лопнуть».", "advice": "Отслеживайте признаки гнева. Делайте паузу."}
        }
    },
    "defense": {
        "name": "Ваши способы психологической защиты",
        "description": "Инструмент самодиагностики. Помогает заметить привычные способы защищаться от неприятных эмоций.",
        "triggers": ["защита", "защиты", "психологические защиты"],
        "answer_scale": 5,
        "questions": [
            {"id": 1, "text": "Когда задача кажется слишком сложной, я просто её не делаю", "scales": [1]},
            {"id": 2, "text": "Если что-то расстраивает, я стараюсь этого избегать", "scales": [1]},
            {"id": 3, "text": "Когда настроение плохое, я отдаляюсь от людей и бросаю дела", "scales": [1]},
            {"id": 4, "text": "Когда тревожно, мне нужно, чтобы кто-то поддержал и сказал, что всё будет хорошо", "scales": [2]},
            {"id": 5, "text": "Я постоянно всё перепроверяю, чтобы убедиться, что всё в порядке", "scales": [2]},
            {"id": 6, "text": "У меня есть свои ритуалы, которые снимают страх", "scales": [2]},
            {"id": 7, "text": "Я поступаю импульсивно, как велит мне настроение", "scales": [3]},
            {"id": 8, "text": "Когда я расстраиваюсь, я теряю самоконтроль", "scales": [3]},
            {"id": 9, "text": "Я делаю что-то на эмоциях, даже если знаю, что потом пожалею", "scales": [3]},
            {"id": 10, "text": "Мне невыносимо грустить или огорчаться", "scales": [4]},
            {"id": 11, "text": "Я не выношу физические ощущения стресса", "scales": [4]},
            {"id": 12, "text": "Физические симптомы стресса пугают меня и кажутся невыносимыми", "scales": [4]},
            {"id": 13, "text": "Я стараюсь не замечать свои эмоции, когда грустно", "scales": [5]},
            {"id": 14, "text": "Я обычно отгоняю неприятные чувства", "scales": [5]},
            {"id": 15, "text": "Когда мне плохо, я заставляю себя перестать это чувствовать", "scales": [5]},
            {"id": 16, "text": "Когда приходят грустные мысли, я сразу пытаюсь от них избавиться", "scales": [6]},
            {"id": 17, "text": "Я отгоняю тяжёлые воспоминания", "scales": [6]},
            {"id": 18, "text": "Мне нужно блокировать болезненные мысли", "scales": [6]},
            {"id": 19, "text": "В стрессе я мыслю крайностями: «или идеально, или полный провал»", "scales": [7]},
            {"id": 20, "text": "В сложной ситуации я тороплюсь с выводами", "scales": [7]},
            {"id": 21, "text": "В трудных ситуациях я уверен(а), что знаю, о чём думают другие", "scales": [7]},
            {"id": 22, "text": "Если что-то идёт не так, я виню себя", "scales": [8]},
            {"id": 23, "text": "Я критикую себя за свои решения и ошибки", "scales": [8]},
            {"id": 24, "text": "Я виню себя даже тогда, когда другие говорят, что я не виноват(а)", "scales": [8]},
            {"id": 25, "text": "Я осуждаю других за их поведение и злюсь", "scales": [9]},
            {"id": 26, "text": "Я критикую других за их ошибки", "scales": [9]},
            {"id": 27, "text": "Если у меня что-то не выходит, я думаю, что виноваты окружающие", "scales": [9]},
            {"id": 28, "text": "Я прокручиваю в голове всё плохое, что может случиться в будущем", "scales": [10]},
            {"id": 29, "text": "Столкнувшись с проблемой, я зацикливаюсь на самом страшном сценарии", "scales": [10]},
            {"id": 30, "text": "Я предполагаю худшее и сильно преувеличиваю масштаб беды", "scales": [10]},
            {"id": 31, "text": "Я зацикливаюсь на неприятных событиях из прошлого", "scales": [11]},
            {"id": 32, "text": "Я постоянно прокручиваю в голове неприятные события", "scales": [11]},
            {"id": 33, "text": "Я подолгу анализирую события прошлого, возвращаясь к ним мыслями", "scales": [11]},
        ],
        "scales": {
            1: {"name": "Избегание", "term": "«Я подумаю об этом завтра»", "description": "Психика защищается через уход. Вы откладываете, убегаете, прячетесь.", "price": "Проблемы накапливаются, жизнь проходит мимо.", "motto": "«Я подумаю об этом завтра».", "advice": "Правило 5 минут — просто начните."},
            2: {"name": "Поиск опоры и ритуалы", "term": "«Если я проверю всё 3 раза»", "description": "В тревоге вы ищете опору в повторяющихся действиях и одобрении.", "price": "Отнимает силы, зависимость от чужого мнения.", "motto": "«Если я проверю всё 3 раза, ничего плохого не случится».", "advice": "Сделайте ритуал на один раз меньше."},
            3: {"name": "Эмоциональная импульсивность", "term": "«Я чувствую — значит действую»", "description": "Эмоции берут верх над разумом.", "price": "Разрушенные отношения, чувство вины.", "motto": "«Я чувствую — значит действую».", "advice": "Сделайте 5 глубоких вдохов перед действием."},
            4: {"name": "Непереносимость дискомфорта", "term": "«Лишь бы это прекратилось»", "description": "Любое напряжение кажется невыносимым.", "price": "Ограничение жизни, избегание.", "motto": "«Лишь бы это прекратилось».", "advice": "Перенесите внимание в стопы, назовите 5 предметов."},
            5: {"name": "Подавление эмоций", "term": "«Я не чувствую»", "description": "Вместо проживания чувств вы их «выключаете».", "price": "Психосоматика, срывы, апатия.", "motto": "«Я не чувствую».", "advice": "3 минуты пишите о чувствах."},
            6: {"name": "Блокировка мыслей", "term": "«Я не буду об этом думать»", "description": "Вы пытаетесь не думать о боли.", "price": "Мысли возвращаются сильнее.", "motto": "«Я не буду об этом думать».", "advice": "Представьте мысль на облаке и отпустите."},
            7: {"name": "Крайности мышления", "term": "«Всё или ничего»", "description": "Мозг мыслит крайностями.", "price": "Искажённое восприятие.", "motto": "«Всё или ничего».", "advice": "Придумайте 3 спокойных объяснения."},
            8: {"name": "Самообвинение", "term": "«Это всё из-за меня»", "description": "Вы вините себя во всём.", "price": "Депрессия, низкая самооценка.", "motto": "«Это всё из-за меня».", "advice": "Разделите ответственность на 3 колонки."},
            9: {"name": "Обвинение других", "term": "«Это они всё испортили»", "description": "Вы ищете причины в других.", "price": "Позиция жертвы, потеря контроля.", "motto": "«Это они всё испортили».", "advice": "Спросите: «Что я могу сделать сейчас?»"},
            10: {"name": "Катастрофизация", "term": "«А что, если...»", "description": "Мозг рисует страшные сценарии.", "price": "Постоянная тревога.", "motto": "«А что, если случится самое страшное?»", "advice": "Выделите 15 минут для тревоги."},
            11: {"name": "Руминация", "term": "«Почему так случилось?»", "description": "Вы прокручиваете прошлое снова и снова.", "price": "Силы уходят, настоящее проходит мимо.", "motto": "«Почему так случилось?»", "advice": "Сделайте физическое действие и спросите: «Что теперь?»"}
        }
    },
    "thinking": {
        "name": "Ваши ловушки мышления",
        "description": "Инструмент самодиагностики когнитивных искажений.",
        "triggers": ["мышление", "искажения", "когнитивные искажения", "ловушки мышления"],
        "answer_scale": 5,
        "questions": [
            {"id": 1, "text": "Я часто мыслю крайностями: «или идеально, или никак»", "scales": [1]},
            {"id": 2, "text": "Любая моя ошибка кажется мне тотальным провалом", "scales": [1]},
            {"id": 3, "text": "В людях я вижу либо только хорошее, либо только плохое", "scales": [1]},
            {"id": 4, "text": "Я часто прокручиваю в голове худшие сценарии", "scales": [2]},
            {"id": 5, "text": "Я сильно преувеличиваю масштаб проблем и их последствий", "scales": [2]},
            {"id": 6, "text": "Мне кажется, что если что-то пойдёт не так, это будет катастрофа", "scales": [2]},
            {"id": 7, "text": "Я часто думаю, что знаю, о чём думают другие люди", "scales": [3]},
            {"id": 8, "text": "Я уверен(а), что окружающие оценивают и осуждают меня", "scales": [3]},
            {"id": 9, "text": "Я предполагаю, что другие обо мне плохого мнения, не проверяя это", "scales": [3]},
            {"id": 10, "text": "Из одной неудачи я делаю вывод, что у меня вообще ничего не получается", "scales": [4]},
            {"id": 11, "text": "Если что-то идёт не так в одном месте, я думаю, что так будет везде", "scales": [4]},
            {"id": 12, "text": "Я делаю глобальные выводы из единичных случаев", "scales": [4]},
            {"id": 13, "text": "У меня есть много жёстких правил о том, как должны поступать другие", "scales": [5]},
            {"id": 14, "text": "Я часто говорю «я должен/должна» и чувствую вину, если не справляюсь", "scales": [5]},
            {"id": 15, "text": "Когда люди не соответствуют моим ожиданиям, я сильно раздражаюсь", "scales": [5]},
            {"id": 16, "text": "Я не замечаю свои успехи и достижения — я их обесцениваю", "scales": [6]},
            {"id": 17, "text": "Хорошие события кажутся мне неважными или случайными", "scales": [6]},
            {"id": 18, "text": "Я концентрируюсь на негативе, даже если позитива было больше", "scales": [6]},
            {"id": 19, "text": "Я считаю, что мои чувства всегда отражают реальность", "scales": [7]},
            {"id": 20, "text": "Если я боюсь, я думаю, что есть реальная опасность", "scales": [7]},
            {"id": 21, "text": "Если я чувствую себя виноватым(ой), значит, я действительно виноват(а)", "scales": [7]},
            {"id": 22, "text": "Я часто беру на себя ответственность за настроение других", "scales": [8]},
            {"id": 23, "text": "Мне кажется, что люди вокруг меня расстраиваются из-за моих действий", "scales": [8]},
            {"id": 24, "text": "Я чувствую себя ответственным(ой) за всё, что происходит вокруг", "scales": [8]},
            {"id": 25, "text": "Я замечаю в других то, что не принимаю в себе", "scales": [9]},
            {"id": 26, "text": "Когда я злюсь, мне кажется, что это на меня злятся", "scales": [9]},
            {"id": 27, "text": "Я осуждаю в людях те качества, которые есть у меня", "scales": [9]},
        ],
        "scales": {
            1: {"name": "Черно-белое мышление", "term": "«Всё или ничего»", "description": "Вы видите мир в крайностях.", "price": "Любая ошибка превращается в катастрофу.", "motto": "«Всё или ничего».", "advice": "Замените крайность на средний вариант."},
            2: {"name": "Катастрофизация", "term": "«А что, если...»", "description": "Вы преувеличиваете масштаб проблемы.", "price": "Постоянная тревога.", "motto": "«А что, если...»", "advice": "Спросите: «Что самое страшное?»"},
            3: {"name": "Чтение мыслей", "term": "«Я знаю, что ты думаешь»", "description": "Вы уверены, что знаете мысли других.", "price": "Обиды, недопонимание.", "motto": "«Я знаю, что ты думаешь».", "advice": "Спросите прямо."},
            4: {"name": "Чрезмерное обобщение", "term": "«У меня никогда...»", "description": "Из одного случая — глобальный вывод.", "price": "Низкая самооценка.", "motto": "«У меня никогда ничего не получается».", "advice": "Найдите исключение."},
            5: {"name": "Долженствование", "term": "«Друзья должны...»", "description": "Жёсткие правила о том, как всё должно быть.", "price": "Злость и разочарование.", "motto": "«Друзья должны...»", "advice": "Замените «должен» на «предпочитаю»."},
            6: {"name": "Обесценивание позитива", "term": "«Это случайно»", "description": "Вы не замечаете хорошее.", "price": "Потеря радости.", "motto": "«Это случайно».", "advice": "Записывайте 3 хорошие вещи в день."},
            7: {"name": "Эмоциональное обоснование", "term": "«Я боюсь — значит опасно»", "description": "Вы путаете чувства с реальностью.", "price": "Тревога управляет жизнью.", "motto": "«Я боюсь — значит есть опасность».", "advice": "Разделите чувства и факты."},
            8: {"name": "Персонализация", "term": "«Это я виноват(а)»", "description": "Вы берёте ответственность за всё.", "price": "Чувство вины, истощение.", "motto": "«Это я виноват(а)».", "advice": "Спросите: «Это про меня?»"},
            9: {"name": "Проекция", "term": "«Это не я, это он»", "description": "Вы видите в других то, что не принимаете в себе.", "price": "Искажённое восприятие.", "motto": "«Это не я, это он».", "advice": "Спросите: «А не чувствую ли я это сам(а)?»"}
        }
    },
    "projection": {
        "name": "Замечаете ли вы в других то, что скрыто в вас?",
        "description": "Инструмент самодиагностики проекции.",
        "triggers": ["проекция", "проекции", "тест на проекцию"],
        "answer_scale": 5,
        "questions": [
            {"id": 1, "text": "Когда я злюсь, мне кажется, что окружающие злятся на меня", "scales": [1]},
            {"id": 2, "text": "Мне часто кажется, что люди агрессивно ко мне настроены", "scales": [1]},
            {"id": 3, "text": "Если я чувствую раздражение, я вижу его в глазах других", "scales": [1]},
            {"id": 4, "text": "Если человек мне приятен, мне кажется, что я ему тоже нравлюсь", "scales": [2]},
            {"id": 5, "text": "Я часто думаю, что кто-то в меня влюблён, хотя у меня нет доказательств", "scales": [2]},
            {"id": 6, "text": "Мне кажется, что люди смотрят на меня с особым интересом", "scales": [2]},
            {"id": 7, "text": "Если я завидую, мне кажется, что это мне завидуют", "scales": [3]},
            {"id": 8, "text": "Я думаю, что люди завидуют моим успехам", "scales": [3]},
            {"id": 9, "text": "Мне кажется, что другие не радуются за меня искренне", "scales": [3]},
            {"id": 10, "text": "Когда я чувствую вину, мне кажется, что все меня осуждают", "scales": [4]},
            {"id": 11, "text": "Если мне стыдно, я вижу осуждение в глазах других", "scales": [4]},
            {"id": 12, "text": "Мне кажется, что люди видят мои недостатки", "scales": [4]},
            {"id": 13, "text": "Я замечаю в других то, что не принимаю в себе", "scales": [5]},
            {"id": 14, "text": "Больше всего меня бесят в людях те черты, которые есть у меня", "scales": [5]},
            {"id": 15, "text": "Я осуждаю в других то, что тайно делаю сам(а)", "scales": [5]},
            {"id": 16, "text": "Мне кажется, что люди считают меня слабым(ой)", "scales": [6]},
            {"id": 17, "text": "Если я чувствую себя неуверенно, я думаю, что все это замечают", "scales": [6]},
            {"id": 18, "text": "Мне кажется, что окружающие не верят в меня", "scales": [6]},
            {"id": 19, "text": "Если я боюсь быть отвергнутым(ой), мне кажется, что люди меня избегают", "scales": [7]},
            {"id": 20, "text": "Мне кажется, что люди не хотят со мной общаться", "scales": [7]},
            {"id": 21, "text": "Я вижу признаки того, что меня не любят", "scales": [7]},
            {"id": 22, "text": "Если я не доверяю людям, мне кажется, что они не доверяют мне", "scales": [8]},
            {"id": 23, "text": "Мне кажется, что люди говорят обо мне за моей спиной", "scales": [8]},
            {"id": 24, "text": "Я думаю, что окружающие хотят меня обмануть", "scales": [8]},
            {"id": 25, "text": "Если я недоволен(льна) собой, мне кажется, что другие недовольны мной", "scales": [9]},
            {"id": 26, "text": "Когда я не справляюсь, я вижу разочарование в глазах других", "scales": [9]},
            {"id": 27, "text": "Мне кажется, что люди ждут от меня большего", "scales": [9]},
            {"id": 28, "text": "Если мне чего-то хочется, мне кажется, что этого хотят и другие", "scales": [10]},
            {"id": 29, "text": "Я приписываю другим свои скрытые желания", "scales": [10]},
            {"id": 30, "text": "Если я о чём-то мечтаю, я вижу намёки на это в словах других", "scales": [10]},
        ],
        "scales": {
            1: {"name": "Проекция злости", "term": "«Это не я злюсь, это на меня злятся»", "description": "Вы не признаёте свою злость и видите её в других.", "price": "Ощущение, что на вас нападают.", "motto": "«Это не я злюсь, это на меня злятся».", "advice": "Спросите: «А не злюсь ли я сам(а)?»"},
            2: {"name": "Проекция симпатии", "term": "«Я нравлюсь ему(ей)»", "description": "Вы приписываете другим своё влечение.", "price": "Неверное истолкование поведения.", "motto": "«Я нравлюсь ему(ей)».", "advice": "Проверяйте реальность."},
            3: {"name": "Проекция зависти", "term": "«Это мне завидуют»", "description": "Вы не признаёте свою зависть.", "price": "Не можете радоваться чужим успехам.", "motto": "«Это мне завидуют».", "advice": "Признайте: «Я завидую. Это нормально»."},
            4: {"name": "Проекция вины и стыда", "term": "«Все меня осуждают»", "description": "Внутренняя вина превращается в уверенность, что все осуждают.", "price": "Ощущение, что все видят недостатки.", "motto": "«Все меня осуждают».", "advice": "Разделите: что я знаю, а что предполагаю."},
            5: {"name": "Проекция своих качеств", "term": "«Меня бесит в других то, что есть во мне»", "description": "Вы замечаете и осуждаете в других свои качества.", "price": "Не можете принять себя.", "motto": "«Меня бесит в других то, что есть во мне».", "advice": "Спросите: «Где это есть во мне?»"},
            6: {"name": "Проекция беспомощности", "term": "«Все видят, что я не справляюсь»", "description": "Неуверенность превращается в уверенность, что другие не верят в вас.", "price": "Избегание действий.", "motto": "«Все видят, что я не справляюсь».", "advice": "Спросите: «Кто конкретно это сказал?»"},
            7: {"name": "Проекция отвержения", "term": "«Меня не любят»", "description": "Страх быть отвергнутым заставляет видеть отвержение.", "price": "Отдаление от людей.", "motto": "«Меня не любят».", "advice": "Проверяйте факты."},
            8: {"name": "Проекция недоверия", "term": "«Им нельзя доверять»", "description": "Вы подозреваете других в обмане.", "price": "Напряжение в отношениях.", "motto": "«Им нельзя доверять».", "advice": "Спросите: «Что подтверждено фактами?»"},
            9: {"name": "Проекция ответственности", "term": "«Я должна всё контролировать»", "description": "Вы приписываете другим свои завышенные требования.", "price": "Чувство, что не соответствуете ожиданиям.", "motto": "«Я должна всё контролировать».", "advice": "Разделите: чего жду я, а чего ждут другие."},
            10: {"name": "Проекция желаний", "term": "«Я хочу — значит, и другие хотят»", "description": "Вы приписываете другим свои желания.", "price": "Ошибки в понимании других.", "motto": "«Я хочу — значит, и другие хотят».", "advice": "Спросите: «А чего хочет этот человек?»"}
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
                        "Напишите одно из слов:\n"
                        "• тест\n"
                        "• защита\n"
                        "• мышление\n"
                        "• проекция"
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
        
        else:
            send_message(
                user_id,
                "По всем вопросам пишите мне:\n"
                "👉 https://vk.ru/tonker"
            )
            
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
    
    message = "🎯 Ваш результат: " + test_data["name"] + "\n\n"
    message += dominant["name"] + "\n"
    message += "📊 " + dominant["term"] + "\n\n"
    message += "Как проявляется:\n" + dominant["description"] + "\n\n"
    message += "Цена:\n" + dominant["price"] + "\n\n"
    message += "Девиз:\n" + dominant["motto"] + "\n\n"
    message += "Что делать:\n" + dominant["advice"] + "\n\n"
    message += "📈 Балл: " + str(results["dominant_score"]) + "\n"
    
    if results["secondary_type"]:
        secondary = scales[results["secondary_type"]]
        message += "\n🔹 Дополнительно: " + secondary["name"] + "\n"
        message += "📊 " + secondary["term"] + "\n"
    
    message += "\n💬 Нужна помощь?\n👉 " + VK_COMMUNITY_URL + "\n"
    
    return message

def update_stats(user_id, username, dominant_type, scores):
    """Обновление статистики"""
    try:
        stats = load_stats()
        stats["total_tests"] = stats.get("total_tests", 0) + 1
        
        if "scale_stats" not in stats:
            stats["scale_stats"] = {}
        
        key = str(dominant_type)
        stats["scale_stats"][key] = stats["scale_stats"].get(key, 0) + 1
        
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
        
        text = "📊 Статистика:\n\n"
        text += "Всего тестов: " + str(stats.get("total_tests", 0)) + "\n"
        text += "Всего пользователей: " + str(len(stats.get("users", []))) + "\n"
        
        if "scale_stats" in stats and stats["scale_stats"]:
            text += "\nРаспределение:\n"
            for scale_id, count in stats["scale_stats"].items():
                if count > 0:
                    text += "• Шкала " + str(scale_id) + ": " + str(count) + "\n"
        
        send_message(user_id, text)
    except Exception as e:
        logger.error(f"Ошибка показа статистики: {e}")

def run_longpoll():
    """Запуск Long Poll"""
    logger.info("VK бот запущен")
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                try:
                    process_message(event)
                except Exception as e:
                    logger.error(f"Ошибка: {e}")
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
