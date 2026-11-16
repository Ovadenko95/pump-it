"""
Pump it — мінімальний бот для Telegram-групи Kraken Ukraine.

Що вміє:
  /start  (в особистих) — надсилає кнопку «Грати» з прямим посиланням на Mini App.
  /post   (в гілці групи, тільки адмін) — публікує в цю гілку пост з кнопкою «Грати» і закріплює його.

Запуск:
  pip install requests
  export BOT_TOKEN="123456:ABC..."      # токен від @BotFather
  export BOT_USERNAME="PumpItKrakenBot" # без @
  export APP_NAME="play"                # short name з /newapp
  python bot.py

Боту потрібні права адміна в групі: «Надсилати повідомлення» і «Закріплювати повідомлення».
"""
import os
import time
import requests

TOKEN = os.environ["BOT_TOKEN"]
BOT_USERNAME = os.environ.get("BOT_USERNAME", "PumpItKrakenBot")
APP_NAME = os.environ.get("APP_NAME", "play")
API = f"https://api.telegram.org/bot{TOKEN}"

GAME_LINK = f"https://t.me/{BOT_USERNAME}/{APP_NAME}"

PINNED_TEXT = (
    "🎮 <b>PUMP IT — голосова крипто-гра</b>\n\n"
    "Кричи, щоб запампити ціну. Замовкнеш — і графік піде вниз.\n"
    "🟥 Обходь ведмежі свічки\n"
    "🟣 Збирай Kraken, щоб підняти множник\n"
    "🏆 Найкращі ATH тижня потрапляють у топ\n\n"
    "Немає мікрофона під рукою? Можна грати утриманням пальця.\n\n"
    "Поділись своєю карткою з рекордом тут, у гілці 👇"
)


def api(method, **params):
    r = requests.post(f"{API}/{method}", json=params, timeout=40)
    data = r.json()
    if not data.get("ok"):
        print(f"[{method}] error:", data)
    return data


def play_button(start_param=None):
    url = GAME_LINK + (f"?startapp={start_param}" if start_param else "")
    return {"inline_keyboard": [[{"text": "🚀 Грати в Pump it", "url": url}]]}


def is_admin(chat_id, user_id):
    res = api("getChatMember", chat_id=chat_id, user_id=user_id)
    return res.get("ok") and res["result"]["status"] in ("administrator", "creator")


def handle(msg):
    chat = msg["chat"]
    text = (msg.get("text") or "").split("@")[0].strip()
    user = msg.get("from", {})

    if text == "/start" and chat["type"] == "private":
        api("sendMessage", chat_id=chat["id"], parse_mode="HTML",
            text="Готовий запампити? Тисни кнопку 👇",
            reply_markup=play_button())

    elif text == "/post" and chat["type"] in ("group", "supergroup"):
        # anonymous admins post "as the group" (sender_chat == this chat)
        anon_admin = msg.get("sender_chat", {}).get("id") == chat["id"]
        if not anon_admin and not is_admin(chat["id"], user.get("id")):
            api("sendMessage", chat_id=chat["id"], message_thread_id=msg.get("message_thread_id"),
                text="Команда /post доступна лише адмінам групи.")
            return
        params = dict(chat_id=chat["id"], parse_mode="HTML", text=PINNED_TEXT,
                      reply_markup=play_button("group_krakenua"))
        if msg.get("message_thread_id"):
            params["message_thread_id"] = msg["message_thread_id"]
        sent = api("sendMessage", **params)
        if sent.get("ok"):
            api("pinChatMessage", chat_id=chat["id"],
                message_id=sent["result"]["message_id"], disable_notification=True)
        # прибираємо саму команду /post, щоб не засмічувати гілку
        api("deleteMessage", chat_id=chat["id"], message_id=msg["message_id"])


def main():
    print(f"Бот запущено. Посилання на гру: {GAME_LINK}")
    offset = 0
    while True:
        try:
            upd = api("getUpdates", offset=offset, timeout=30, allowed_updates=["message"])
            for u in upd.get("result", []):
                offset = u["update_id"] + 1
                if "message" in u:
                    handle(u["message"])
        except requests.RequestException as e:
            print("network error:", e)
            time.sleep(3)


if __name__ == "__main__":
    main()
