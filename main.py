from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

app = FastAPI()

# Pyrogram client
bot = Client("info_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Serve static files (like index.html)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Start bot on server start
@app.on_event("startup")
async def startup():
    await bot.start()

# Stop bot on server shutdown
@app.on_event("shutdown")
async def shutdown():
    await bot.stop()

# Show index.html at root "/"
@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# API endpoint to fetch user info
@app.get("/get_user_info")
async def get_user_info(username: str):
    try:
        user = await bot.get_users(username)
        return {
            "id": user.id,
            "name": user.first_name,
            "username": user.username,
            "premium": user.is_premium,
            "verified": getattr(user, 'is_verified', False)
        }
    except Exception as e:
        return {"error": str(e)}
