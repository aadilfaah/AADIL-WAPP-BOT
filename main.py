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

# ডাটা ফাইল ইনিশিয়ালাইজ করা
def init_files():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({"hello": "Hi! How can I help?"}, f)
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

# অ্যাডমিন প্যানেল ডিজাইন
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>InstaBot Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #fafafa; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: auto; }
        .card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #dbdbdb; margin-bottom: 20px; }
        h2, h3 { color: #262626; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #dbdbdb; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .btn-blue { background: #0095f6; color: white; }
        .btn-green { background: #47b347; color: white; }
        .status { color: #8e8e8e; font-size: 14px; }
        ul { list-style: none; padding: 0; }
        li { background: #efefef; padding: 10px; margin-bottom: 5px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>Account Info</h2>
            <p class="status">User: <strong>{{ status['logged_in_user'] }}</strong></p>
            <p class="status">Bot Status: <strong>{{ status['status'] }}</strong></p>
        </div>

        <div class="card">
            <h3>Login Instagram</h3>
            <form action="/login" method="post">
                <input type="text" name="user" placeholder="Username" required>
                <input type="password" name="pass" placeholder="Password" required>
                <button type="submit" class="btn-blue">Start & Login</button>
            </form>
        </div>

        <div class="card">
            <h3>Train Bot</h3>
            <form action="/add" method="post">
                <input type="text" name="key" placeholder="Keyword (e.g. price)" required>
                <input type="text" name="val" placeholder="Reply (e.g. It is $10)" required>
                <button type="submit" class="btn-green">Save Rule</button>
            </form>
            <h4>Rules:</h4>
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

# বটের কাজ
def bot_process(user, pw):
    st = get_json(STATUS_FILE)
    st['status'] = "Logging in..."
    save_json(STATUS_FILE, st)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get("https://www.instagram.com/")
        time.sleep(10)
        
        driver.find_element(By.NAME, "username").send_keys(user)
        driver.find_element(By.NAME, "password").send_keys(pw)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        time.sleep(15)
        
        st['logged_in_user'] = user
        st['status'] = "Running (Active)"
        save_json(STATUS_FILE, st)

        while True:
            # এখানে মেসেজ চেক ও রিপ্লাই দেওয়ার লজিক কাজ করবে
            time.sleep(60)
            
    except Exception as e:
        st['status'] = "Error: Login Failed"
        save_json(STATUS_FILE, st)
    finally:
        driver.quit()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
