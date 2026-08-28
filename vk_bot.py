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
        print("=" * 50)
        print("📨 ПОЛНЫЙ ЗАПРОС ОТ ВК:")
        print(data)
        print("=" * 50)
        
        if data.get("type") == "confirmation":
            return CONFIRMATION_CODE
        
        if data.get("type") == "wall_reply_new":
            print("✅ Найден комментарий!")
            text = data["object"].get("text", "").lower()
            print(f"Текст комментария: '{text}'")
            if "тест" in text:
                print("✅ Найдено слово 'тест'!")
                user_id = data["object"]["from_id"]
                post_id = data["object"]["post_id"]
                
                vk_request("wall.createComment", {
                    "group_id": GROUP_ID,
                    "post_id": post_id,
                    "from_group": 1,
                    "message": "✅ Чтобы получить ссылку на тест, подпишись на наше сообщество и напиши слово «тест» в личные сообщения 🤍"
                })
                print("✅ Ответ в комментариях отправлен")
            else:
                print("❌ Слово 'тест' не найдено")
        
        if data.get("type") == "message_new":
            print("✅ Найдено сообщение!")
            user_id = data["object"]["from_id"]
            text = data["object"].get("text", "").lower()
            print(f"Текст сообщения: '{text}'")
            
            if "тест" in text:
                print("✅ Найдено слово 'тест' в сообщении!")
                check = vk_request("groups.isMember", {
                    "group_id": GROUP_ID,
                    "user_id": user_id
                })
                is_subscribed = check.get("response", 0) == 1
                print(f"Подписка: {is_subscribed}")
                
                if is_subscribed:
                    vk_request("messages.send", {
                        "user_id": user_id,
                        "message": f"🎉 Ссылка на тест: {TELEGRAM_BOT_LINK}",
                        "random_id": random.randint(1, 999999)
                    })
                    print("✅ Ссылка отправлена")
                else:
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
                        "message": f"🙁 Ты пока не подписан(а).\nПодпишись: https://vk.ru/club{GROUP_ID}\nИ нажми кнопку.",
                        "random_id": random.randint(1, 999999),
                        "keyboard": str(keyboard)
                    })
                    print("✅ Просьба подписаться отправлена")
        
        return "ok", 200
    except Exception as e:
        print("❌ ОШИБКА:")
        print(e)
        traceback.print_exc()
        return "error", 500

@app.route('/')
def index():
    return "✅ VK Bot is running!"

if __name__ == "__main__":
    print("✅ Бот ВКонтакте запущен!")
    app.run(host="0.0.0.0", port=5000)
