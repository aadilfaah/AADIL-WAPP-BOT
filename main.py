from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import json
import uvicorn
from bot import load_rules, start_whatsapp_bot
import threading

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# বট চালানোর জন্য আলাদা থ্রেড
@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=start_whatsapp_bot, daemon=True)
    thread.start()

@app.get("/", response_class=HTMLResponse)
async def admin_panel(request: Request):
    data = load_rules()
    return templates.TemplateResponse("admin.html", {"request": request, "rules": data["rules"]})

@app.post("/add-rule")
async def add_rule(keyword: str = Form(...), reply: str = Form(...)):
    data = load_rules()
    new_id = len(data["rules"]) + 1
    data["rules"].append({
        "id": new_id,
        "keyword": keyword.lower(),
        "reply": reply,
        "is_ai": False
    })
    with open("rules.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return RedirectResponse("/", status_code=303)

@app.post("/delete-rule")
async def delete_rule(rule_id: int = Form(...)):
    data = load_rules()
    data["rules"] = [r for r in data["rules"] if r["id"] != rule_id]
    with open("rules.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return RedirectResponse("/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
