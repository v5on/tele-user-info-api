from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pyrogram import Client
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from config import API_ID, API_HASH, BOT_TOKEN

app = FastAPI()

bot = Client("info_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

app.mount("/static", StaticFiles(directory="static"), name="static")

def estimate_account_creation_date(user_id: int) -> datetime:
    reference_points = [
        (100000000, datetime(2013, 8, 1)),
        (1273841502, datetime(2020, 8, 13)),
        (1500000000, datetime(2021, 5, 1)),
        (2000000000, datetime(2022, 12, 1)),
    ]
    closest_point = min(reference_points, key=lambda x: abs(x[0] - user_id))
    closest_user_id, closest_date = closest_point
    id_diff = user_id - closest_user_id
    days_diff = id_diff / 20000000
    estimated_date = closest_date + timedelta(days=days_diff)
    return estimated_date

def calculate_account_age(creation_date: datetime) -> str:
    now = datetime.now()
    diff = relativedelta(now, creation_date)
    return f"{diff.years} years, {diff.months} months, {diff.days} days"

@app.on_event("startup")
async def startup():
    await bot.start()

@app.on_event("shutdown")
async def shutdown():
    await bot.stop()

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/get_user_info", response_class=PlainTextResponse)
async def get_user_info(username: str):
    try:
        user = await bot.get_users(username)

        creation_date = estimate_account_creation_date(user.id)
        account_age = calculate_account_age(creation_date)

        # স্ট্যাটাস (যদি থাকে)
        status = "Unknown"
        if user.status:
            status_str = str(user.status).upper()
            if "ONLINE" in status_str:
                status = "Online"
            elif "OFFLINE" in status_str:
                status = "Offline"
            elif "RECENTLY" in status_str:
                status = "Recently online"
            elif "LAST_WEEK" in status_str:
                status = "Last seen within week"
            elif "LAST_MONTH" in status_str:
                status = "Last seen within month"

        # প্রোফাইল পিকচার URL (যদি থাকে এবং ইউজারনেম থাকে)
        profile_pic_url = f"https://t.me/i/userpic/320/{user.username}.jpg" if (user.photo and user.username) else "No Profile Picture"

        response_text = f"""
✘《 User Information ↯ 》
↯ Full Name: {user.first_name or ''} {user.last_name or ''}
↯ User ID: {user.id}
↯ Username: @{user.username if user.username else 'No username'}
↯ Chat Id: {user.id}
↯ Premium User: {"Yes" if user.is_premium else "No"}
↯ Verified: {"Yes" if getattr(user, 'is_verified', False) else "No"}
↯ Status: {status}
↯ Account Created On: {creation_date.strftime('%b %d, %Y')}
↯ Account Age: {account_age}

↯ Profile Picture URL: {profile_pic_url}
"""
        return response_text.strip()

    except Exception as e:
        return f"Error: {str(e)}"
