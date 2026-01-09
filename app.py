from flask import Flask, render_template_string, request, redirect
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import threading
import time

TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789  # твой Telegram ID

# глобальный переключатель
bot_enabled = True
active_chats = set()

app = Flask(__name__)

# HTML интерфейс
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head><title>Управление ботом</title></head>
<body style="font-family:Arial; background:#222; color:#fff; text-align:center; padding:50px;">
    <h2>Глобальный выключатель бота</h2>
    <p>Состояние: <b>{{ 'Включен' if bot_enabled else 'Выключен' }}</b></p>
    <form method="post">
        {% if bot_enabled %}
            <button type="submit" name="action" value="off">Выключить</button>
        {% else %}
            <button type="submit" name="action" value="on">Включить</button>
        {% endif %}
    </form>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    global bot_enabled
    if request.method == "POST":
        action = request.form.get("action")
        if action == "on":
            bot_enabled = True
        elif action == "off":
            bot_enabled = False
    return render_template_string(HTML_PAGE, bot_enabled=bot_enabled)

# Telegram‑бот
def start(update, context):
    user = update.effective_user
    info = f"""
👤 ID: {user.id}
🌐 Username: @{user.username if user.username else "нет"}
🗣 Язык интерфейса: {user.language_code}
"""
    update.message.reply_text("Привет! Вот твоя информация:\n" + info)
    # Отчёт админу
    context.bot.send_message(chat_id=ADMIN_ID, text=f"📩 Новый пользователь: {info}")

def group_control(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    if text == "!on":
        active_chats.add(chat_id)
        update.message.reply_text("✅ Рассылка включена в этом чате.")
    elif text == "!off":
        active_chats.discard(chat_id)
        update.message.reply_text("⛔ Рассылка выключена.")

def spam_loop(bot):
    while True:
        time.sleep(10)
        if bot_enabled:  # проверяем глобальный выключатель
            for chat_id in list(active_chats):
                bot.send_message(chat_id=chat_id, text="🔔 Рабочее уведомление!")

def run_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & Filters.chat_type.groups, group_control))
    threading.Thread(target=spam_loop, args=(updater.bot,), daemon=True).start()
    updater.start_polling()

if __name__ == "__main__":
    # Запускаем Flask и бота параллельно
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
