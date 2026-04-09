import json
import os
import time
from playwright.sync_api import sync_playwright

DATA_FILE = "rules.json"
STATUS_FILE = "status.json"

def load_rules():
    if not os.path.exists(DATA_FILE):
        return {"rules": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_reply(message: str):
    message = message.lower().strip()
    data = load_rules()
    for rule in data.get("rules", []):
        if rule.get("keyword") == "default":
            continue
        keywords = [k.strip() for k in rule["keyword"].split(",")]
        if any(k in message for k in keywords if k):
            return rule["reply"]
    for rule in data.get("rules", []):
        if rule.get("keyword") == "default":
            return rule["reply"]
    return "আমি এখন ব্যস্ত আছি। পরে কথা বলবো। ধন্যবাদ! 😊"

def save_status(status, pairing_code=None):
    data = {"status": status, "pairing_code": pairing_code}
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_status():
    if not os.path.exists(STATUS_FILE):
        return {"status": "disconnected", "pairing_code": None}
    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def start_whatsapp():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="./sessions",
            headless=True,
            viewport={"width": 900, "height": 700},
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer'
            ]
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
        
        print("✅ WhatsApp Web খুলেছে। Pairing Code তৈরি হচ্ছে...")
        time.sleep(15)

        pairing_code = "কোড পাওয়া যায়নি। পেজ রিফ্রেশ করুন।"
        
        try:
            # Pairing code বের করার চেষ্টা
            page.click('button:has-text("Link a device")', timeout=15000)
            time.sleep(8)
            code = page.locator('div[class*="code"]').first.inner_text(timeout=10000)
            pairing_code = code.strip().replace(" ", "")
        except:
            pass

        save_status("pairing_code_ready", pairing_code)
        print(f"✅ Pairing Code: {pairing_code}")

        # অটো রিপ্লাই লুপ
        while True:
            try:
                unread = page.locator('span[aria-label*="unread"]').all()
                for chat in unread[:5]:
                    try:
                        chat.click()
                        time.sleep(2.5)
                        last_msg = page.locator('div.message-in div.copyable-text').last.inner_text()
                        if last_msg:
                            reply = get_reply(last_msg)
                            input_box = page.locator('div[role="textbox"][contenteditable="true"]')
                            input_box.fill(reply)
                            page.keyboard.press("Enter")
                            print(f"✅ রিপ্লাই দেওয়া হয়েছে")
                    except:
                        continue
            except:
                pass
            time.sleep(5)
