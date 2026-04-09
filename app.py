import os
import json
import time
import threading
from flask import Flask, render_template_string, request, redirect
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
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
<head><title>Bot Admin</title><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:sans-serif;background:#f0f2f5;padding:20px;}.card{background:white;padding:25px;border-radius:15px;max-width:400px;margin:auto;box-shadow:0 4px 12px rgba(0,0,0,0.1);}.status{background:#f8f9fa;padding:15px;border-radius:10px;margin-bottom:20px;border-left:5px solid #0095f6;}</style>
</head>
<body>
    <div class="card">
        <h2>Bot Control</h2>
        <div class="status">
            <p>User: {{ status['logged_in_user'] }}</p>
            <p>Status: {{ status['status'] }}</p>
        </div>
        <form action="/login" method="post">
            <input type="text" name="user" placeholder="Username" style="width:100%;padding:12px;margin-bottom:10px;border-radius:8px;border:1px solid #ddd;" required>
            <input type="password" name="pass" placeholder="Password" style="width:100%;padding:12px;margin-bottom:10px;border-radius:8px;border:1px solid #ddd;" required>
            <button type="submit" style="width:100%;padding:12px;background:#0095f6;color:white;border:none;border-radius:8px;font-weight:bold;">Login & Start</button>
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
    st['status'] = "Launching Stealth Browser..."
    save_json(STATUS_FILE, st)

    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        # undetected_chromedriver নিজে থেকেই সব সেটআপ করে নেবে
        driver = uc.Chrome(options=options)
        wait = WebDriverWait(driver, 25)
        
        driver.get("https://www.instagram.com/accounts/login/")
        
        user_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        user_field.send_keys(user)
        driver.find_element(By.NAME, "password").send_keys(pw)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        time.sleep(15)
        
        if "login" in driver.current_url.lower():
            st['status'] = "Error: Blocked/Invalid Login"
        else:
            st['status'] = "Active & Online"
            st['logged_in_user'] = user
            
        save_json(STATUS_FILE, st)
        while True: time.sleep(300)

    except Exception as e:
        st['status'] = f"Error: {str(e)[:50]}"
        save_json(STATUS_FILE, st)
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
