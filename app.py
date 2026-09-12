import os
import time
import threading
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
timers = {}


def telegram(method, data):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    return requests.post(url, data=data, timeout=20)


def format_time(seconds):
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def run_timer(chat_id, message_id, end_time):
    while True:
        remaining = int(end_time - time.time())

        if remaining <= 0:
            text = "⏰ شمارش معکوس تمام شد!\n\n🔴 00:00:00"
            telegram("editMessageText", {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text
            })
            timers.pop(chat_id, None)
            break

        text = (
            "⏳ شمارش معکوس ۱۲ ساعته\n\n"
            f"🔥 {format_time(remaining)}"
        )

        telegram("editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text
        })

        time.sleep(5)


def start_countdown(chat_id):
    end_time = time.time() + (12 * 60 * 60)

    result = telegram("sendMessage", {
        "chat_id": chat_id,
        "text": "⏳ شمارش معکوس ۱۲ ساعته شروع شد!\n\n🔥 12:00:00"
    })

    try:
        message_id = result.json()["result"]["message_id"]
    except Exception:
        return

    timers[chat_id] = True

    thread = threading.Thread(
        target=run_timer,
        args=(chat_id, message_id, end_time),
        daemon=True
    )
    thread.start()


def stop_countdown(chat_id):
    timers.pop(chat_id, None)

    telegram("sendMessage", {
        "chat_id": chat_id,
        "text": "🛑 شمارش معکوس متوقف شد."
    })


@app.route("/", methods=["GET"])
def home():
    return "Countdown Bot is running! ✅"


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True)

    if not update:
        return "OK"

    message = update.get("message", {})
    text = message.get("text", "")
    chat = message.get("chat", {})

    chat_id = chat.get("id")

    if not chat_id:
        return "OK"

    if text.startswith("/start12"):
        start_countdown(chat_id)

    elif text.startswith("/stop"):
        stop_countdown(chat_id)

    return "OK"


def set_webhook():
    time.sleep(5)

    render_url = os.environ.get("RENDER_EXTERNAL_URL")

    if render_url:
        webhook_url = render_url + "/webhook"

        telegram("setWebhook", {
            "url": webhook_url
        })


if __name__ == "__main__":
    threading.Thread(target=set_webhook, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
  )
