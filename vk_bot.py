from flask import Flask, request
import requests

app = Flask(__name__)

# ===== ВСТАВЬТЕ СВОИ ДАННЫЕ =====
VK_TOKEN = "vk1.a.eEG1xkwki89TN16IwkYx4609iMe0KRryhMnFIYNRIb7ywwPPBiwWvCzNH-QIghtmP7EwVHemkla_uszpynhymfHLFdVdpmW4mdHbuaq2i-YvVNvhPotX35FNduMmxyed00deNmh9Xk4EFpL7RFsIrdJTU8O6EE_Pif_hbeadgux3ICwj-KVRP5TfR3kF09oGYTHF_R7SClBfiZK3VfIzmQ"
CONFIRMATION_CODE = "d0aa297c"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("📨 ПРИШЛО:", data)

    if data.get("type") == "confirmation":
        return CONFIRMATION_CODE

    if data.get("type") == "message_new":
        user_id = data["object"]["from_id"]
        text = data["object"].get("text", "").lower()

        if "тест" in text:
            # Проверяем подписку
            check = requests.get("https://api.vk.com/method/groups.isMember", params={
                "group_id": "240718452",
                "user_id": user_id,
                "access_token": VK_TOKEN,
                "v": "5.199"
            }).json()

            if check.get("response", 0) == 1:
                # Отправляем ссылку
                requests.post("https://api.vk.com/method/messages.send", params={
                    "user_id": user_id,
                    "message": "🎉 Ссылка на тест: https://t.me/uznaisebya_tonker_bot",
                    "random_id": 123456,
                    "access_token": VK_TOKEN,
                    "v": "5.199"
                })
            else:
                # Просим подписаться
                requests.post("https://api.vk.com/method/messages.send", params={
                    "user_id": user_id,
                    "message": "🌸 Подпишись: https://vk.ru/club240718452 и напиши «тест» снова.",
                    "random_id": 123457,
                    "access_token": VK_TOKEN,
                    "v": "5.199"
                })

    return "ok", 200

@app.route('/')
def index():
    return "VK Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
