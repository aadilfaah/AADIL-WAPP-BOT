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

app = Flask(__name__)
DATA_FILE = 'replies.json'
STATUS_FILE = 'status.json'

def init_files():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({"hello": "Hi!"}, f)
    if not os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'w') as f:
            json.dump({"logged_in_user": "None", "status": "Offline"}, f)

init_files()

def get_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)

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
        body { font-family: 'Segoe UI', sans-serif; background: #fafafa; padding: 20px; }
        .container { max-width: 500px; margin: auto; }
        .card { background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px; }
        .status-box { font-size: 15px; padding: 10px; border-radius: 5px; background: #f0f0f0; border-left: 5px solid #0095f6; }
        .error-msg { color: #d9534f; font-weight: bold; }
        input { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .btn-login { background: #0095f6; color: white; }
        .btn-save { background: #28a745; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>System Status</h2>
            <div class="status-box">
                <p>User: <strong>{{ status['logged_in_user'] }}</strong></p>
                <p>Status: <span class="{% if 'Error' in status['status'] %}error-msg{% endif %}">{{ status['status'] }}</span></p>
            </div>
        </div>

        <div class="card">
            <h3>Login to Instagram</h3>
            <form action="/login" method="post">
                <input type="text" name="user" placeholder="Username" required>
                <input type="password" name="pass" placeholder="Password" required>
                <button type="submit" class="btn-login">Login & Start Bot</button>
            </form>
        </div>

        <div class="card">
            <h3>Auto-Reply Training</h3>
            <form action="/add" method="post">
                <input type="text" name="key" placeholder="If message is..." required>
                <input type="text" name="val" placeholder="Reply with..." required>
                <button type="submit" class="btn-save">Add Rule</button>
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

def bot_process(user, pw):
    st = get_json(STATUS_FILE)
    print(f"[INFO] Bot started for: {user}")
    st['status'] = "Initializing Browser..."
    save_json(STATUS_FILE, st)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Render-এ ক্রোম বাইনারি পাথ সেট করা (আপনার এরর ঠিক করার জন্য)
    chrome_bin = "/opt/render/project/.render/chrome/opt/google/chrome/google-chrome"
    if os.path.exists(chrome_bin):
        options.binary_location = chrome_bin

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        print("[INFO] Loading Instagram...")
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(10)
        
        print("[INFO] Submitting credentials...")
        driver.find_element(By.NAME, "username").send_keys(user)
        driver.find_element(By.NAME, "password").send_keys(pw)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        time.sleep(15)
        
        # লগইন এরর চেক লজিক
        current_url = driver.current_url.lower()
        if "login" in current_url:
            # চেক করা হচ্ছে কোনো এরর মেসেজ দেখা যাচ্ছে কি না
            try:
                error_element = driver.find_element(By.ID, "slfErrorAlert")
                error_text = error_element.text
                st['status'] = f"Error: {error_text}"
            except:
                st['status'] = "Error: Checkpoint/2FA Required"
            
            print(f"[FAILED] {st['status']}")
        else:
            print("[SUCCESS] Logged in!")
            st['logged_in_user'] = user
            st['status'] = "Active & Checking Messages"
            
        save_json(STATUS_FILE, st)

        while True:
            # বটের রিপ্লাই লজিক এখানে চলবে
            time.sleep(120)
            
    except Exception as e:
        err_msg = str(e)[:50] # প্রথম ৫০ অক্ষর দেখাবে
        print(f"[CRITICAL] {err_msg}")
        st['status'] = f"System Error: {err_msg}"
        save_json(STATUS_FILE, st)
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
