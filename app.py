import os
import json
import time
import threading
from flask import Flask, render_template_string, request, redirect
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
DATA_FILE = 'replies.json'
STATUS_FILE = 'status.json'

def init_files():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f: json.dump({"hello": "Hi!"}, f)
    if not os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'w') as f: json.dump({"logged_in_user": "None", "status": "Offline"}, f)

init_files()

def get_json(filename):
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return {}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>InstaBot Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; padding: 20px; }
        .container { max-width: 500px; margin: auto; }
        .card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .status-box { padding: 15px; border-radius: 10px; background: #f8f9fa; border-left: 6px solid #0095f6; }
        .error-msg { color: #d93025; font-size: 14px; font-weight: bold; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; background: #0095f6; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>Bot Status</h2>
            <div class="status-box">
                <p>User: <strong>{{ status['logged_in_user'] }}</strong></p>
                <p>Status: <span class="{% if 'Error' in status['status'] %}error-msg{% endif %}">{{ status['status'] }}</span></p>
            </div>
        </div>
        <div class="card">
            <h3>Login Instagram</h3>
            <form action="/login" method="post">
                <input type="text" name="user" placeholder="Username" required>
                <input type="password" name="pass" placeholder="Password" required>
                <button type="submit">Start Bot Session</button>
            </form>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, status=get_json(STATUS_FILE))

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('user')
    pw = request.form.get('pass')
    threading.Thread(target=bot_process, args=(user, pw), daemon=True).start()
    return redirect('/')

def bot_process(user, pw):
    st = get_json(STATUS_FILE)
    st['status'] = "Starting Browser..."
    save_json(STATUS_FILE, st)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    chrome_path = "/opt/render/project/.render/chrome/chrome"
    driver_path = "/opt/render/project/.render/chromedriver"
    
    if os.path.exists(chrome_path): options.binary_location = chrome_path

    try:
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 20)
        
        print("[INFO] Loading Instagram Login Page...")
        driver.get("https://www.instagram.com/accounts/login/")
        
        # এলিমেন্ট আসার জন্য অপেক্ষা করা
        user_input = wait.until(EC.presence_of_element_for_location((By.NAME, "username")))
        pass_input = driver.find_element(By.NAME, "password")
        
        print("[INFO] Entering details...")
        user_input.send_keys(user)
        pass_input.send_keys(pw)
        
        login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_btn.click()
        
        time.sleep(10)
        
        if "login" in driver.current_url.lower():
            st['status'] = "Error: Invalid Credentials or 2FA/Security Check"
        else:
            st['status'] = "Active & Online"
            st['logged_in_user'] = user
            
        save_json(STATUS_FILE, st)
        while True: time.sleep(300)

    except Exception as e:
        st['status'] = f"System Error: Element not found or Timeout"
        print(f"Error: {str(e)}")
        save_json(STATUS_FILE, st)
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
