import time
import requests
import random
from flask import Flask, request, jsonify

# ===== НАСТРОЙКИ (ЗАМЕНИТЕ НА СВОИ) =====
VK_TOKEN = "vk1.a.u4aTmwLlYk5hgPCFtah29K6shnccC1zmphd29rY3oIW0C3oIxmbfQzH7X-RUyYsviRrc2R1_idmxGIZh51VXriSQQgFXyP8ENzZAYYV82ovy7VRHT7KsrT3TUv1DxT-AxDzNTMtpFHlcBLnFx_gCjnvZ_KJoGqcXcZjSjrivBQCeEiylTHUHh1zPN7Zt0nXjN9SKFqr-ILum9aMPut8dOg"
GROUP_ID = "240718452"
TELEGRAM_BOT_LINK = "https://t.me/uznaisebya_tonker_bot"

# ===== ОТВЕТЫ =====
COMMENT_REPLY = "Спасибо за интерес! 😊 Я отправил(а) тебе ссылку на тест в личные сообщения — проверь директ. Чтобы получить доступ, нужно быть подписанным на наше сообщество 🤍"

MESSAGE_SUBSCRIBED = "Отлично! 🎉 Я вижу твою подписку!\n\nВот ссылка на тест «Психологические защиты»:\n👉 {}\n\nПроходи тест, а потом пришли мне скриншот результатов — я помогу с расшифровкой! 🤍".format(TELEGRAM_BOT_LINK)

MESSAGE_NOT_SUBSCRIBED = "Я тебя пока не вижу среди подписчиков 🙁\n\nПодпишись на наше сообщество «Всё будет, просто нужно время»:\n👉 https://vk.ru/club{}\n\nИ нажми на кнопку «Подписка есть», чтобы я проверил(а) снова 👇".format(GROUP_ID)

# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С ВК =====

def vk_request(method, params):
    url = f"https://api.vk.com/method/{method}"
    params["access_token"] = VK_TOKEN
    params["v"] = "5.131"
    response = requests.get(url, params=params)
    return response.json()

def check_subscription(user_id):
    result = vk_request("groups.isMember", {
        "group_id": GROUP_ID,
        "user_id": user_id
    })
    return result.get("response", 0) == 1

def send_message(user_id, message, keyboard=None):
    params = {
        "user_id": user_id,
        "message": message,
        "random_id": random.randint(1, 10**9)
    }
    if keyboard:
        params["keyboard"] = keyboard
    return vk_request("messages.send", params)

def reply_to_comment(post_id, user_id, message):
    params = {
        "group_id": GROUP_ID,
        "post_id": post_id,
        "from_group": 1,
        "message": message
    }
    return vk_request("wall.createComment", params)

# ===== ОБРАБОТКА СОБЫТИЙ =====

def handle_comment(comment_data):
    text = comment_data.get("text", "").lower()
    if "тест" not in text:
        return
    user_id = comment_data["from_id"]
    post_id = comment_data["post_id"]
    reply_to_comment(post_id, user_id, COMMENT_REPLY)
    if check_subscription(user_id):
        send_message(user_id, MESSAGE_SUBSCRIBED)
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

def handle_message(message_data):
    user_id = message_data["from_id"]
    text = message_data.get("text", "").lower()
    if "подписка есть" in text:
        if check_subscription(user_id):
            send_message(user_id, MESSAGE_SUBSCRIBED)
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

# ===== Flask-СЕРВЕР =====

app = Flask(__name__)

@app.route('/')
def index():
    return "VK Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data.get("type") == "confirmation":
        return "YOUR_CONFIRMATION_CODE"
    if data.get("type") == "wall_reply_new":
        handle_comment(data["object"])
    elif data.get("type") == "message_new":
        handle_message(data["object"])
    return "ok"

if __name__ == "__main__":
    if VK_TOKEN == "vk1.a.u4aTmwLlYk5hgPCFtah29K6shnccC1zmphd29rY3oIW0C3oIxmbfQzH7X-RUyYsviRrc2R1_idmxGIZh51VXriSQQgFXyP8ENzZAYYV82ovy7VRHT7KsrT3TUv1DxT-AxDzNTMtpFHlcBLnFx_gCjnvZ_KJoGqcXcZjSjrivBQCeEiylTHUHh1zPN7Zt0nXjN9SKFqr-ILum9aMPut8dOg":
        print("⚠️ Вставьте токен ВКонтакте в переменную VK_TOKEN!")
        exit()
    print("✅ Бот ВКонтакте запущен!")
    app.run(host="0.0.0.0", port=5000)