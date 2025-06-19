from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pyrogram import Client
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Env variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = FastAPI()

# Pyrogram client
bot = Client("info_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Start bot on server start
@app.on_event("startup")
async def startup():
    await bot.start()

# Stop bot on server shutdown
@app.on_event("shutdown")
async def shutdown():
    await bot.stop()

# Load index.html
@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

def calculate_account_age(creation_date):
    today = datetime.now()
    delta = relativedelta(today, creation_date)
    years = delta.years
    months = delta.months
    days = delta.days
    return f"{years} years, {months} months, {days} days"

def estimate_account_creation_date(user_id: int):
    # This is approximate based on user id ranges
    reference_points = [
        (100000000, datetime(2013, 8, 1)),
        (1273841502, datetime(2020, 8, 13)),
        (1500000000, datetime(2021, 5, 1)),
        (2000000000, datetime(2022, 12, 1)),
    ]
    closest_point = min(reference_points, key=lambda x: abs(x[0] - user_id))
    closest_user_id, closest_date = closest_point
    id_diff = user_id - closest_user_id
    days_diff = id_diff / 20000000  # Adjust this value as needed
    return closest_date + relativedelta(days=+days_diff)

# API endpoint to fetch user info with scam/fake flags
@app.get("/get_user_info")
async def get_user_info(username: str = Query(..., description="Telegram username")):
    try:
        user = await bot.get_users(username)

        # Estimate account creation date (approximate)
        account_created = estimate_account_creation_date(user.id)
        account_created_str = account_created.strftime("%B %d, %Y")
        account_age = calculate_account_age(account_created)

        # Get scam/fake flags safely
        is_scam = getattr(user, "is_scam", False)
        is_fake = getattr(user, "is_fake", False)

        # Get premium and verified status
        is_premium = user.is_premium if hasattr(user, "is_premium") else False
        is_verified = getattr(user, "is_verified", False)

        # User status string (simplified)
        status = "Unknown"
        if hasattr(user, "status"):
            status = str(user.status).split(".")[-1].replace("_", " ").title()

        return {
            "full_name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
            "user_id": user.id,
            "username": f"@{user.username}" if user.username else "No username",
            "chat_id": user.id,
            "premium": "Yes" if is_premium else "No",
            "verified": "Yes" if is_verified else "No",
            "status": status,
            "account_created_on": account_created_str,
            "account_age": account_age,
            "is_scam": is_scam,
            "is_fake": is_fake,
        }
    except Exception as e:
        return {"error": str(e)}
