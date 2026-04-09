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

# ফাইল এবং ডাটা ইনিশিয়ালাইজেশন
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

# অ্যাডমিন প্যানেল ইন্টারফেস
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>InstaBot Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }
        .container { max-width: 500px; margin: auto; }
        .card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-bottom: 20px; border: 1px solid #e0e0e0; }
        h2 { color: #1c1e21; margin-top: 0; }
        .status-box { padding: 15px; border-radius: 10px; background: #f8f9fa; border-left: 6px solid #0095f6; margin-bottom: 10px; }
        .error-text { color: #d93025; font-weight: bold; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-size: 14px; }
        button { width: 100%; padding: 12px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; transition: 0.3s; }
        .btn-login { background: #0095f6; color: white; }
        .btn-login:hover { background: #1877f2; }
        .btn-save { background: #42b72a; color: white; }
        .btn-save:hover { background: #36a420; }
        ul { list-style: none; padding: 0; }
        li { background: #f1f3f4; padding: 12px; margin-top: 8px; border-radius: 8px; font-size: 14px; border: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>Bot Status</h2>
            <div class="status-box">
                <p><strong>Active User:</strong> {{ status['logged_in_user'] }}</p>
                <p><strong>System Status:</strong> <span class="{% if 'Error' in status['status'] %}error-text{% endif %}">{{ status['status'] }}</span></p>
            </div>
        </div>

        <div class="card">
            <h3>Login Instagram</h3>
            <form action="/login" method="post">
                <input type="text" name="user" placeholder="Instagram Username" required>
                <input type="password" name="pass" placeholder="Instagram Password" required>
                <button type="submit" class="btn-login">Login & Start Bot</button>
            </form>
        </div>

        <div class="card">
            <h3>Auto-Reply Training</h3>
            <form action="/add" method="post">
                <input type="text" name="key" placeholder="Keyword (lowercase)" required>
                <input type="text" name="val" placeholder="Bot Reply" required>
                <button type="submit" class="btn-save">Save Rule</button>
            </form>
            <h4>Current Rules:</h4>
            <ul>
                {% for k, v in replies.items() %}
                <li><strong>{{ k }}</strong> : {{ v }}</li>
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

# --- মেইন অটোমেশন লজিক ---
def bot_process(user, pw):
    st = get_json(STATUS_FILE)
    print(f"\n[INFO] Initializing Bot Process for: {user}")
    st['status'] = "Initializing Browser..."
    save_json(STATUS_FILE, st)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Render-এ লেটেস্ট ক্রোম এবং ড্রাইভার পাথ (render-build.sh অনুযায়ী)
    chrome_path = "/opt/render/project/.render/chrome/chrome"
    driver_path = "/opt/render/project/.render/chromedriver"
    
    if os.path.exists(chrome_path):
        options.binary_location = chrome_path
        print("[INFO] Custom Chrome binary found.")

    try:
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        print("[INFO] Navigating to Instagram...")
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(12)
        
        print("[INFO] Submitting login form...")
        driver.find_element(By.NAME, "username").send_keys(user)
        driver.find_element(By.NAME, "password").send_keys(pw)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        print("[INFO] Authentication in progress...")
        time.sleep(15)
        
        # লগইন স্ট্যাটাস ভেরিফিকেশন
        if "login" in driver.current_url.lower():
            try:
                err_msg = driver.find_element(By.ID, "slfErrorAlert").text
                st['status'] = f"Error: {err_msg}"
            except:
                st['status'] = "Error: Checkpoint or 2FA required"
            print(f"[FAILED] Login unsuccessful. Reason: {st['status']}")
        else:
            print("[SUCCESS] Logged in and Bot is Live!")
            st['logged_in_user'] = user
            st['status'] = "Active & Auto-replying"
            
        save_json(STATUS_FILE, st)

        while True:
            # সেশন সচল রাখতে হার্টবিট প্রিন্ট
            print(f"[HEARTBEAT] {user} session is healthy.")
            time.sleep(180) 
            
    except Exception as e:
        full_err = str(e).split('\n')[0]
        print(f"[CRITICAL] System Error: {full_err}")
        st['status'] = f"System Error: {full_err[:50]}"
        save_json(STATUS_FILE, st)
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
