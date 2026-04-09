import os
import json
import time
import threading
from flask import Flask, render_template_string, request, redirect
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
STATUS_FILE = 'status.json'

def init_files():
    if not os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'w') as f:
            json.dump({"logged_in_user": "None", "status": "Offline"}, f)

init_files()

def get_json(filename):
    with open(filename, 'r') as f: return json.load(f)

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>InstaBot Firefox Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f4f7f6; padding: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 450px; margin: auto; }
        .status { padding: 10px; background: #e9ecef; border-radius: 5px; margin-bottom: 20px; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .error { color: #dc3545; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Firefox Bot Status</h2>
        <div class="status">
            <p>User: <strong>{{ status['logged_in_user'] }}</strong></p>
            <p>Status: <span class="{% if 'Error' in status['status'] %}error{% endif %}">{{ status['status'] }}</span></p>
        </div>
        <form action="/login" method="post">
            <input type="text" name="user" placeholder="Instagram Username" required>
            <input type="password" name="pass" placeholder="Password" required>
            <button type="submit">Login & Start (Firefox)</button>
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
    st['status'] = "Launching Firefox..."
    save_json(STATUS_FILE, st)

    options = Options()
    options.add_argument("--headless")
    
    # রেন্ডার পাথ সেটআপ
    firefox_bin = "/opt/render/project/.render/firefox/firefox"
    gecko_bin = "/opt/render/project/.render/geckodriver"
    
    options.binary_location = firefox_bin
    service = Service(executable_path=gecko_bin)

    try:
        driver = webdriver.Firefox(service=service, options=options)
        wait = WebDriverWait(driver, 30)
        
        print("[INFO] Firefox Started. Loading Instagram...")
        driver.get("https://www.instagram.com/accounts/login/")
        
        # এলিমেন্ট খোঁজার জন্য শক্তিশালী ওয়েট
        user_field = wait.until(EC.visibility_of_element_located((By.NAME, "username")))
        pass_field = driver.find_element(By.NAME, "password")
        
        user_field.send_keys(user)
        pass_field.send_keys(pw)
        
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(15)
        
        if "login" in driver.current_url.lower():
            st['status'] = "Error: Login Blocked or Invalid"
            print("[FAILED] Still on login page.")
        else:
            st['status'] = "Active (Firefox Online)"
            st['logged_in_user'] = user
            print("[SUCCESS] Logged in!")
            
        save_json(STATUS_FILE, st)
        while True: time.sleep(300)

    except Exception as e:
        print(f"Error: {str(e)}")
        st['status'] = "Error: Connection Timeout"
        save_json(STATUS_FILE, st)
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
