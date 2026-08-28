import requests
import random
import traceback
from flask import Flask, request

# ===== НАСТРОЙКИ =====
VK_TOKEN = "vk1.a.O1auF69C9UOlPmdYFDk6n_Vr1yHhiVDSljJhFiAtNbAg5o-AtkL33zIT6wN_IK7yuzayK3lbTmPX_r6MgucZLp7zX9NB0bDNHJMX4J8x54l03pSzNdsSc7ETq-Pvk3kUdoftaGuxJuNwwSj_Rm_9nipRmJCNxEhilmQzoGh5PVUMTEGydcmHp3RwdiiKN8G_6TxUHcOJAxU5e1nzcOMj2g"
GROUP_ID = "240718452"
CONFIRMATION_CODE = "afe8a0fa"
TELEGRAM_BOT_LINK = "https://t.me/uznaisebya_tonker_bot"

app = Flask(__name__)

def vk_request(method, params):
    params["access_token"] = VK_TOKEN
    params["v"] = "5.199"
    try:
        response = requests.get(f"https://api.vk.com/method/{method}", params=params)
        return response.json()
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return {}

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print("📨 ЗАПРОС ОТ ВК:", data)
        
        if data.get("type") == "confirmation":
            return CONFIRMATION_CODE
        
        # ===== ОБРАБОТКА КОММЕНТАРИЕВ =====
        if data.get("type") == "wall_reply_new":
            text = data["object"].get("text", "").lower()
            # Проверяем, есть ли слово "тест" в любом регистре
            if "тест" in text:
                user_id = data["object"]["from_id"]
                post_id = data["object"]["post_id"]
                
                # Отвечаем в комментариях
                vk_request("wall.createComment", {
                    "group_id": GROUP_ID,
                    "post_id": post_id,
                    "from_group": 1,
                    "message": "✅ Спасибо! Чтобы получить ссылку на тест, напиши мне в личные сообщения слово «тест»."
                })
                print("✅ Ответ в комментариях отправлен")
        
        # ===== ОБРАБОТКА ЛИЧНЫХ СООБЩЕНИЙ =====
        if data.get("type") == "message_new":
            user_id = data["object"]["from_id"]
            text = data["object"].get("text", "").lower()
            print(f"💬 Сообщение от {user_id}: {text}")
            
            # Проверяем, есть ли слово "тест" в сообщении
            if "тест" in text:
                # Проверяем подписку
                check = vk_request("groups.isMember", {
                    "group_id": GROUP_ID,
                    "user_id": user_id
                })
                is_subscribed = check.get("response", 0) == 1
                print(f"Подписка пользователя {user_id}: {is_subscribed}")
                
                if is_subscribed:
                    # Отправляем ссылку на тест
                    vk_request("messages.send", {
                        "user_id": user_id,
                        "message": f"🎉 Ссылка на тест: {TELEGRAM_BOT_LINK}",
                        "random_id": random.randint(1, 999999)
                    })
                    print("✅ Ссылка отправлена подписчику")
                else:
                    # Просим подписаться
                    keyboard = {
                        "one_time": True,
                        "buttons": [[{
                            "action": {
                                "type": "callback",
                                "label": "✅ Проверить подписку",
                                "payload": {}
                            },
                            "color": "positive"
                        }]]
                    }
                    vk_request("messages.send", {
                        "user_id": user_id,
                        "message": f"🙁 Ты пока не подписан(а) на наше сообщество.\n\nПодпишись: https://vk.ru/club{GROUP_ID}\nИ нажми кнопку «Проверить подписку».",
                        "random_id": random.randint(1, 999999),
                        "keyboard": str(keyboard)
                    })
                    print("✅ Сообщение с просьбой подписаться отправлено")
        
        return "ok", 200
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        traceback.print_exc()
        return "error", 500

@app.route('/')
def index():
    return "✅ VK Bot is running!"

if __name__ == "__main__":
    print("✅ Бот ВКонтакте запущен!")
    app.run(host="0.0.0.0", port=5000)
