import telebot
import requests
import base64
import os
import time
from flask import Flask
from threading import Thread

# --- CONFIG ---
TOKEN = os.getenv('TG_TOKEN') 
OR_API_KEY = os.getenv('OR_API_KEY') 

# Models
CHAT_MODEL = "google/gemini-2.0-flash-001" 
IMAGE_GEN_API = "https://image.pollinations.ai/prompt/" 

# Parse mode ko None rakha hai taaki symbols se error na aaye
bot = telebot.TeleBot(TOKEN)
app = Flask('')

# --- WEB SERVER (For Render 24/7) ---
@app.route('/')
def home(): return "Multi-AI Bot is Running!"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# --- HELPERS ---
def generate_image(prompt):
    encoded_prompt = requests.utils.quote(prompt)
    seed = int(time.time())
    final_url = f"{IMAGE_GEN_API}{encoded_prompt}?seed={seed}&width=1024&height=1024&nologo=true"
    return final_url

# --- BOT LOGIC ---

@bot.message_handler(commands=['start'])
def start(message):
    welcome = (
        "Namaste! Main hoon aapka Multi-AI Bot.\n\n"
        "1. Kuch bhi puchhein (Text ya Photo).\n"
        "2. Image banane ke liye likhein: /imagine [aapka prompt]"
    )
    bot.reply_to(message, welcome)

@bot.message_handler(commands=['imagine'])
def imagine(message):
    try:
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Please use: /imagine your prompt")
            return
        
        prompt = parts[1]
        status = bot.reply_to(message, "🎨 Image bana raha hoon, thoda sabr rakhein...")
        
        img_url = generate_image(prompt)
        bot.send_photo(message.chat.id, img_url, caption=f"✨ Prompt: {prompt}")
        bot.delete_message(message.chat.id, status.message_id)
    except Exception as e:
        bot.reply_to(message, f"❌ Image error: {str(e)}")

@bot.message_handler(content_types=['text', 'photo'])
def handle_all(message):
    chat_id = message.chat.id
    user_text = message.text or message.caption or "Analyze this image"
    
    if user_text.startswith('/'): return

    status = bot.reply_to(message, "🤔 Soch raha hoon...")

    img_b64 = None
    if message.content_type == 'photo':
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            img_b64 = base64.b64encode(downloaded_file).decode('utf-8')
        except Exception as e:
            bot.edit_message_text(f"❌ Photo download error: {e}", chat_id, status.message_id)
            return

    headers = {"Authorization": f"Bearer {OR_API_KEY}", "Content-Type": "application/json"}
    
    content_list = [{"type": "text", "text": user_text}]
    if img_b64:
        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})
    
    payload = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "You are a smart AI. Reply in friendly Hindi-English mix. Don't use complex markdown."},
            {"role": "user", "content": content_list}
        ]
    }

    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            ai_reply = r.json()['choices'][0]['message']['content']
            # Bina kisi parse_mode ke bhej rahe hain taaki crash na ho
            bot.edit_message_text(ai_reply, chat_id=chat_id, message_id=status.message_id)
        else:
            bot.edit_message_text(f"❌ API Error: {r.status_code}", chat_id, status.message_id)
    except Exception as e:
        # Agar text mein koi issue ho toh plain text bhej do
        bot.edit_message_text(f"⚠️ Connect nahi ho paya: {str(e)}", chat_id, status.message_id)

if __name__ == '__main__':
    keep_alive()
    print("Bot is alive!")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
