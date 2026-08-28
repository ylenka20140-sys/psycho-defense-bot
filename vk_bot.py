from flask import Flask, request
import requests

app = Flask(__name__)

VK_TOKEN = "vk1.a.O1auF69C9UOlPmdYFDk6n_Vr1yHhiVDSljJhFiAtNbAg5o-AtkL33zIT6wN_IK7yuzayK3lbTmPX_r6MgucZLp7zX9NB0bDNHJMX4J8x54l03pSzNdsSc7ETq-Pvk3kUdoftaGuxJuNwwSj_Rm_9nipRmJCNxEhilmQzoGh5PVUMTEGydcmHp3RwdiiKN8G_6TxUHcOJAxU5e1nzcOMj2g"
GROUP_ID = "240718452"
CONFIRMATION_CODE = "dd5bba33"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print("=" * 50)
        print("📨 ПОЛНЫЙ ЗАПРОС ОТ ВК:")
        print(data)
        print("=" * 50)
        
        if data.get("type") == "confirmation":
            print("✅ Подтверждение сервера")
            return CONFIRMATION_CODE
        
        if data.get("type") == "wall_reply_new":
            text = data["object"].get("text", "").lower()
            print(f"Текст комментария: '{text}'")
            if "тест" in text:
                user_id = data["object"]["from_id"]
                post_id = data["object"]["post_id"]
                print(f"Пользователь {user_id}, пост {post_id}")
                result = requests.post("https://api.vk.com/method/wall.createComment", params={
                    "group_id": GROUP_ID,
                    "post_id": post_id,
                    "from_group": 1,
                    "message": "✅ Чтобы получить ссылку на тест, подпишись и напиши «тест» в личку.",
                    "access_token": VK_TOKEN,
                    "v": "5.199"
                })
                print(f"Ответ ВК: {result.text}")
            else:
                print("⚠️ Слово 'тест' не найдено")
        
        if data.get("type") == "message_new":
            user_id = data["object"]["from_id"]
            text = data["object"].get("text", "").lower()
            print(f"Текст сообщения: '{text}'")
            if "тест" in text:
                check = requests.get("https://api.vk.com/method/groups.isMember", params={
                    "group_id": GROUP_ID,
                    "user_id": user_id,
                    "access_token": VK_TOKEN,
                    "v": "5.199"
                }).json()
                is_subscribed = check.get("response", 0) == 1
                print(f"Подписка: {is_subscribed}")
                if is_subscribed:
                    requests.post("https://api.vk.com/method/messages.send", params={
                        "user_id": user_id,
                        "message": "🎉 Ссылка на тест: https://t.me/uznaisebya_tonker_bot",
                        "random_id": 123456,
                        "access_token": VK_TOKEN,
                        "v": "5.199"
                    })
                    print("✅ Ссылка отправлена")
                else:
                    requests.post("https://api.vk.com/method/messages.send", params={
                        "user_id": user_id,
                        "message": "🙁 Подпишись: https://vk.ru/club240718452 и напиши «тест» снова.",
                        "random_id": 123457,
                        "access_token": VK_TOKEN,
                        "v": "5.199"
                    })
                    print("✅ Просьба подписаться отправлена")
            else:
                print("⚠️ Слово 'тест' не найдено в сообщении")
        
        return "ok", 200
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return "error", 500

@app.route('/')
def index():
    return "VK Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
