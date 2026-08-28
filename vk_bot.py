from flask import Flask, request
import requests

app = Flask(__name__)

VK_TOKEN = "vk1.a.O1auF69C9UOlPmdYFDk6n_Vr1yHhiVDSljJhFiAtNbAg5o-AtkL33zIT6wN_IK7yuzayK3lbTmPX_r6MgucZLp7zX9NB0bDNHJMX4J8x54l03pSzNdsSc7ETq-Pvk3kUdoftaGuxJuNwwSj_Rm_9nipRmJCNxEhilmQzoGh5PVUMTEGydcmHp3RwdiiKN8G_6TxUHcOJAxU5e1nzcOMj2g"
GROUP_ID = "240718452"
CONFIRMATION_CODE = "dd5bba33"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("ПРИШЛО:", data)

    # ЭТО САМОЕ ВАЖНОЕ — ПОДТВЕРЖДЕНИЕ СЕРВЕРА
    if data.get("type") == "confirmation":
        return CONFIRMATION_CODE

    if data.get("type") == "wall_reply_new":
        text = data["object"].get("text", "").lower()
        if "тест" in text:
            user_id = data["object"]["from_id"]
            post_id = data["object"]["post_id"]
            requests.post("https://api.vk.com/method/wall.createComment", params={
                "group_id": GROUP_ID,
                "post_id": post_id,
                "from_group": 1,
                "message": "✅ Чтобы получить ссылку на тест, подпишись и напиши «тест» в личку.",
                "access_token": VK_TOKEN,
                "v": "5.199"
            })
            print("Ответил в комментариях")

    if data.get("type") == "message_new":
        user_id = data["object"]["from_id"]
        text = data["object"].get("text", "").lower()
        if "тест" in text:
            check = requests.get("https://api.vk.com/method/groups.isMember", params={
                "group_id": GROUP_ID,
                "user_id": user_id,
                "access_token": VK_TOKEN,
                "v": "5.199"
            }).json()
            if check.get("response", 0) == 1:
                requests.post("https://api.vk.com/method/messages.send", params={
                    "user_id": user_id,
                    "message": "🎉 Ссылка на тест: https://t.me/uznaisebya_tonker_bot",
                    "random_id": 123456,
                    "access_token": VK_TOKEN,
                    "v": "5.199"
                })
                print("Ссылка отправлена")
            else:
                requests.post("https://api.vk.com/method/messages.send", params={
                    "user_id": user_id,
                    "message": "Подпишись: https://vk.ru/club240718452 и напиши «тест» снова.",
                    "random_id": 123457,
                    "access_token": VK_TOKEN,
                    "v": "5.199"
                })
                print("Просьба подписаться отправлена")

    return "ok", 200

@app.route('/')
def index():
    return "VK Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
