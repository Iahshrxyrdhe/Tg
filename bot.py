import telebot
import requests
import base64
import os
from flask import Flask
from threading import Thread

# --- CONFIG ---
TOKEN = os.getenv('TG_TOKEN') 
OR_API_KEY = os.getenv('OR_API_KEY') 
CHAT_MODEL = "google/gemini-2.0-flash-001" 

bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home(): return "Vision AI Bot is Online!"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# --- HELPER: AI SE JAWAB LENA ---
def get_ai_response(text, img_b64=None):
    headers = {
        "Authorization": f"Bearer {OR_API_KEY}",
        "Content-Type": "application/json"
    }
    
    content_list = [{"type": "text", "text": text}]
    if img_b64:
        content_list.append({
            "type": "image_url", 
            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
        })
    
    payload = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful AI. Answer in Hinglish. Be concise."},
            {"role": "user", "content": content_list}
        ]
    }

    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        else:
            return f"❌ API Error: {r.status_code}"
    except Exception as e:
        return f"⚠️ Connection Error: {str(e)}"

# --- HANDLERS ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Namaste! Main taiyaar hoon.\n\n💬 Mujhe msg bhejein ya\n🖼️ Koi photo bhej kar uske baare mein puchein.")

@bot.message_handler(content_types=['text', 'photo'])
def handle_all(message):
    chat_id = message.chat.id
    user_text = message.text or message.caption or "Is image ko describe karo."
    
    if message.text and message.text.startswith('/'): return

    status = bot.reply_to(message, "🤔 Soch raha hoon...")

    img_b64 = None
    if message.content_type == 'photo':
        try:
            # Photo download karna
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            # Base64 mein convert karna Gemini ke liye
            img_b64 = base64.b64encode(downloaded_file).decode('utf-8')
        except Exception as e:
            bot.edit_message_text(f"❌ Photo download fail: {e}", chat_id, status.message_id)
            return

    # AI se jawab mangna
    response = get_ai_response(user_text, img_b64)
    
    # Jawab bhejna
    bot.edit_message_text(response, chat_id, status.message_id)

if __name__ == '__main__':
    keep_alive()
    bot.remove_webhook()
    print("Vision Bot Started!")
    bot.infinity_polling(skip_pending=True)
