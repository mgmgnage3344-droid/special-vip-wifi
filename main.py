import os
import time
import random
import threading
import speedtest
import telebot
from telebot import types

# ----------------- Configurations -----------------
# Railway ရဲ့ Variables ထဲမှာ ထည့်သွင်းရပါမည်
BOT_TOKEN = os.getenv("BOT_TOKEN", "8890680174:AAFWbvPGffVWhTjwDm-dRlXpNpRNYSapqNg")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1757006852"))

bot = telebot.TeleBot(BOT_TOKEN)

# Package ဈေးနှုန်းများ (1GB မှ 10GB အထိ)
PACKAGES = {
    "1GB": 3000,
    "2GB": 6000,
    "3GB": 9000,
    "4GB": 12000,
    "5GB": 15000,
    "6GB": 18000,
    "7GB": 21000,
    "8GB": 24000,
    "9GB": 27000,
    "10GB": 30000
}

# လျှို့ဝှက်ကုဒ်
SECRET_BYPASS_CODE = "@@@$$$"

# Data သိမ်းဆည်းရန် ယာယီ Memory
users_db = set()           # User အားလုံးစာရင်း (Broadcast အတွက်)
pending_orders = {}       # OTP နှင့် Order အခြေအနေများ
admin_reply_targets = {}  # Admin ပြန်စာပို့ရန် target user map

# ဆဲဆိုမည့် စကားလုံးများနှင့် Keyword များ
CREDIT_KEYWORDS = ["အကြွေး", "အရင်သုံး", "နောက်မှပေး", "ရမလား", "အကြွေးပေး"]
ABUSE_RESPONSES = [
    "အကြွေး လုံးဝမရဘူး! ငွေရှင်းမှ သုံးရမယ်။ လာမရစ်နဲ့!",
    "WiFi ကို အကြွေးနဲ့ သုံးချင်ရင် သွားအိပ်နေလိုက်! လုံးဝမရဘူး။",
    "အကြွေး မပေးဘူးနော်! KPay နဲ့ အရင်လွှဲမှ ရမယ်။ ခဏခဏ လာမမေးနဲ့!"
]

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_packages = types.KeyboardButton("📶 VIP Package များ ဝယ်မည်")
    btn_speed = types.KeyboardButton("🚀 Speed Test စစ်မည်")
    markup.add(btn_packages, btn_speed)
    return markup

# ----------------- Start Command -----------------
@bot.message_handler(commands=['start'])
def start_cmd(message):
    users_db.add(message.chat.id)
    welcome_text = (
        "🌟 **Special VIP WiFi Agent Bot မှ ကြိုဆိုပါသည်** 🌟\n\n"
        "မြန်နှုန်းမြင့် အထူး VIP WiFi Code များကို အောက်ပါ Menu မှတစ်ဆင့် ဝယ်ယူနိုင်ပါပြီခင်ဗျာ။\n"
        "⚠ _(မှတ်ချက် - အကြွေးစနစ် လုံးဝမရပါ)_"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# ----------------- Broadcast စနစ် (Admin သီးသန့်) -----------------
@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if message.chat.id != ADMIN_ID:
        return
    msg_text = message.text.replace("/broadcast", "").strip()
    if not msg_text:
        bot.send_message(ADMIN_ID, "⚠️ ပို့ချင်သော စာသားကို `/broadcast <စာသား>` ပုံစံဖြင့် ရေးပါခင်ဗျာ။")
        return
    
    count = 0
    for uid in users_db:
        try:
            bot.send_message(uid, f"📢 **အသိပေးကြေညာချက်** 📢\n\n{msg_text}", parse_mode="Markdown")
            count += 1
        except Exception:
            pass
    bot.send_message(ADMIN_ID, f"✅ စုစုပေါင်း User ({count}) ယောက်ထံ အသိပေးစာ အောင်မြင်စွာ ပို့ဆောင်ပြီးပါပြီ။")

# ----------------- လျှို့ဝှက်ကုဒ် စနစ် (@@@$$$) -----------------
def stealth_delete_messages(chat_id, msg_ids, delay=5):
    time.sleep(delay)
    for m_id in msg_ids:
        try:
            bot.delete_message(chat_id, m_id)
        except Exception:
            pass

@bot.message_handler(func=lambda m: SECRET_BYPASS_CODE in m.text)
def secret_code_handler(message):
    dummy_vip_code = f"VIP-{random.randint(100000, 999999)}"
    reply_msg = bot.reply_to(
        message, 
        f"🤫 **Secret Access Granted!**\n\nသင့်အတွက် အခမဲ့ VIP WiFi Code: `{dummy_vip_code}`\n\n_(လုံခြုံရေးအရ ဤစာသားသည် ၅ စက္ကန့်အတွင်း အလိုအလျောက် ပျက်သွားပါမည်)_",
        parse_mode="Markdown"
    )
    threading.Thread(
        target=stealth_delete_messages, 
        args=(message.chat.id, [message.message_id, reply_msg.message_id], 5)
    ).start()

# ----------------- Speed Test စစ်ဆေးခြင်း -----------------
def run_speedtest_thread(chat_id):
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        down = round(st.download() / 1_000_000, 2)
        up = round(st.upload() / 1_000_000, 2)
        ping = round(st.results.ping, 1)

        result_text = (
            f"🚀 **WiFi Server Speed စစ်ဆေးမှု ရလဒ်** 🚀\n\n"
            f"📥 **Download:** `{down} Mbps`\n"
            f"📤 **Upload:** `{up} Mbps`\n"
            f"📶 **Ping:** `{ping} ms`"
        )
        bot.send_message(chat_id, result_text, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, "⚠️ Speed Test စစ်ဆေးမှု ယာယီမအောင်မြင်ပါ။ နောက်မှ ထပ်စမ်းကြည့်ပါ။")

@bot.message_handler(func=lambda m: m.text == "🚀 Speed Test စစ်မည်")
def speedtest_handler(message):
    bot.send_message(message.chat.id, "⏳ လက်ရှိ WiFi Server အမြန်နှုန်းကို တိုင်းတာနေပါသည်၊ ခေတ္တစောင့်ဆိုင်းပေးပါ...")
    threading.Thread(target=run_speedtest_thread, args=(message.chat.id,)).start()

# ----------------- VIP Package ရွေးချယ်မှု -----------------
@bot.message_handler(func=lambda m: m.text == "📶 VIP Package များ ဝယ်မည်")
def show_packages(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for pkg, price in PACKAGES.items():
        buttons.append(types.InlineKeyboardButton(f"{pkg} - {price:,} Ks", callback_data=f"buy_{pkg}"))
    markup.add(*buttons)
    bot.send_message(message.chat.id, "🛒 သင်ဝယ်ယူလိုသော VIP Package ကို ရွေးချယ်ပေးပါ -", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_package_choice(call):
    pkg_name = call.data.replace("buy_", "")
    price = PACKAGES.get(pkg_name, 0)
    
    pay_info = (
        f"📌 သင်ရွေးချယ်ထားသော ပက်ကေ့ခ်ျ - **{pkg_name} ({price:,} Ks)**\n\n"
        f"💳 **ငွေပေးချေရန် KPay စာရင်း -**\n"
        f"• KPay နံပါတ်: `09XXXXXXXXX`\n"
        f"• အမည်: `(သင့်နာမည်ထည့်ပါ)`\n"
        f"• ပမာဏ: `{price:,}` ကျပ်တိတိ\n\n"
        f"⚠️ **အရေးကြီးသည် -** ငွေလွှဲပြီးပါက ရရှိသော Screenshot (Slip) ကို ဤ Bot ဆီသို့ Photo ပုံစံဖြင့် ချက်ချင်း ပို့ပေးပါခင်ဗျာ။ စလစ်စစ်ဆေးပြီးမှသာ အတည်ပြုကုဒ် ထွက်လာပါမည်။"
    )
    bot.send_message(call.message.chat.id, pay_info, parse_mode="Markdown")

# ----------------- KPay Slip စစ်ဆေးခြင်း -----------------
@bot.message_handler(content_types=['photo'])
def handle_slip(message):
    users_db.add(message.chat.id)
    markup = types.InlineKeyboardMarkup()
    btn_approve = types.InlineKeyboardButton("✅ Approve (ငွေရရှိ)", callback_data=f"approve_{message.chat.id}")
    btn_reject = types.InlineKeyboardButton("❌ Reject (ပယ်ဖျက်)", callback_data=f"reject_{message.chat.id}")
    markup.add(btn_approve, btn_reject)

    caption = (
        f"🔔 **ငွေလွှဲပြေစာ အသစ် ရောက်ရှိလာပါသည်!**\n\n"
        f"👤 User: @{message.from_user.username or 'No Username'}\n"
        f"🆔 ID: `{message.chat.id}`"
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, parse_mode="Markdown", reply_markup=markup)
    bot.reply_to(message, "✅ ငွေလွှဲပြေစာ ရရှိပါသည်။ Admin ဘက်မှ အတည်ပြုပေးသည်နှင့် အတည်ပြုကုဒ် ပို့ပေးပါမည်ခင်ဗျာ။")

# Admin Approve / Reject Handler
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def process_admin_approval(call):
    if call.message.chat.id != ADMIN_ID:
        return

    action, user_id_str = call.data.split("_")
    user_id = int(user_id_str)

    if action == "approve":
        otp = str(random.randint(1000, 9999))
        pending_orders[user_id] = otp
        
        bot.send_message(
            user_id,
            f"🎉 **ငွေလွှဲအတည်ပြုပြီးပါပြီခင်ဗျာ!**\n\n"
            f"🔑 သင်၏ အတည်ပြုကုဒ်မှာ - `{otp}` ဖြစ်ပါသည်။\n\n"
            f"WiFi ကုတ်ရယူရန်အတွက် ဤဂဏန်း ၄ လုံးကို Bot ထံ စာသားအဖြစ် ပြန်လည်ရိုက်ထည့်ပေးပါခင်ဗျာ။",
            parse_mode="Markdown"
        )
        bot.edit_message_caption("✅ အောင်မြင်စွာ အတည်ပြုပြီးပါပြီ။", call.message.chat.id, call.message.message_id)

    elif action == "reject":
        bot.send_message(user_id, "❌ ငွေလွှဲပြေစာ မမှန်ကန်ပါသဖြင့် ငြင်းပယ်လိုက်ပါသည်။ သေချာစွာ ပြန်လည်စစ်ဆေးပေးပါ။")
        bot.edit_message_caption("❌ ပယ်ဖျက်လိုက်ပါပြီ။", call.message.chat.id, call.message.message_id)

# ----------------- စာလုံးစစ်ခြင်း၊ OTP၊ အကြွေးဆဲဆိုခြင်း & Admin Two-way Chat -----------------
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    user_id = message.chat.id
    users_db.add(user_id)
    text = message.text.strip()

    # ၁။ Admin ဘက်မှ စာပြန်ခြင်း (Live Reply)
    if user_id == ADMIN_ID:
        if message.reply_to_message:
            target_id = admin_reply_targets.get(message.reply_to_message.message_id)
            if target_id:
                bot.send_message(target_id, f"💬 **Admin မှ ပြန်ကြားစာ -**\n\n{text}")
                bot.reply_to(message, "✅ ပြန်ကြားစာ ပို့ပြီးပါပြီ။")
                return
        bot.send_message(ADMIN_ID, "⚠️ User ဆီ စာပြန်လိုပါက ထို User ဆီမှ လာသော Message ကို Telegram Reply လုပ်ပြီး ပြန်ပေးပါခင်ဗျာ။")
        return

    # ၂။ OTP အတည်ပြုကုဒ် စစ်ဆေးခြင်း
    if user_id in pending_orders and pending_orders[user_id] == text:
        wifi_code = f"VIP-{random.randint(100000, 999999)}"
        bot.reply_to(
            message,
            f"🎊 **အတည်ပြုချက် အောင်မြင်ပါသည်!** 🎊\n\n"
            f"📶 သင့်၏ VIP WiFi Code မှာ - `{wifi_code}` ဖြစ်ပါသည်။\n"
            f"အသုံးပြုသည့်အတွက် ကျေးဇူးတင်ပါသည်ခင်ဗျာ။",
            parse_mode="Markdown"
        )
        del pending_orders[user_id]
        return

    # ၃။ အကြွေးတောင်းသူများကို အလိုအလျောက် ဆဲဆိုခြင်း
    if any(k in text for k in CREDIT_KEYWORDS):
        bot.reply_to(message, random.choice(ABUSE_RESPONSES))
        return

    # ၄။ Admin ဆီသို့ User ၏ စာကို တိုက်ရိုက် Forward ပို့ခြင်း
    fwd_msg = bot.send_message(
        ADMIN_ID,
        f"📩 **User ထံမှ မက်ဆေ့ခ်ျ -**\n"
        f"👤 နာမည်: {message.from_user.first_name}\n"
        f"🆔 ID: `{user_id}`\n\n"
        f"စာသား: {text}",
        parse_mode="Markdown"
    )
    admin_reply_targets[fwd_msg.message_id] = user_id

    # ၅။ စာလုံးပေါင်းမှားခြင်း အသိပေးချက်
    bot.reply_to(message, "⚠️ စာရိုက်မှားနေပါသည် (သို့မဟုတ်) မှားယွင်းသော စာသားဖြစ်နေပါသည်။ ကျေးဇူးပြု၍ သတ်မှတ် Menu များမှတစ်ဆင့်သာ ရွေးချယ်အသုံးပြုပေးပါခင်ဗျာ။")

# Bot စတင်လည်ပတ်ခြင်း
if __name__ == "__main__":
    print("Special VIP WiFi Bot စတင်အလုပ်လုပ်နေပါပြီ...")
    bot.infinity_polling()
