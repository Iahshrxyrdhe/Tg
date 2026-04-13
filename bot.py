import telebot
import requests
import os
import time
from flask import Flask
from threading import Thread

# --- CONFIG ---
TOKEN = os.getenv('TG_TOKEN') 
OR_API_KEY = os.getenv('OR_API_KEY') 

bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home(): return "Bot is Online!"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# --- IMAGE GENERATION FUNCTION ---
def send_ai_image(chat_id, prompt):
    try:
        # Prompt ko URL safe banana
        encoded_prompt = requests.utils.quote(prompt)
        seed = int(time.time())
        # Pollinations AI link
        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=1024&height=1024&nologo=true"
        
        # Seedha photo bhejna
        bot.send_photo(chat_id, img_url, caption=f"✨ Prompt: {prompt}")
        return True
    except Exception as e:
        print(f"Image Error: {e}")
        return False

# --- BOT HANDLERS ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot Chalu Hai! \n\nImage ke liye likho: /imagine [prompt]\nChat ke liye bas msg bhejo.")

@bot.message_handler(commands=['imagine'])
def imagine(message):
    msg_text = message.text.split(' ', 1)
    if len(msg_text) < 2:
        bot.reply_to(message, "Bhai, prompt toh likho! Udaharan: /imagine a red car")
        return
    
    prompt = msg_text[1]
    wait_msg = bot.reply_to(message, "🎨 Image ban rahi hai, 10-15 seconds rukein...")
    
    success = send_ai_image(message.chat.id, prompt)
    
    if not success:
        bot.edit_message_text("❌ Image generate nahi ho saki. Dubara try karein.", message.chat.id, wait_msg.message_id)
    else:
        bot.delete_message(message.chat.id, wait_msg.message_id)

@bot.message_handler(content_types=['text', 'photo'])
def chat_handler(message):
    # (Pura chat logic wahi rahega jo pehle diya tha)
    # Bas dhyaan rakhein ki image bhejne par AI response deta hai ya nahi
    bot.reply_to(message, "Main aapka message dekh raha hoon, AI processing on hai...")

if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling()
