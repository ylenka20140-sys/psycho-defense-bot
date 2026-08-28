import time
import requests
import random
import traceback
from flask import Flask, request, jsonify

# ===== НАСТРОЙКИ =====
VK_TOKEN = "vk1.a.u4aTmwLlYk5hgPCFtah29K6shnccC1zmphd29rY3oIW0C3oIxmbfQzH7X-RUyYsviRrc2R1_idmxGIZh51VXriSQQgFXyP8ENzZAYYV82ovy7VRHT7KsrT3TUv1DxT-AxDzNTMtpFHlcBLnFx_gCjnvZ_KJoGqcXcZjSjrivBQCeEiylTHUHh1zPN7Zt0nXjN9SKFqr-ILum9aMPut8dOg"
GROUP_ID = "240718452"
TELEGRAM_BOT_LINK = "https://t.me/uznaisebya_tonker_bot"
CONFIRMATION_CODE = "afe8a0fa"

# ===== ОТВЕТЫ =====
# Ответ в комментариях (теперь всегда отправляется)
COMMENT_REPLY = "Спасибо за интерес! 😊 Чтобы получить ссылку на тест «Психологические защиты», пожалуйста, напиши мне в личные сообщения. Я проверю, подписан(а) ли ты на наше сообщество, и отправлю тебе ссылку! 🤍"

# Ответ в личку (только если пользователь сам написал боту)
MESSAGE_SUBSCRIBED = "Отлично! 🎉 Ты подписан(а) на наше сообщество!\n\nВот ссылка на тест «Психологические защиты»:\n👉 {}\n\nПроходи тест, а потом пришли мне скриншот результатов — я помогу с расшифровкой! 🤍".format(TELEGRAM_BOT_LINK)

MESSAGE_NOT_SUBSCRIBED = "Я тебя пока не вижу среди подписчиков 🙁\n\nПодпишись на наше сообщество «Всё будет, просто нужно время»:\n👉 https://vk.ru/club{}\n\nИ нажми на кнопку «Подписка есть», чтобы я проверил(а) снова 👇".format(GROUP_ID)

# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С ВК =====

def vk_request(method, params):
    url = f"https://api.vk.com/method/{method}"
    params["access_token"] = VK_TOKEN
    params["v"] = "5.199"
    try:
        print(f"Запрос к ВК: {method}")
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"Ошибка запроса к ВК: {e}")
        return {}

def check_subscription(user_id):
    print(f"Проверка подписки для пользователя {user_id}")
    result = vk_request("groups.isMember", {
        "group_id": GROUP_ID,
        "user_id": user_id
    })
    return result.get("response", 0) == 1

def send_message(user_id, message, keyboard=None):
    print(f"Отправка сообщения пользователю {user_id}")
    params = {
        "user_id": user_id,
        "message": message,
        "random_id": random.randint(1, 10**9)
    }
    if keyboard:
        params["keyboard"] = keyboard
    return vk_request("messages.send", params)

def reply_to_comment(post_id, user_id, message):
    print(f"Ответ на комментарий в посте {post_id} пользователю {user_id}")
    params = {
        "group_id": GROUP_ID,
        "post_id": post_id,
        "from_group": 1,
        "message": message
    }
    return vk_request("wall.createComment", params)

# ===== ОБРАБОТКА СОБЫТИЙ =====

def handle_comment(comment_data):
    try:
        print("=" * 50)
        print("Начало обработки комментария")
        
        text = comment_data.get("text", "").lower()
        print(f"Текст комментария: '{text}'")
        
        if "тест" not in text:
            print("Ключевое слово 'тест' не найдено")
            return
        
        user_id = comment_data["from_id"]
        post_id = comment_data["post_id"]
        
        print(f"✅ Найдено ключевое слово! Пользователь {user_id}")
        
        # ✅ ВСЕГДА ОТВЕЧАЕМ В КОММЕНТАРИЯХ
        print("Отправка ответа в комментарии...")
        reply_to_comment(post_id, user_id, COMMENT_REPLY)
        print("✅ Ответ в комментариях отправлен")
        
        print("Обработка комментария завершена")
        print("=" * 50)
    except Exception as e:
        print(f"❌ Ошибка в handle_comment: {e}")
        traceback.print_exc()

def handle_message(message_data):
    try:
        print("=" * 50)
        print("Начало обработки сообщения")
        user_id = message_data["from_id"]
        text = message_data.get("text", "").lower()
        print(f"Текст сообщения: '{text}'")
        print(f"От пользователя: {user_id}")
        
        # Проверяем подписку
        is_subscribed = check_subscription(user_id)
        print(f"Пользователь подписан: {is_subscribed}")
        
        if is_subscribed:
            send_message(user_id, MESSAGE_SUBSCRIBED)
            print("✅ Сообщение подписчику отправлено")
        else:
            keyboard = {
                "one_time": True,
                "buttons": [
                    [{
                        "action": {
                            "type": "callback",
                            "label": "✅ Подписка есть",
                            "payload": {"action": "check_subscription"}
                        },
                        "color": "positive"
                    }]
                ]
            }
            send_message(user_id, MESSAGE_NOT_SUBSCRIBED, str(keyboard))
            print("✅ Сообщение неподписанному пользователю отправлено")
        
        print("Обработка сообщения завершена")
        print("=" * 50)
    except Exception as e:
        print(f"❌ Ошибка в handle_message: {e}")
        traceback.print_exc()

# ===== Flask-СЕРВЕР =====

app = Flask(__name__)

@app.route('/')
def index():
    return "VK Bot is running! ✅"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        print("=" * 60)
        print("📨 ПОЛУЧЕН НОВЫЙ ЗАПРОС ОТ ВК")
        data = request.json
        print(f"Полный запрос: {data}")
        
        if not data:
            print("❌ Пустой запрос")
            return "ok", 200
        
        event_type = data.get("type")
        print(f"Тип события: {event_type}")
        
        if event_type == "confirmation":
            print("✅ Подтверждение сервера")
            return CONFIRMATION_CODE
        
        if event_type == "wall_reply_new":
            print("✅ Найден новый комментарий!")
            handle_comment(data["object"])
        elif event_type == "message_new":
            print("✅ Найдено новое сообщение!")
            handle_message(data["object"])
        else:
            print(f"⚠️ Неизвестный тип события: {event_type}")
        
        print("=" * 60)
        return "ok", 200
    except Exception as e:
        print("=" * 60)
        print("❌ ОШИБКА В WEBHOOK:")
        print(f"Текст ошибки: {e}")
        traceback.print_exc()
        print("=" * 60)
        return "error", 500

if __name__ == "__main__":
    print("✅ Бот ВКонтакте запущен!")
    app.run(host="0.0.0.0", port=5000)
