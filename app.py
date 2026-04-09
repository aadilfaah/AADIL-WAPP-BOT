import os
import json
import time
import threading
from flask import Flask, render_template_string, request, redirect
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

app = Flask(__name__)
DATA_FILE = 'replies.json'
STATUS_FILE = 'status.json'

# ফাইল তৈরি এবং ডাটা লোড
def init_files():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({"hello": "Hi! How can I help?"}, f)
    if not os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'w') as f:
            json.dump({"logged_in_user": "None", "status": "Offline"}, f)

init_files()

def get_json(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)

# অ্যাডমিন প্যানেল UI
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>InstaBot Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; padding: 20px; color: #1c1e21; }
        .container { max-width: 500px; margin: auto; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px; border: 1px solid #ddd; }
        .status-box { padding: 15px; border-radius: 8px; background: #f8f9fa; border-left: 6px solid #0095f6; }
        .error { color: #dc3545; font-weight: bold; font-size: 14px; margin-top: 10px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; transition: 0.3s; }
        .btn-blue { background: #0095f6; color: white; }
        .btn-blue:hover { background: #1877f2; }
        .btn-green { background: #42b72a; color: white; margin-top: 10px; }
        ul { list-style: none; padding: 0; }
        li { background: #f1f3f4; padding: 10px; margin-top: 5px; border-radius: 6px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2 style="margin-top:0;">System Status</h2>
            <div class="status-box">
                <p><strong>Logged User:</strong> {{ status['logged_in_user'] }}</p>
                <p><strong>Bot Status:</strong> {{ status['status'] }}</p>
            </div>
        </div>

        <div class="card">
            <h3>Login Instagram</h3>
            <form action="/login" method="post">
                <input type="text" name="user" placeholder="Instagram Username" required>
                <input type="password" name="pass" placeholder="Instagram Password" required>
                <button type="submit" class="btn-blue">Start Bot Session</button>
            </form>
        </div>

        <div class="card">
            <h3>Training & Rules</h3>
            <form action="/add" method="post">
                <input type="text" name="key" placeholder="Keyword (e.g. hello)" required>
                <input type="text" name="val" placeholder="Reply (e.g. Hi there!)" required>
                <button type="submit" class="btn-green">Save Rule</button>
            </form>
            <h4>Current Rules:</h4>
            <ul>
                {% for k, v in replies.items() %}
                <li><strong>{{ k }}</strong>: {{ v }}</li>
                {% endfor %}
            </ul>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, replies=get_json(DATA_FILE), status=get_json(STATUS_FILE))

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('user')
    pw = request.form.get('pass')
    threading.Thread(target=bot_process, args=(user, pw), daemon=True).start()
    return redirect('/')

@app.route('/add', methods=['POST'])
def add():
    key = request.form.get('key').lower()
    val = request.form.get('val')
    data = get_json(DATA_FILE)
    data[key] = val
    save_json(DATA_FILE, data)
    return redirect('/')

# --- মেইন অটোমেশন ইঞ্জিন ---
def bot_process(user, pw):
    st = get_json(STATUS_FILE)
    print(f"\n[INFO] Initializing bot for: {user}")
    st['status'] = "Initializing Browser..."
    save_json(STATUS_FILE, st)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Render-এ ম্যানুয়ালি ইনস্টল করা ক্রোমের পাথ সেটআপ
    chrome_bin = "/opt/render/project/.render/chrome/opt/google/chrome/google-chrome"
    if os.path.exists(chrome_bin):
        options.binary_location = chrome_bin
        print("[INFO] Chrome binary found at custom path.")

    try:
        # WebDriver Manager ব্যবহার করে অটোমেটিক ড্রাইভার সেটআপ
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print("[INFO] Navigating to Instagram...")
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(10)
        
        print("[INFO] Typing credentials...")
        driver.find_element(By.NAME, "username").send_keys(user)
        driver.find_element(By.NAME, "password").send_keys(pw)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        print("[INFO] Waiting for result...")
        time.sleep(15)
        
        # লগইন স্ট্যাটাস চেক
        if "login" in driver.current_url.lower():
            try:
                # ভুল পাসওয়ার্ড বা অন্য এরর মেসেজ খুঁজা
                err_element = driver.find_element(By.ID, "slfErrorAlert")
                st['status'] = f"Login Failed: {err_element.text}"
            except:
                st['status'] = "Login Failed: Checkpoint/2FA triggered"
            print(f"[FAILED] {st['status']}")
        else:
            print("[SUCCESS] Bot is now online!")
            st['logged_in_user'] = user
            st['status'] = "Active & Auto-replying"
        
        save_json(STATUS_FILE, st)

        while True:
            # এখানে ফিউচার মেসেজ লজিক থাকবে
            print(f"[ALIVE] {user} session active...")
            time.sleep(180) # প্রতি ৩ মিনিটে একটি হার্টবিট লগ দিবে
            
    except Exception as e:
        error_msg = str(e).split('\n')[0] # প্রথম লাইনের এরর মেসেজ নিবে
        print(f"[CRITICAL] {error_msg}")
        st['status'] = f"System Error: {error_msg}"
        save_json(STATUS_FILE, st)
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
