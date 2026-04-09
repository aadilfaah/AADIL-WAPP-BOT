import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

DATA_FILE = "rules.json"

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
    return "আমি এখন ব্যস্ত আছি। পরে কথা বলবো। 😊"

def start_whatsapp_bot():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=800,600")
    chrome_options.add_argument("--user-data-dir=./sessions")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    driver.get("https://web.whatsapp.com")
    print("✅ WhatsApp Web খুলছে... প্রথমবার QR স্ক্যান করুন")
    time.sleep(25)   # QR স্ক্যানের জন্য সময়

    print("🤖 বট চালু হয়েছে!")

    while True:
        try:
            # আনরিড চ্যাট খোঁজা (Selenium XPath)
            unread_chats = driver.find_elements("xpath", '//div[contains(@class, "message-in")]//span[contains(@aria-label, "unread")]')
            
            for chat in unread_chats[:3]:
                try:
                    chat.click()
                    time.sleep(3)
                    
                    messages = driver.find_elements("xpath", '//div[contains(@class, "message-in")]//div[contains(@class, "copyable-text")]')
                    if messages:
                        last_msg = messages[-1].text.strip()
                        if last_msg:
                            reply_text = get_reply(last_msg)
                            input_box = driver.find_element("xpath", '//div[@contenteditable="true" and @role="textbox"]')
                            input_box.send_keys(reply_text)
                            time.sleep(1)
                            input_box.send_keys("\n")   # Enter
                            print(f"✅ রিপ্লাই পাঠানো হয়েছে")
                except:
                    continue
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(5)
