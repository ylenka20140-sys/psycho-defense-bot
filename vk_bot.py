import asyncio
import json
import os
from vkbottle import Bot, Message
from vkbottle.bot import BotLabeler
from vkbottle.types import Keyboard, KeyboardButtonColor, Text

# ==================== НАСТРОЙКИ ====================
VK_TOKEN = "vk1.a.a_3dITwtsV9pQscXoUm1fgSpAtJDYBCaFkPZ30GRn4KqdpreBbX_9TP_e5oKJ7Kq5VSu_b1wKtNjcadpGDpN8AOxuipt34XEIvsW8KohkWGBO2Xtp7X5EK2H4e4ScGGWnRAWOx0726cjUYPWwtVX-wK_39mIA_nM0SCyvKhr6KgNbGZeqnTDp4ru_hSXj9jTeHkpBG1xPcYkNoanCMfY-g"
ADMIN_ID = 240718452 # Ваш ID ВКонтакте
STATS_FILE = "vk_stats.json"

# ==================== ДАННЫЕ ТЕСТА ====================
TEST_TITLE = "Ваше эмоциональное реагирование"
TEST_SUBTITLE = "Тест на определение индивидуального стиля совладания с эмоциями"

QUESTIONS = [
    ("Когда я злюсь, я говорю «всё нормально», хотя внутри всё кипит", [1, 0, 0, 0, 0, 0, 0]),
    ("Я скорее промолчу, чем вступлю в конфликт, даже если меня обидели", [1, 0, 0, 0, 0, 0, 0]),
    ("Если на меня накричали, я потом срываюсь на том, кто слабее", [0, 1, 0, 0, 0, 0, 0]),
    ("Я могу кричать, бить посуду или хлопать дверью, когда меня довели", [0, 1, 0, 0, 0, 0, 0]),
    ("Я долго ношу обиду в себе и прокручиваю, что надо было ответить", [0, 0, 1, 0, 0, 0, 0]),
    ("После ссоры я не могу уснуть, потому что мысленно продолжаю спор", [0, 0, 1, 0, 0, 0, 0]),
    ("Я убеждён, что злиться — это плохо и стыдно", [1, 0, 0, 0, 0, 0, 0]),
    ("Я стараюсь вообще не попадать в ситуации, где возможен конфликт", [0, 0, 0, 1, 0, 0, 0]),
    ("Когда я тревожусь, я начинаю есть, даже если не голоден", [0, 0, 0, 0, 1, 0, 0]),
    ("От тревоги у меня пропадает аппетит", [0, 0, 0, 0, 1, 0, 0]),
    ("Чтобы успокоиться, мне нужно выпить, покурить или принять что-то", [0, 0, 0, 0, 1, 0, 0]),
    ("Я загружаю себя делами, чтобы не чувствовать тревогу", [0, 0, 0, 0, 0, 1, 0]),
    ("Я часами сижу в телефоне/сериалах, чтобы убежать от мыслей", [0, 0, 0, 1, 0, 0, 0]),
    ("Я фантазирую о другой жизни, где у меня всё хорошо", [0, 0, 0, 1, 0, 0, 0]),
    ("Я постоянно проверяю и перепроверяю всё, чтобы не случилось плохого", [0, 0, 0, 0, 0, 1, 0]),
    ("Мне нужно, чтобы всё было предсказуемо, иначе я не могу расслабиться", [0, 0, 0, 0, 0, 1, 0]),
    ("Когда что-то идёт не так, я виню в этом только себя", [0, 0, 0, 0, 0, 0, 1]),
    ("Я называю себя глупым/никчёмным, когда ошибаюсь", [0, 0, 0, 0, 0, 0, 1]),
    ("Я говорю себе «да ерунда, не стоит расстраиваться», чтобы не плакать", [1, 0, 0, 0, 0, 0, 0]),
    ("Я обесцениваю свои проблемы: «кому-то хуже, чем мне»", [1, 0, 0, 0, 0, 0, 0]),
    ("Я ухожу в работу с головой, чтобы не чувствовать боль/грусть", [0, 0, 0, 0, 0, 1, 0]),
    ("Я могу сутками лежать и ничего не делать, когда мне плохо", [0, 0, 0, 1, 0, 0, 0]),
    ("Я заедаю грусть или наоборот — не могу есть совсем", [0, 0, 0, 0, 1, 0, 0]),
    ("Мне сложно просить помощи, я должен справляться сам", [0, 0, 0, 0, 0, 1, 0]),
]

TYPES = [
    {
        "name": "«Подавитель»",
        "term": "Вытеснение",
        "description": "🧊 Ваш доминирующий стиль — «Подавитель». Научный термин: вытеснение.\nКак проявляется: «Я не чувствую», эмоции замораживаются.\nЦена: психосоматика, головные боли, панические атаки.\nЧто делать: учиться замечать телесные сигналы и называть эмоции."
    },
    {
        "name": "«Взрыватель»",
        "term": "Отреагирование",
        "description": "💥 Ваш доминирующий стиль — «Взрыватель». Эмоция мгновенно выплёскивается на того, кто под рукой.\nЦена: разрушенные отношения, чувство вины.\nЧто делать: отслеживать первые признаки гнева и делать паузу."
    },
    {
        "name": "«Мыслитель»",
        "term": "Руминация",
        "description": "🧠 Ваш доминирующий стиль — «Мыслитель». Вместо чувств — бесконечный анализ.\nЦена: истощение, бессонница, потеря контакта с телом.\nЧто делать: переключаться с мыслей на тело, ограничивать время обдумывания."
    },
    {
        "name": "«Убегающий»",
        "term": "Избегание",
        "description": "🏃 Ваш доминирующий стиль — «Убегающий». Любой способ уйти от реальности.\nЦена: проблемы копятся, жизнь проходит мимо.\nЧто делать: 10 минут в день без отвлечений, записывать, от чего убегаете."
    },
    {
        "name": "«Заглушающий»",
        "term": "Химический копинг",
        "description": "🍷 Ваш доминирующий стиль — «Заглушающий». Еда, алкоголь, никотин — всё, что даёт быстрый эффект.\nЦена: зависимость, разрушение здоровья, стыд.\nЧто делать: вести дневник эмоций, искать замену (прогулка, звонок другу)."
    },
    {
        "name": "«Контролёр»",
        "term": "Гиперконтроль",
        "description": "🎯 Ваш доминирующий стиль — «Контролёр». Тотальный контроль: всё должно быть идеально.\nЦена: выгорание, раздражение на людей, одиночество.\nЧто делать: тренироваться отпускать мелочи, позволять другим ошибаться."
    },
    {
        "name": "«Самонаказывающий»",
        "term": "Аутоагрессия",
        "description": "⚡ Ваш доминирующий стиль — «Самонаказывающий». Вся агрессия направлена на себя.\nЦена: депрессия, чувство вины, низкая самооценка.\nЧто делать: говорить с собой как с другом, переформулировать самообвинения."
    },
]

# Хранилище
user_answers = {}

# ==================== КЛАВИАТУРЫ ====================

def get_start_keyboard():
    keyboard = Keyboard(inline=False)
    keyboard.add(Text("Начать тест 🔥", payload={"start": True}))
    return keyboard

def get_answer_keyboard(question_index: int):
    keyboard = Keyboard(inline=False)
    for i, label in enumerate(["Совсем не про меня", "Иногда бывает", "Часто бывает", "Это точно про меня"], start=1):
        keyboard.add(Text(f"{i}. {label}", payload={"q": question_index, "a": i}))
    return keyboard

def get_restart_keyboard():
    keyboard = Keyboard(inline=False)
    keyboard.add(Text("Пройти заново 🔄", payload={"restart": True}))
    return keyboard

# ==================== ФУНКЦИИ СТАТИСТИКИ ====================

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"total": 0, "types": [0] * 7, "users": []}

def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def update_stats(user_id: int, dominant_index: int):
    stats = load_stats()
    stats["total"] += 1
    stats["types"][dominant_index] += 1
    if user_id not in stats["users"]:
        stats["users"].append(user_id)
    save_stats(stats)

# ==================== БОТ ====================

bot = Bot(token=VK_TOKEN)
labeler = BotLabeler()
bot.labeler = labeler

@labeler.message(payload={"start": True})
async def start_test(message: Message):
    user_id = message.peer_id
    user_answers[user_id] = []
    await send_question(message, user_id, 0)

@labeler.message(payload={"restart": True})
async def restart_test(message: Message):
    user_id = message.peer_id
    user_answers[user_id] = []
    await send_question(message, user_id, 0)

@labeler.message()
async def handle_text(message: Message):
    user_id = message.peer_id
    text = message.text

    # Проверяем ответ на вопрос (начинается с 1., 2., 3., 4.)
    if text and text[0].isdigit() and ". " in text[:3]:
        parts = text.split(". ", 1)
        if len(parts) == 2:
            try:
                value = int(parts[0])
                if user_id in user_answers and len(user_answers[user_id]) < len(QUESTIONS):
                    q_index = len(user_answers[user_id])
                    user_answers[user_id].append((q_index, value))
                    await send_question(message, user_id, q_index + 1)
                return
            except:
                pass

    # Команда статистики для админа
    if text == "/статистика" and message.from_id == ADMIN_ID:
        stats = load_stats()
        total = stats["total"]
        type_counts = stats["types"]
        unique = len(stats["users"])
        
        msg = f"📊 Статистика:\nВсего прохождений: {total}\nУникальных: {unique}\n\n"
        for i, t in enumerate(TYPES):
            count = type_counts[i]
            percent = round((count / total * 100), 1) if total > 0 else 0
            msg += f"{t['name']}: {count} ({percent}%)\n"
        
        await message.answer(msg)
        return

    # Если не ответ — показываем приветствие
    await show_welcome(message)

async def show_welcome(message: Message):
    text = (
        f"👋 Привет!\n\n"
        f"Это тест «{TEST_TITLE}»\n"
        f"{TEST_SUBTITLE}\n\n"
        f"Он поможет узнать ваш стиль эмоционального реагирования.\n\n"
        f"⚠️ Нет правильных ответов. Будьте честны.\n"
        f"📝 Тест из 24 вопросов, займёт 5–7 минут.\n"
        f"В конце — описание вашего типа."
    )
    await message.answer(text, keyboard=get_start_keyboard())

async def send_question(message: Message, user_id: int, q_index: int):
    if q_index >= len(QUESTIONS):
        await finish_test(message, user_id)
        return

    q_text, _ = QUESTIONS[q_index]
    text = f"Вопрос {q_index + 1} из {len(QUESTIONS)}\n\n{q_text}"
    await message.answer(text, keyboard=get_answer_keyboard(q_index))

async def finish_test(message: Message, user_id: int):
    answers = user_answers.get(user_id, [])
    if not answers:
        return

    # Считаем баллы
    scores = [0] * 7
    for q_index, value in answers:
        _, weights = QUESTIONS[q_index]
        for i, w in enumerate(weights):
            if w == 1:
                scores[i] += value

    max_score = max(scores)
    dominant_index = scores.index(max_score)

    update_stats(user_id, dominant_index)

    result = f"📋 {TEST_TITLE}\n━━━━━━━━━━━\n\n"
    result += TYPES[dominant_index]["description"]
    result += f"\n\n📊 Ваш балл: {max_score}"

    # Дополнительный тип
    secondary = max([(s, i) for i, s in enumerate(scores) if i != dominant_index], default=(0, None))
    if secondary[1] is not None and secondary[0] >= max_score * 0.7:
        result += f"\n\n🔸 Дополнительный тип: {TYPES[secondary[1]]['name']} ({secondary[0]} баллов)"

    result += "\n\n━━━━━━━━━━━\n💡 Большинство людей используют 2–3 стиля.\nТревожный сигнал — когда один стиль становится единственным."

    await message.answer(result, keyboard=get_restart_keyboard())
    user_answers.pop(user_id, None)

# ==================== ЗАПУСК ====================

async def main():
    print("✅ VK Бот запущен!")
    await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
