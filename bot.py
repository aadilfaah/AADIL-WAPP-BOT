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
        if rule["keyword"] == "default":
            continue
        keywords = [k.strip() for k in rule["keyword"].split(",")]
        if any(k in message for k in keywords if k):
            return rule["reply"]
    
    # ডিফল্ট রিপ্লাই
    for rule in data["rules"]:
        if rule["keyword"] == "default":
            return rule["reply"]
    return "আমি এখন ব্যস্ত আছি। পরে কথা বলবো।"

def start_whatsapp_bot():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="sessions",
            headless=False,
            viewport={"width": 1200, "height": 800}
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
        
        print("✅ WhatsApp Web খুলছে... QR কোড স্ক্যান করুন (প্রথমবার)")
        input("QR স্ক্যান হয়ে গেলে Enter চাপুন...")

        print("🤖 বট চালু হয়েছে! অটো রিপ্লাই চলছে...")

        while True:
            try:
                # আনরিড চ্যাট খুঁজে বের করা
                unread = page.locator('div[role="listitem"] span[aria-label*="unread message"]').all()
                
                for chat in unread[:3]:  # একবারে সর্বোচ্চ ৩টা
                    try:
                        chat.click()
                        time.sleep(2)
                        
                        # লাস্ট মেসেজ নেওয়া
                        messages = page.locator('div.message-in div.copyable-text').all()
                        if messages:
                            last_msg = messages[-1].inner_text().strip()
                            
                            if last_msg:
                                reply_text = get_reply(last_msg)
                                # রিপ্লাই পাঠানো
                                input_box = page.locator('div[role="textbox"][contenteditable="true"]')
                                input_box.fill(reply_text)
                                page.keyboard.press("Enter")
                                print(f"✅ রিপ্লাই দেওয়া হয়েছে: {last_msg[:30]}...")
                                
                        time.sleep(1)
                    except:
                        continue
                        
            except Exception as e:
                print(f"Error: {e}")
            
            time.sleep(4)
