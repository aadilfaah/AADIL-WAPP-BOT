import os
import json
import time
import threading
from flask import Flask, render_template_string, request, redirect
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

app = Flask(__name__)
DATA_FILE = 'replies.json'
STATUS_FILE = 'status.json'

# ফাইল ম্যানেজমেন্ট
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

# অ্যাডমিন প্যানেল ডিজাইন
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>InstaBot Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; padding: 20px; }
        .container { max-width: 500px; margin: auto; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .status-box { padding: 15px; border-radius: 8px; background: #f8f9fa; border-left: 6px solid #0095f6; }
        .error { color: #dc3545; font-weight: bold; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .btn-blue { background: #0095f6; color: white; }
        .btn-green { background: #42b72a; color: white; margin-top: 10px; }
        ul { list-style: none; padding: 0; }
        li { background: #f1f3f4; padding: 10px; margin-top: 5px; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>System Status</h2>
            <div class="status-box">
                <p><strong>User:</strong> {{ status['logged_in_user'] }}</p>
                <p><strong>Status:</strong> <span class="{% if 'Error' in status['status'] %}error{% endif %}">{{ status['status'] }}</span></p>
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
                <input type="text" name="key" placeholder="Keyword" required>
                <input type="text" name="val" placeholder="Reply" required>
                <button type="submit" class="btn-green">Save Rule</button>
            </form>
            <h4>Rules List:</h4>
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

# --- অটোমেশন ইঞ্জিন ---
def bot_process(user, pw):
    st = get_json(STATUS_FILE)
    print(f"\n[INFO] Starting bot for: {user}")
    st['status'] = "Initializing Browser..."
    save_json(STATUS_FILE, st)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Render-এ ডাউনলোড করা ক্রোম এবং ড্রাইভার পাথ
    chrome_path = "/opt/render/project/.render/chrome/chrome"
    driver_path = "/opt/render/project/.render/chromedriver"
    
    if os.path.exists(chrome_path):
        options.binary_location = chrome_path
        print("[INFO] Manual Chrome binary set.")

    try:
        # সরাসরি পাথ দিয়ে সার্ভিস চালু করা (ভার্সন সমস্যা এড়াতে)
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        print("[INFO] Loading Instagram Login...")
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(10)
        
        driver.find_element(By.NAME, "username").send_keys(user)
        driver.find_element(By.NAME, "password").send_keys(pw)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        print("[INFO] Authenticating...")
        time.sleep(15)
        
        if "login" in driver.current_url.lower():
            try:
                err = driver.find_element(By.ID, "slfErrorAlert").text
                st['status'] = f"Login Error: {err}"
            except:
                st['status'] = "Error: 2FA or Security Check needed"
        else:
            print("[SUCCESS] Bot is online!")
            st['logged_in_user'] = user
            st['status'] = "Active & Running"
        
        save_json(STATUS_FILE, st)

        while True:
            # বট সেশন বজায় রাখা
            print(f"[ALIVE] {user} is active.")
            time.sleep(180)
            
    except Exception as e:
        error_msg = str(e).split('\n')[0]
        print(f"[CRITICAL] {error_msg}")
        st['status'] = f"System Error: {error_msg}"
        save_json(STATUS_FILE, st)
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
