import os
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pyrogram import Client
from pyrogram.types import User
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from config import API_ID, API_HASH, BOT_TOKEN


app = FastAPI()
bot = Client("info_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

app.mount("/static", StaticFiles(directory="static"), name="static")

DC_LOCATIONS = {
    1: "MIA, Miami, USA, US",
    2: "AMS, Amsterdam, Netherlands, NL",
    3: "SFO, San Francisco, USA, US",
    4: "GRU, São Paulo, Brazil, BR",
    5: "DME, Moscow, Russia, RU",
    7: "SIN, Singapore, SG",
    8: "FRA, Frankfurt, Germany, DE",
    9: "IAD, Washington DC, USA, US",
    10: "BLR, Bangalore, India, IN",
    11: "TYO, Tokyo, Japan, JP",
    12: "BOM, Mumbai, India, IN",
    13: "HKG, Hong Kong, HK",
    14: "MAD, Madrid, Spain, ES",
    15: "CDG, Paris, France, FR",
    16: "MEX, Mexico City, Mexico, MX",
    17: "YYZ, Toronto, Canada, CA",
    18: "MEL, Melbourne, Australia, AU",
    19: "DEL, Delhi, India, IN",
    20: "JFK, New York, USA, US",
    21: "LHR, London, UK, GB",
}


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


async def get_entity_type(client: Client, username: str) -> str:
    try:
        user = await client.get_users(username)
        return "bot" if user.is_bot else "user"
    except Exception:
        entity = await client.get_chat(username)
        if entity.type.value in ["group", "supergroup"]:
            return "group"
        elif entity.type.value == "channel":
            return "channel"
        else:
            return "unknown"


async def get_info_by_type(client: Client, username: str) -> str:
    entity_type = await get_entity_type(client, username)

    if entity_type == "user":
        user = await client.get_users(username)
        creation_date = estimate_account_creation_date(user.id)
        account_age = calculate_account_age(creation_date)

        dc_location = DC_LOCATIONS.get(getattr(user, "dc_id", None), "Unknown")
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

        profile_pic_url = f"https://t.me/i/userpic/320/{user.username}.jpg" if (user.photo and user.username) else "No Profile Picture"

        return f"""
✘《 User Information ↯ 》
↯ Full Name: {user.first_name or ''} {user.last_name or ''}
↯ User ID: {user.id}
↯ Username: @{user.username or 'No username'}
↯ Chat ID: {user.id}

↯ Premium User: {"Yes" if user.is_premium else "No"}
↯ Verified: {"Yes" if getattr(user, 'is_verified', False) else "No"}

↯ Scam: {"Yes" if getattr(user, "is_scam", False) else "No"}
↯ Fake: {"Yes" if getattr(user, "is_fake", False) else "No"}
↯ Data Center: {dc_location}

↯ Status: {status}
↯ Account Created On: {creation_date.strftime('%b %d, %Y')}
↯ Account Age: {account_age}

↯ Profile Picture URL: {profile_pic_url}

↯ API Owner: @itz_mahir404 follow: https://t.me/bro_bin_lagbe
""".strip()

    elif entity_type == "bot":
        bot_user = await client.get_users(username)
        creation_date = estimate_account_creation_date(bot_user.id)
        account_age = calculate_account_age(creation_date)

        profile_pic_url = f"https://t.me/i/userpic/320/{bot_user.username}.jpg" if (bot_user.photo and bot_user.username) else "No Profile Picture"

        return f"""
✘《 Bot Information ↯ 》
↯ Name: {bot_user.first_name}
↯ Username: @{bot_user.username or 'No username'}
↯ User ID: {bot_user.id}
↯ Verified: {"Yes" if getattr(bot_user, 'is_verified', False) else "No"}
↯ Scam: {"Yes" if getattr(bot_user, "is_scam", False) else "No"}
↯ Fake: {"Yes" if getattr(bot_user, "is_fake", False) else "No"}

↯ Account Created On: {creation_date.strftime('%b %d, %Y')}
↯ Account Age: {account_age}
↯ Profile Picture URL: {profile_pic_url}

↯ API Owner: @itz_mahir404 follow: https://t.me/bro_bin_lagbe
""".strip()

    elif entity_type in ["group", "channel"]:
        chat = await client.get_chat(username)
        members_count = "Unknown"
        try:
            members_count = await client.get_chat_members_count(chat.id)
        except:
            members_count = "Not accessible"

        profile_pic = f"https://t.me/i/userpic/320/{chat.username}.jpg" if chat.username else "No Profile Picture"
        description = chat.description or "No description"
        is_verified = "Yes" if getattr(chat, "is_verified", False) else "No"
        is_scam = "Yes" if getattr(chat, "is_scam", False) else "No"
        is_fake = "Yes" if getattr(chat, "is_fake", False) else "No"
        flagged_status = "Flagged/Unsafe" if is_scam == "Yes" or is_fake == "Yes" else "Safe"

        member_list = ""
        if entity_type == "group":
            try:
                members = client.iter_chat_members(chat.id)
                ids = []
                async for member in members:
                    ids.append(str(member.user.id))
                    if len(ids) >= 10:
                        break
                member_list = "\n↯ Top Member Chat IDs:\n" + "\n".join(f" - {uid}" for uid in ids)
            except:
                member_list = "\n↯ Top Member Chat IDs: Not accessible"

        return f"""
✘《 {entity_type.capitalize()} Information ↯ 》
↯ Title: {chat.title}
↯ Username: @{chat.username or 'No username'}
↯ Chat ID: {chat.id}
↯ Type: {chat.type.value.capitalize()}
↯ Members Count: {members_count}

↯ Verified: {is_verified}
↯ Scam: {is_scam}
↯ Fake: {is_fake}
↯ Safety Status: {flagged_status}

↯ Description: {description}
↯ Profile Picture URL: {profile_pic}
{member_list}

↯ API Owner: @itz_mahir404 follow: https://t.me/bro_bin_lagbe
""".strip()

    else:
        return "Unknown entity type."


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
async def get_user_info(username: str = Query(..., min_length=4, max_length=32)):
    try:
        return await get_info_by_type(bot, username)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
