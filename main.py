from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import threading
import os
from bot import start_whatsapp_bot, load_rules

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# বট চালানো
@app.on_event("startup")
async def startup_event():
    thread = threading.Thread(target=start_whatsapp_bot, daemon=True)
    thread.start()

@app.get("/", response_class=HTMLResponse)
async def admin_panel(request: Request):
    data = load_rules()
    return templates.TemplateResponse("admin.html", {"request": request, "rules": data.get("rules", [])})

# Add & Delete route আগের মতোই রাখো...
@app.post("/add-rule")
async def add_rule(keyword: str = Form(...), reply: str = Form(...)):
    # আগের কোড অনুসারে যোগ করো
    data = load_rules()
    new_id = len(data.get("rules", [])) + 1
    if "rules" not in data:
        data["rules"] = []
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
    data["rules"] = [r for r in data.get("rules", []) if r["id"] != rule_id]
    with open("rules.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return RedirectResponse("/", status_code=303)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
