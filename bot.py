import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DATA_FILE = "rules.json"
STATUS_FILE = "status.json"
driver = None

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
    # ডিফল্ট রিপ্লাই
    for rule in data.get("rules", []):
        if rule.get("keyword") == "default":
            return rule["reply"]
    return "আমি এখন ব্যস্ত আছি। পরে কথা বলবো। ধন্যবাদ! 😊"

def save_status(status, pairing_code=None):
    data = {
        "status": status,
        "pairing_code": pairing_code
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_status():
    if not os.path.exists(STATUS_FILE):
        return {"status": "disconnected", "pairing_code": None}
    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def start_whatsapp():
    global driver
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=900,700")
    chrome_options.add_argument("--user-data-dir=./sessions")
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://web.whatsapp.com")
    
    print("🔄 WhatsApp Web লোড হচ্ছে... Pairing Code তৈরির চেষ্টা চলছে")
    time.sleep(15)

    pairing_code = "কোড পাওয়া যায়নি। পেজ রিফ্রেশ করুন।"

    try:
        wait = WebDriverWait(driver, 25)
        # Link with phone number অপশন খোঁজা
        link_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(., "Link a device") or contains(., "pair") or contains(., "phone number")]')))
        link_btn.click()
        time.sleep(8)

        # 8 ডিজিটের কোড বের করা
        code_elements = driver.find_elements(By.XPATH, '//div[contains(@class, "code")] | //span[contains(text(),"8")]/following-sibling::div | //div[contains(text()," ") and string-length(text())=11]')
        for el in code_elements:
            code_text = el.text.strip().replace(" ", "")
            if len(code_text) == 8 and code_text.isdigit():
                pairing_code = code_text
                break
    except:
        pass

    save_status("pairing_code_ready", pairing_code)
    print(f"✅ Pairing Code: {pairing_code}")

    # অটো রিপ্লাই লুপ
    while True:
        try:
            unread_chats = driver.find_elements(By.XPATH, '//span[contains(@aria-label, "unread")]')
            for chat in unread_chats[:5]:
                try:
                    chat.click()
                    time.sleep(2.5)
                    messages = driver.find_elements(By.XPATH, '//div[contains(@class,"message-in")]//div[contains(@class,"copyable-text")]')
                    if messages:
                        last_msg = messages[-1].text.strip()
                        if last_msg:
                            reply_text = get_reply(last_msg)
                            input_box = driver.find_element(By.XPATH, '//div[@contenteditable="true" and @role="textbox"]')
                            input_box.send_keys(reply_text)
                            time.sleep(1)
                            input_box.send_keys("\n")
                            print(f"✅ রিপ্লাই পাঠানো হয়েছে")
                except:
                    continue
        except:
            pass
        time.sleep(5)
