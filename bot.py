import json
import os
import time
from playwright.sync_api import sync_playwright

DATA_FILE = "rules.json"

def load_rules():
    if not os.path.exists(DATA_FILE):
        return {"rules": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_reply(message: str):
    message = message.lower().strip()
    data = load_rules()
    for rule in data["rules"]:
        if rule.get("keyword") == "default":
            continue
        keywords = [k.strip() for k in rule["keyword"].split(",")]
        if any(k in message for k in keywords if k):
            return rule["reply"]
    for rule in data["rules"]:
        if rule.get("keyword") == "default":
            return rule["reply"]
    return "আমি এখন ব্যস্ত আছি। পরে কথা বলবো। 😊"

def start_whatsapp_bot():
    with sync_playwright() as p:
        # Render-এর জন্য extra args
        context = p.chromium.launch_persistent_context(
            user_data_dir="./sessions",
            headless=True,                    # Render-এ headless=True রাখো
            viewport={"width": 800, "height": 600},
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
        
        print("✅ WhatsApp Web লোড হয়েছে। প্রথমবার QR স্ক্যান করতে হবে।")
        # প্রথমবার ম্যানুয়ালি QR স্ক্যান করার জন্য অপেক্ষা
        time.sleep(30)
        
        print("🤖 Auto Reply Bot চালু হয়েছে (Render-এ 24/7)")

        while True:
            try:
                unread_chats = page.locator('div[role="listitem"] span[aria-label*="unread"]').all()
                for chat in unread_chats[:5]:
                    try:
                        chat.click()
                        time.sleep(3)
                        
                        messages = page.locator('div.message-in div.copyable-text').all()
                        if messages:
                            last_msg = messages[-1].inner_text().strip()
                            if last_msg:
                                reply_text = get_reply(last_msg)
                                input_box = page.locator('div[role="textbox"][contenteditable="true"]')
                                input_box.fill(reply_text)
                                page.keyboard.press("Enter")
                                print(f"✅ রিপ্লাই: {last_msg[:40]}...")
                        time.sleep(1.5)
                    except:
                        continue
            except Exception as e:
                print(f"Error: {e}")
            
            time.sleep(5)
