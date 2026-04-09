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
STATUS_FILE = 'status.json'

def init_files():
    if not os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'w') as f: json.dump({"logged_in_user": "None", "status": "Offline"}, f)

init_files()

def get_json(filename):
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return {"logged_in_user": "None", "status": "Offline"}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>InstaBot Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f0f2f5; padding: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; max-width: 450px; margin: auto; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .status { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid #0095f6; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #0095f6; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .error { color: #dc3545; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Bot Control Panel</h2>
        <div class="status">
            <p>User: <strong>{{ status['logged_in_user'] }}</strong></p>
            <p>Status: <span class="{% if 'Error' in status['status'] %}error{% endif %}">{{ status['status'] }}</span></p>
        </div>
        <form action="/login" method="post">
            <input type="text" name="user" placeholder="Instagram Username" required>
            <input type="password" name="pass" placeholder="Instagram Password" required>
            <button type="submit">Start Bot Process</button>
        </form>
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
    st['status'] = "Initializing Browser..."
    save_json(STATUS_FILE, st)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Render পাথ সেটআপ (render-build.sh অনুযায়ী)
    chrome_path = "/opt/render/project/.render/chrome/chrome"
    driver_path = "/opt/render/project/.render/chromedriver"
    
    if os.path.exists(chrome_path):
        options.binary_location = chrome_path

    try:
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 20)
        
        print(f"[INFO] Bot starting for {user}...")
        driver.get("https://www.instagram.com/accounts/login/")
        
        # এলিমেন্ট খোঁজা (Explicit Wait)
        user_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        user_field.send_keys(user)
        driver.find_element(By.NAME, "password").send_keys(pw)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        time.sleep(15)
        
        if "login" in driver.current_url.lower():
            st['status'] = "Error: Invalid Login or Security Check"
        else:
            st['status'] = "Active & Online"
            st['logged_in_user'] = user
            
        save_json(STATUS_FILE, st)
        while True:
            time.sleep(300)

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        st['status'] = f"Error: {str(e)[:50]}"
        save_json(STATUS_FILE, st)
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
