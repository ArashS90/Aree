# -*- coding: utf-8 -*-
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import sqlite3
import random
import smtplib
import time
from email.mime.text import MIMEText
import re
import json
import requests
import urllib3
urllib3.disable_warnings()

# ================= تنظیمات =================
TOKEN = "8923408965:AAEyod61XQcYGES1WRvGcO0QI7yfy9a0L7I"
ADMIN_IDS = [7955284547, 6953888592]
CHANNEL_USERNAME = "@VELORIX_VPN"
CHANNEL_ID = -1003965169089
CARD_NUMBER_1 = "6037701214510429"
CARD_NAME_1 = "نیما کریمی"
CARD_NUMBER_2 = "6219861955514681"
CARD_NAME_2 = "صفری"
EMAIL = "jigartunnel@gmail.com"
APP_PASSWORD = "ddbx wjqz ubke eyif"
SHOP_URL = "https://arashs90.github.io/Aree/index.html"

BASE_PRICE_PER_GIG = 9000
AGENT_PRICE_PER_GIG = 8000
BOT_NAME = "ربات شراکتی Jigar Tunnel و VPN Nima"

bot = telebot.TeleBot(TOKEN)
session = requests.Session()
session.verify = False
bot.session = session

temp_agent_data = {}
temp_purchase = {}

# ================= دیتابیس =================
def get_db():
    return sqlite3.connect("jigar_tunnel.db", check_same_thread=False, timeout=20)

def init_db():
    db = get_db()
    cur = db.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT,
        balance INTEGER DEFAULT 0,
        reg_date INTEGER,
        plan TEXT,
        expiry INTEGER,
        disabled INTEGER DEFAULT 0,
        is_agent INTEGER DEFAULT 0,
        agent_daily_sales TEXT,
        agent_full_name TEXT,
        agent_national_code TEXT,
        agent_phone TEXT,
        agent_approved_at INTEGER
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan TEXT,
        original_amount TEXT,
        final_amount TEXT,
        discount_code TEXT,
        method TEXT,
        tracking_code TEXT UNIQUE,
        status TEXT,
        timestamp INTEGER,
        receipt_photo TEXT,
        qty INTEGER DEFAULT 1
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS discount_codes (
        code TEXT PRIMARY KEY,
        type TEXT,
        value TEXT,
        uses_left INTEGER,
        expiry INTEGER,
        created_by INTEGER
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS broadcast_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT,
        recipients INTEGER,
        target TEXT,
        timestamp INTEGER
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bot_config (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS plan_status (
        plan TEXT PRIMARY KEY,
        available INTEGER DEFAULT 1
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS banned_users (
        user_id INTEGER PRIMARY KEY,
        banned_at INTEGER,
        reason TEXT
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        title TEXT,
        status TEXT,
        created_at INTEGER,
        closed_at INTEGER
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ticket_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER,
        sender_id INTEGER,
        sender_role TEXT,
        message TEXT,
        timestamp INTEGER
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS balance_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        type TEXT,
        description TEXT,
        timestamp INTEGER
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin_permissions (
        user_id INTEGER PRIMARY KEY,
        can_manage_plans INTEGER DEFAULT 1,
        can_manage_discounts INTEGER DEFAULT 1,
        can_broadcast INTEGER DEFAULT 1,
        can_manage_tickets INTEGER DEFAULT 1,
        can_ban INTEGER DEFAULT 1
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS agent_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        full_name TEXT,
        national_code TEXT,
        phone_number TEXT,
        daily_sales TEXT,
        status TEXT,
        created_at INTEGER,
        approved_at INTEGER,
        rejected_at INTEGER,
        admin_note TEXT
    )
    """)
    
    # ===== اضافه کردن ستون‌های گمشده برای دیتابیس‌های قدیمی =====
    try:
        cur.execute("SELECT is_agent FROM users LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("ALTER TABLE users ADD COLUMN is_agent INTEGER DEFAULT 0")
        cur.execute("ALTER TABLE users ADD COLUMN agent_daily_sales TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN agent_full_name TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN agent_national_code TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN agent_phone TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN agent_approved_at INTEGER")
    
    # حذف ستون photo_id اگه وجود داره
    try:
        cur.execute("ALTER TABLE agent_requests DROP COLUMN photo_id")
    except:
        pass
    
    for plan in ['10','20','30','50']:
        cur.execute("INSERT OR IGNORE INTO plan_status (plan, available) VALUES (?,?)", (plan, 1))
    
    for admin in ADMIN_IDS:
        cur.execute("INSERT OR IGNORE INTO admin_permissions (user_id) VALUES (?)", (admin,))
    
    db.commit()
    cur.close()
    db.close()

init_db()

# ================= توابع کمکی =================
def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_agent(user_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT is_agent FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    cur.close()
    db.close()
    return row and row[0] == 1

def is_user_banned(user_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT 1 FROM banned_users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    cur.close()
    db.close()
    return row is not None

def is_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def add_user(user_id):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("INSERT INTO users (id, reg_date, balance) VALUES (?,?,?)", (user_id, int(time.time()), 0))
        db.commit()
        cur.close()
        db.close()
        return True
    except:
        cur.close()
        db.close()
        return False

def user_exists(user_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    cur.close()
    db.close()
    return row is not None

def get_user_email(user_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT email FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    cur.close()
    db.close()
    return row[0] if row else None

def set_user_email(user_id, email):
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE users SET email=? WHERE id=?", (email, user_id))
    db.commit()
    cur.close()
    db.close()

def get_user_balance(user_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT balance FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    cur.close()
    db.close()
    return row[0] if row else 0

def update_balance(user_id, amount, desc):
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, user_id))
    db.commit()
    cur.execute("INSERT INTO balance_history (user_id, amount, type, description, timestamp) VALUES (?,?,?,?,?)",
                (user_id, amount, 'credit' if amount>0 else 'debit', desc, int(time.time())))
    db.commit()
    cur.close()
    db.close()

def generate_tracking_code():
    return str(random.randint(100000, 999999))

def is_plan_available(plan):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT available FROM plan_status WHERE plan=?", (str(plan),))
    row = cur.fetchone()
    cur.close()
    db.close()
    return row[0] == 1 if row else True

def set_plan_availability(plan, available):
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE plan_status SET available=? WHERE plan=?", (1 if available else 0, str(plan)))
    db.commit()
    cur.close()
    db.close()

def apply_discount_code(code, original_amount_int):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT type, value, uses_left, expiry FROM discount_codes WHERE code=?", (code,))
    row = cur.fetchone()
    cur.close()
    db.close()
    if not row:
        return None, "کد نامعتبر"
    dtype, dvalue, uses_left, expiry = row
    if expiry < int(time.time()):
        return None, "کد منقضی شده"
    if uses_left <= 0:
        return None, "کد استفاده شده"
    if dtype == "percent":
        final = original_amount_int * (100 - int(dvalue)) // 100
    else:
        final = max(0, original_amount_int - int(dvalue))
    return final, None

def consume_discount_code(code):
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE discount_codes SET uses_left = uses_left - 1 WHERE code=?", (code,))
    db.commit()
    cur.close()
    db.close()

def send_to_admins(text, parse_mode="Markdown", reply_markup=None):
    for admin in ADMIN_IDS:
        try:
            bot.send_message(admin, text, parse_mode=parse_mode, reply_markup=reply_markup)
        except:
            pass

def send_photo_to_admins(photo, caption=None, reply_markup=None):
    for admin in ADMIN_IDS:
        try:
            bot.send_photo(admin, photo, caption=caption, reply_markup=reply_markup, parse_mode="Markdown")
        except:
            pass

def set_bot_disabled(disabled, reason=""):
    db = get_db()
    cur = db.cursor()
    cur.execute("REPLACE INTO bot_config (key, value) VALUES (?,?)", ("bot_disabled", "1" if disabled else "0"))
    cur.execute("REPLACE INTO bot_config (key, value) VALUES (?,?)", ("disable_reason", reason))
    db.commit()
    cur.close()
    db.close()

def is_bot_disabled():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT value FROM bot_config WHERE key='bot_disabled'")
    row = cur.fetchone()
    cur.close()
    db.close()
    return row and row[0] == "1"

def get_disable_reason():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT value FROM bot_config WHERE key='disable_reason'")
    row = cur.fetchone()
    cur.close()
    db.close()
    return row[0] if row else ""

def has_pending_agent_request(user_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM agent_requests WHERE user_id=? AND status='pending'", (user_id,))
    row = cur.fetchone()
    cur.close()
    db.close()
    return row is not None

def get_plan_price(plan_gig, user_id):
    if is_agent(user_id):
        return AGENT_PRICE_PER_GIG * plan_gig
    return BASE_PRICE_PER_GIG * plan_gig

def get_total_users():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE disabled=0")
    count = cur.fetchone()[0]
    cur.close()
    db.close()
    return count

def get_total_agents():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE is_agent=1 AND disabled=0")
    count = cur.fetchone()[0]
    cur.close()
    db.close()
    return count

def broadcast_to_users(text):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE disabled=0")
    users = cur.fetchall()
    cur.close()
    db.close()
    success = 0
    for user in users:
        try:
            bot.send_message(user[0], text, parse_mode="Markdown")
            success += 1
            time.sleep(0.05)
        except:
            pass
    return success

def broadcast_to_agents(text):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE is_agent=1 AND disabled=0")
    agents = cur.fetchall()
    cur.close()
    db.close()
    success = 0
    for agent in agents:
        try:
            bot.send_message(agent[0], text, parse_mode="Markdown")
            success += 1
            time.sleep(0.05)
        except:
            pass
    return success

def bot_enabled_for_users(func):
    def wrapper(message, *args, **kwargs):
        user_id = message.from_user.id
        if is_user_banned(user_id):
            bot.reply_to(message, "⛔ شما توسط ادمین مسدود شده‌اید.", parse_mode="Markdown")
            return
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT disabled FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        cur.close()
        db.close()
        if row and row[0] == 1:
            bot.reply_to(message, "🔐 حساب کاربری شما غیرفعال شده است.", parse_mode="Markdown")
            return
        if not is_admin(user_id) and is_bot_disabled():
            bot.reply_to(message, f"🔴 **ربات در حال حاضر غیرفعال است.**\nعلت: {get_disable_reason()}\nلطفاً بعداً مراجعه کنید.", parse_mode="Markdown")
            return
        return func(message, *args, **kwargs)
    return wrapper

# ================= کیبوردها =================
def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("🛒 خرید اشتراک"), KeyboardButton("📞 پشتیبانی"))
    kb.add(KeyboardButton("👤 حساب کاربری"), KeyboardButton("💰 کیف پول"))
    kb.add(KeyboardButton("🎫 تیکت‌های من"), KeyboardButton("ℹ️ درباره ما"))
    kb.add(KeyboardButton("🛍️ فروشگاه", web_app=WebAppInfo(url=SHOP_URL)))
    kb.add(KeyboardButton("📜 قوانین"), KeyboardButton("🤝 درخواست نمایندگی"))
    kb.add(KeyboardButton("❓ راهنما"))
    return kb

def buy_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    plans = [('10','۹۰,۰۰۰'), ('20','۱۸۰,۰۰۰'), ('30','۲۷۰,۰۰۰'), ('50','۴۵۰,۰۰۰')]
    for plan, price in plans:
        if is_plan_available(plan):
            kb.add(KeyboardButton(f"🗓️ {plan} گیگ - {price} تومان"))
    kb.add(KeyboardButton("🔙 بازگشت به منو"))
    return kb

def back_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    kb.add(KeyboardButton("🔙 بازگشت به منو"))
    return kb

# ================= کامند start =================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not is_admin(user_id) and is_bot_disabled():
        bot.send_message(user_id, f"🔴 **ربات در حال حاضر غیرفعال است.**\nعلت: {get_disable_reason()}\nلطفاً بعداً مراجعه کنید.", parse_mode="Markdown")
        return
    if is_user_banned(user_id):
        bot.send_message(user_id, "⛔ شما توسط ادمین مسدود شده‌اید.")
        return
    
    text = message.text.strip()
    
    if text.startswith('/start buy_'):
        parts = text.split('_')
        if len(parts) < 2:
            bot.send_message(user_id, "❌ لینک نامعتبر")
            return
        plan = parts[1]
        qty = 1
        discount = None
        if len(parts) >= 3:
            try:
                qty = int(parts[2])
            except:
                qty = 1
        if len(parts) >= 4:
            discount = parts[3]
        
        plan_gig = int(plan)
        if plan_gig not in [10, 20, 30, 50]:
            bot.send_message(user_id, "❌ پلن نامعتبر")
            return
        if not is_plan_available(plan):
            bot.send_message(user_id, f"❌ پلن {plan} گیگ ناموجود است.")
            return
        
        original_amount = get_plan_price(plan_gig, user_id) * qty
        final_amount = original_amount
        applied_discount = None
        if discount:
            final_amount, err = apply_discount_code(discount, original_amount)
            if err:
                bot.send_message(user_id, f"⚠️ {err}\nبدون تخفیف ادامه می‌دهید.")
            else:
                applied_discount = discount
                consume_discount_code(discount)
        
        plan_name = f"{plan} گیگ"
        temp_purchase[user_id] = {
            "plan": plan_name,
            "original_amount": original_amount,
            "final_amount": final_amount,
            "plan_key": plan,
            "qty": qty,
            "discount_code": applied_discount,
            "method": None
        }
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("💳 پرداخت با کارت به کارت", callback_data=f"pay_card_{plan}_{qty}_{discount if discount else ''}"),
                   InlineKeyboardButton("💰 پرداخت از کیف پول", callback_data=f"pay_wallet_{plan}_{qty}_{discount if discount else ''}"))
        bot.send_message(user_id, 
            f"🧾 **پلن:** {plan_name}\n"
            f"📦 **تعداد:** {qty}\n"
            f"💰 **مبلغ نهایی:** {final_amount:,} تومان\n\n"
            f"لطفاً روش پرداخت را انتخاب کنید:", 
            reply_markup=markup, parse_mode="Markdown")
        return
    
    if text.startswith('/start track'):
        msg = bot.send_message(user_id, "🔍 **لطفاً کد پیگیری خود را وارد کنید:**")
        bot.register_next_step_handler(msg, check_tracking_code)
        return
    
    if not is_joined(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 عضو شدن در کانال", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"))
        markup.add(InlineKeyboardButton("✅ عضو شدم", callback_data="check_join"))
        bot.send_message(message.chat.id, "❌ ابتدا در کانال عضو شوید!", reply_markup=markup)
        return
    
    if not user_exists(user_id):
        add_user(user_id)
    
    if not get_user_email(user_id):
        msg = bot.send_message(message.chat.id, "📧 لطفاً ایمیل خود را وارد کنید (برای اطلاع‌رسانی سفارش):")
        bot.register_next_step_handler(msg, ask_email, user_id)
        return
    
    welcome_text = f"""
🌟 **به {BOT_NAME} خوش آمدی** 🌟
━━━━━━━━━━━━━━━━━━━━━
🔥 **اینترنت آزاد، پرسرعت و امن**
🔹 **بهترین کانفیگ‌های VPN با کیفیت بالا**
🔹 **پشتیبانی ۲۴ ساعته، ۷ روز هفته**

💰 **قیمت‌های ویژه:**
• کاربر عادی: ۹,۰۰۰ تومان/گیگ
• نماینده‌ها: ۸,۰۰۰ تومان/گیگ

📌 **برای شروع، از دکمه‌های زیر استفاده کن:**

🛒 **خرید اشتراک** → انتخاب پلن و پرداخت
💰 **کیف پول** → مدیریت اعتبار شما
🎫 **تیکت‌های من** → ارتباط با پشتیبانی
🤝 **درخواست نمایندگی** → فروش با قیمت ویژه

━━━━━━━━━━━━━━━━━━━━━
💎 **با ما همراه شو و اینترنت بدون محدودیت رو تجربه کن!**
"""
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=main_keyboard())

def ask_email(message, user_id):
    email = message.text.strip()
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        bot.send_message(message.chat.id, "❌ ایمیل نامعتبر. دوباره وارد کنید:")
        bot.register_next_step_handler(message, ask_email, user_id)
        return
    set_user_email(user_id, email)
    bot.send_message(message.chat.id, "✅ ایمیل ثبت شد.", reply_markup=main_keyboard())
    start(message)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join(call):
    if is_joined(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تأیید شد")
        bot.send_message(call.message.chat.id, "حالا /start را بزن.", reply_markup=main_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ هنوز عضو نشدی.", show_alert=True)

def check_tracking_code(message):
    code = message.text.strip()
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.send_message(user_id, "⛔ شما مسدود شده‌اید.")
        return
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT order_id, plan, final_amount, status, timestamp, qty FROM orders WHERE tracking_code=?", (code,))
    row = cur.fetchone()
    cur.close()
    db.close()
    if not row:
        bot.send_message(user_id, "❌ **کد پیگیری نامعتبر است.**", parse_mode="Markdown")
        return
    order_id, plan, final_amount, status, ts, qty = row
    status_text = {
        'pending': '🕒 در انتظار تأیید ادمین',
        'paid': '✅ پرداخت شده (در انتظار ارسال گانفیک)',
        'done': '🎉 تکمیل شده (گانفیک ارسال شد)',
        'rejected': '❌ رد شده'
    }.get(status, status)
    bot.send_message(user_id, f"""
🔍 **نتیجه پیگیری سفارش**

🆔 شماره سفارش: {order_id}
📦 پلن: {plan}
🔢 تعداد: {qty}
💰 مبلغ: {final_amount} تومان
📌 وضعیت: {status_text}
🕓 تاریخ ثبت: {time.ctime(ts)}
""", parse_mode="Markdown")

# ================= دکمه راهنما =================
@bot.message_handler(func=lambda msg: msg.text == "❓ راهنما")
@bot_enabled_for_users
def help_button(message):
    user_id = message.from_user.id
    
    text = f"""
❓ **راهنمای کامل {BOT_NAME}**
━━━━━━━━━━━━━━━━━━━━━

📌 **دکمه‌های اصلی:**

🛒 **خرید اشتراک** → انتخاب پلن و خرید
💰 **کیف پول** → مشاهده و شارژ موجودی
🎫 **تیکت‌های من** → ثبت و پیگیری تیکت
👤 **حساب کاربری** → اطلاعات حساب شما
🤝 **درخواست نمایندگی** → ثبت درخواست
📞 **پشتیبانی** → ارتباط با پشتیبان
📜 **قوانین** → قوانین فروشگاه

━━━━━━━━━━━━━━━━━━━━━
⌨️ **کامندها:**
/start → شروع
/help → راهنما
/panel → پنل ادمین
/agents → لیست نماینده‌ها

━━━━━━━━━━━━━━━━━━━━━
💰 **قیمت‌ها:**
کاربر عادی: ۹,۰۰۰ تومان/گیگ
نماینده: ۸,۰۰۰ تومان/گیگ
"""
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=main_keyboard())

@bot.message_handler(commands=['help'])
def help_command(message):
    help_button(message)

# ================= کامند قوانین =================
@bot.message_handler(commands=['rules'])
def rules_command(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        return
    
    rules_text = f"""
🚨 **قوانین فروشگاه {BOT_NAME}** 🚨
━━━━━━━━━━━━━━━━━━━━━

1️⃣ رسید جعلی ممنوع → مسدودیت دائمی
2️⃣ واریز دقیق مبلغ → تأخیر در تحویل
3️⃣ عدم انصراف پس از ارسال گانفیک
4️⃣ مسئولیت نگهداری کانفیگ با شماست
5️⃣ پشتیبانی فقط در ربات
6️⃣ تغییر قیمت‌ها محفوظ است
7️⃣ زمان ارسال گانفیک حداکثر 12 ساعت
8️⃣ بدون تأیید رسید، گانفیک ارسال نمی‌شود

⚠️ تخلف = مسدودیت دائمی

📞 پشتیبانی: از دکمه 📞 پشتیبانی استفاده کنید.
"""
    bot.send_message(user_id, rules_text, parse_mode="Markdown", reply_markup=main_keyboard())

# ================= کامند پشتیبانی =================
@bot.message_handler(commands=['support'])
def support_command(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        return
    
    bot.send_message(user_id, 
        f"📞 **پشتیبانی {BOT_NAME}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"برای ارتباط با پشتیبان روی لینک زیر کلیک کنید:\n"
        f"[ارسال پیام به پشتیبان](tg://user?id={ADMIN_IDS[0]})\n\n"
        f"🕐 ساعات پاسخگویی: ۲۴ ساعته\n"
        f"⏱️ زمان پاسخگویی: حداکثر ۱۲ ساعت",
        parse_mode="Markdown", reply_markup=main_keyboard())

# ================= کامند پیگیری سفارش =================
@bot.message_handler(commands=['track'])
def track_command(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        msg = bot.send_message(user_id, "🔍 **لطفاً کد پیگیری خود را وارد کنید:**\nمثال: `/track 123456`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, check_tracking_code)
        return
    
    code = parts[1]
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT order_id, plan, final_amount, status, timestamp, qty FROM orders WHERE tracking_code=?", (code,))
    row = cur.fetchone()
    cur.close()
    db.close()
    
    if not row:
        bot.send_message(user_id, "❌ **کد پیگیری نامعتبر است.**", parse_mode="Markdown")
        return
    
    order_id, plan, final_amount, status, ts, qty = row
    status_text = {
        'pending': '🕒 در انتظار تأیید ادمین',
        'paid': '✅ پرداخت شده (در انتظار ارسال گانفیک)',
        'done': '🎉 تکمیل شده (گانفیک ارسال شد)',
        'rejected': '❌ رد شده'
    }.get(status, status)
    
    bot.send_message(user_id, f"""
🔍 **نتیجه پیگیری سفارش**

🆔 شماره سفارش: {order_id}
📦 پلن: {plan}
🔢 تعداد: {qty}
💰 مبلغ: {final_amount} تومان
📌 وضعیت: {status_text}
🕓 تاریخ ثبت: {time.ctime(ts)}
""", parse_mode="Markdown")

# ================= کامند اطلاعات کامل نماینده =================
@bot.message_handler(commands=['agent_info'])
def agent_info_command(message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ لطفاً آیدی نماینده را وارد کنید:\nمثال: `/agent_info 123456789`", parse_mode="Markdown")
        return
    
    try:
        user_id = int(parts[1])
    except:
        bot.send_message(message.chat.id, "❌ آیدی نامعتبر.", parse_mode="Markdown")
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id, email, balance, reg_date, plan, expiry, disabled,
               is_agent, agent_daily_sales, agent_full_name, agent_national_code, 
               agent_phone, agent_approved_at
        FROM users WHERE id=? AND is_agent=1
    """, (user_id,))
    agent = cur.fetchone()
    cur.close()
    db.close()
    
    if not agent:
        bot.send_message(message.chat.id, f"❌ کاربر {user_id} نماینده نیست یا یافت نشد.", parse_mode="Markdown")
        return
    
    (uid, email, balance, reg_date, plan, expiry, disabled,
     is_agent, daily_sales, full_name, national_code, phone, approved_at) = agent
    
    remain_days = 0
    if plan:
        remain_days = max(0, (expiry - int(time.time())) // 86400)
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM orders WHERE user_id=?", (user_id,))
    total_orders = cur.fetchone()[0]
    cur.execute("SELECT SUM(final_amount) FROM orders WHERE user_id=? AND status='done'", (user_id,))
    total_sales = cur.fetchone()[0] or 0
    cur.close()
    db.close()
    
    text = f"""
👤 **اطلاعات کامل نماینده**
━━━━━━━━━━━━━━━━━━━━━

📌 **اطلاعات شخصی:**
👤 نام و نام خانوادگی: {full_name}
🆔 کد ملی: {national_code}
📞 شماره تماس: {phone}
📊 فروش روزانه: {daily_sales}
🕐 تاریخ تایید: {time.ctime(approved_at) if approved_at else 'ثبت نشده'}

━━━━━━━━━━━━━━━━━━━━━
📌 **اطلاعات حساب:**
🆔 آیدی: `{uid}`
📧 ایمیل: {email if email else 'ثبت نشده'}
💰 موجودی کیف پول: {balance:,} تومان
📅 تاریخ ثبت نام: {time.ctime(reg_date)}

━━━━━━━━━━━━━━━━━━━━━
📌 **وضعیت اشتراک:**
📦 پلن فعال: {plan if plan else 'هیچ'}
⏳ روزهای باقی‌مانده: {remain_days}
🔓 وضعیت حساب: {'✅ فعال' if disabled == 0 else '🔒 غیرفعال'}

━━━━━━━━━━━━━━━━━━━━━
📊 **آمار فروش:**
📝 تعداد کل سفارشات: {total_orders}
💰 کل فروش: {total_sales:,} تومان

━━━━━━━━━━━━━━━━━━━━━
💰 **قیمت ویژه:** ۸,۰۰۰ تومان/گیگ
"""
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ================= کامند لیست نماینده‌ها =================
@bot.message_handler(commands=['agents'])
def list_agents_command(message):
    if not is_admin(message.from_user.id):
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id, agent_full_name, agent_national_code, agent_phone, 
               agent_daily_sales, agent_approved_at, balance 
        FROM users WHERE is_agent=1
        ORDER BY agent_approved_at DESC
    """)
    agents = cur.fetchall()
    cur.close()
    db.close()
    
    if not agents:
        bot.send_message(message.chat.id, "📭 **هیچ نماینده‌ای ثبت نشده است.**", parse_mode="Markdown")
        return
    
    text = "🤝 **لیست نماینده‌ها:**\n━━━━━━━━━━━━━━━━━━━━━\n"
    for i, agent in enumerate(agents, 1):
        user_id, name, national, phone, sales, approved_at, balance = agent
        text += f"""
{i}. 👤 **{name}**
   🆔 آیدی: `{user_id}`
   🆔 کد ملی: {national}
   📞 شماره: {phone}
   📊 فروش روزانه: {sales}
   💰 موجودی: {balance:,} تومان
   ───────────────────
"""
    
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ================= کامند افزودن نماینده (راه حل سریع) =================
@bot.message_handler(commands=['add_agent'])
def add_agent_command(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ شما دسترسی به این بخش ندارید!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, 
            "❌ **فرمت:** `/add_agent آیدی_کاربر`\n"
            "مثال: `/add_agent 123456789`\n\n"
            "برای اضافه کردن با نام: `/add_agent 123456789 ارش صفری`",
            parse_mode="Markdown")
        return
    
    try:
        user_id = int(parts[1])
    except:
        bot.send_message(message.chat.id, "❌ آیدی نامعتبر.")
        return
    
    full_name = " ".join(parts[2:]) if len(parts) > 2 else "بدون نام"
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cur.fetchone():
        add_user(user_id)
    
    cur.execute("""
        UPDATE users 
        SET is_agent=1, agent_full_name=?, agent_approved_at=? 
        WHERE id=?
    """, (full_name, int(time.time()), user_id))
    db.commit()
    cur.close()
    db.close()
    
    bot.send_message(message.chat.id, f"✅ **نماینده جدید اضافه شد**\n👤 {full_name}\n🆔 {user_id}")
    try:
        bot.send_message(user_id, 
            f"🎉 **تبریک! شما به عنوان نماینده JigarTunnel انتخاب شدید.**\n"
            f"👤 **نام:** {full_name}\n"
            "💰 **قیمت ویژه:** ۸,۰۰۰ تومان/گیگ",
            parse_mode="Markdown")
    except:
        pass

# ================= روش‌های پرداخت =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_card_"))
def pay_card(call):
    if not is_admin(call.from_user.id) and is_bot_disabled():
        bot.answer_callback_query(call.id, "ربات غیرفعال است", show_alert=True)
        return
    parts = call.data.split("_")
    if len(parts) < 4:
        bot.answer_callback_query(call.id, "خطا در داده")
        return
    plan_key = parts[2]
    qty = int(parts[3])
    discount = parts[4] if len(parts) > 4 else None
    user_id = call.from_user.id
    if user_id not in temp_purchase:
        bot.answer_callback_query(call.id, "خطا. دوباره خرید را شروع کنید.")
        return
    data = temp_purchase[user_id]
    final_amount = data["final_amount"]
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💰 ارسال رسید", callback_data=f"send_receipt_{plan_key}_{qty}_{discount if discount else ''}"))
    
    card_text = f"""
💳 **پرداخت کارت به کارت**

💰 **مبلغ نهایی:** {final_amount:,} تومان

📌 **شماره کارت اول:**
`{CARD_NUMBER_1}`
👤 **به نام:** {CARD_NAME_1}

📌 **شماره کارت دوم:**
`{CARD_NUMBER_2}`
👤 **به نام:** {CARD_NAME_2}

⚠️ **دقت کنید:** پس از واریز، دکمه زیر را بزنید و تصویر رسید را ارسال کنید.
"""
    bot.send_message(call.message.chat.id, card_text, parse_mode="Markdown", reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_wallet_"))
def pay_wallet(call):
    if not is_admin(call.from_user.id) and is_bot_disabled():
        bot.answer_callback_query(call.id, "ربات غیرفعال است", show_alert=True)
        return
    parts = call.data.split("_")
    if len(parts) < 4:
        bot.answer_callback_query(call.id, "خطا در داده")
        return
    plan_key = parts[2]
    qty = int(parts[3])
    discount = parts[4] if len(parts) > 4 else None
    user_id = call.from_user.id
    if user_id not in temp_purchase:
        bot.answer_callback_query(call.id, "خطا. دوباره خرید را شروع کنید.")
        return
    data = temp_purchase[user_id]
    final_amount = data["final_amount"]
    plan_name = data["plan"]
    original_amount = data["original_amount"]
    balance = get_user_balance(user_id)
    
    if balance < final_amount:
        bot.answer_callback_query(call.id, f"❌ موجودی کافی نیست. موجودی: {balance:,} تومان", show_alert=True)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 پرداخت با کارت به کارت", callback_data=f"pay_card_{plan_key}_{qty}_{discount if discount else ''}"))
        bot.send_message(call.message.chat.id, "موجودی کیف پول شما کافی نیست. آیا می‌خواهید با کارت به کارت پرداخت کنید؟", reply_markup=markup)
        return
    
    update_balance(user_id, -final_amount, f"خرید پلن {plan_name} (تعداد {qty})")
    tracking = generate_tracking_code()
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO orders (user_id, plan, original_amount, final_amount, discount_code, method, tracking_code, status, timestamp, qty)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (user_id, plan_name, str(original_amount), str(final_amount), data.get("discount_code"), "wallet", tracking, "paid", int(time.time()), qty))
    db.commit()
    order_id = cur.lastrowid
    cur.close()
    db.close()
    
    bot.answer_callback_query(call.id, "✅ پرداخت با کیف پول انجام شد.")
    bot.send_message(user_id, f"✅ **پرداخت با کیف پول با موفقیت انجام شد.**\n🔢 کد پیگیری: `{tracking}`\nبه زودی گانفیک برای شما ارسال می‌شود.", parse_mode="Markdown")
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📤 ارسال گانفیک", callback_data=f"approve_{order_id}"))
    send_to_admins(f"💰 **پرداخت با کیف پول**\nسفارش {order_id}\nکاربر {user_id}\nپلن {plan_name}\nتعداد {qty}\nمبلغ {final_amount} تومان\nکد پیگیری {tracking}", reply_markup=markup)
    del temp_purchase[user_id]

@bot.callback_query_handler(func=lambda call: call.data.startswith("send_receipt_"))
def send_receipt_prompt(call):
    if not is_admin(call.from_user.id) and is_bot_disabled():
        bot.answer_callback_query(call.id, "ربات غیرفعال است", show_alert=True)
        return
    parts = call.data.split("_")
    if len(parts) < 4:
        bot.answer_callback_query(call.id, "خطا در داده")
        return
    plan_key = parts[2]
    qty = int(parts[3])
    discount = parts[4] if len(parts) > 4 else None
    user_id = call.from_user.id
    if user_id not in temp_purchase:
        bot.answer_callback_query(call.id, "خطا. دوباره تلاش کن.")
        return
    
    msg = bot.send_message(call.message.chat.id, "📸 **لطفاً تصویر رسید واریز را ارسال کن.**\n(فقط عکس)", reply_markup=back_keyboard(), parse_mode="Markdown")
    bot.register_next_step_handler(msg, receive_receipt, plan_key, qty, discount)
    bot.answer_callback_query(call.id)

def receive_receipt(msg, plan_key, qty, discount):
    if msg.text == "🔙 بازگشت به منو":
        back_main(msg)
        return
    if not msg.photo:
        bot.send_message(msg.chat.id, "❌ فقط عکس.", reply_markup=buy_keyboard())
        return
    user_id = msg.from_user.id
    data = temp_purchase.get(user_id)
    if not data:
        bot.send_message(msg.chat.id, "❌ خطا. دوباره تلاش کن.")
        return
    final_amount = data["final_amount"]
    original_amount = data["original_amount"]
    plan_name = data["plan"]
    photo_id = msg.photo[-1].file_id
    tracking = generate_tracking_code()
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO orders (user_id, plan, original_amount, final_amount, discount_code, method, tracking_code, status, timestamp, receipt_photo, qty)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (user_id, plan_name, str(original_amount), str(final_amount), data.get("discount_code"), "card", tracking, "pending", int(time.time()), photo_id, qty))
    db.commit()
    order_id = cur.lastrowid
    cur.close()
    db.close()
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ تایید و ارسال گانفیک", callback_data=f"approve_{order_id}"),
               InlineKeyboardButton("❌ رد", callback_data=f"reject_{order_id}"))
    caption = f"🧾 **رسید جدید**\n🆔 سفارش: {order_id}\n👤 کاربر: {user_id}\n📦 {plan_name}\n🔢 تعداد: {qty}\n💰 مبلغ نهایی: {final_amount:,} تومان\n🔢 کد پیگیری: {tracking}"
    send_photo_to_admins(photo_id, caption=caption, reply_markup=markup)
    bot.send_message(user_id, f"✅ **رسید شما ارسال شد.**\n🔢 کد پیگیری: `{tracking}`\nپس از تأیید ادمین، گانفیک ارسال می‌شود.", parse_mode="Markdown", reply_markup=main_keyboard())
    del temp_purchase[user_id]

# ================= تایید سفارش =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") and not call.data.startswith("approve_agent_"))
def approve_order(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "شما ادمین نیستید!", show_alert=True)
        return
    
    parts = call.data.split("_")
    if len(parts) < 2:
        bot.answer_callback_query(call.id, "خطا در داده")
        return
    
    try:
        order_id = int(parts[1])
    except ValueError:
        bot.answer_callback_query(call.id, "خطا در شناسه سفارش")
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT status, user_id, plan, final_amount, tracking_code, qty FROM orders WHERE order_id=?", (order_id,))
    row = cur.fetchone()
    if not row:
        bot.answer_callback_query(call.id, "سفارش یافت نشد.")
        cur.close()
        db.close()
        return
    status, user_id, plan, final_amount, tracking, qty = row
    if status not in ['pending', 'paid']:
        bot.answer_callback_query(call.id, f"سفارش قبلاً {status} شده است.")
        cur.close()
        db.close()
        return
    cur.execute("UPDATE orders SET status='approved' WHERE order_id=?", (order_id,))
    db.commit()
    cur.close()
    db.close()
    
    try:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    except Exception as e:
        print(f"Error removing buttons: {e}")
    bot.answer_callback_query(call.id, "حالا گانفیک را بفرست.")
    msg = bot.send_message(call.message.chat.id, f"📤 **لطفاً گانفیک (لینک یا فایل) را برای کاربر {user_id} ارسال کن.**\nسفارش {order_id}\nپلن {plan}\nتعداد {qty}\nمبلغ {final_amount} تومان\nکد پیگیری {tracking}")
    bot.register_next_step_handler(msg, deliver_gunfic, user_id, plan, tracking, order_id, final_amount, qty)

def deliver_gunfic(message, user_id, plan, tracking, order_id, final_amount, qty):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("📞 پشتیبانی", url=f"tg://user?id={ADMIN_IDS[0]}"),
               InlineKeyboardButton("🛒 خرید مجدد", callback_data="buy_plans_inline"))
    try:
        if message.content_type == 'text':
            link = message.text.strip()
            full_text = f"""
🎉 **خرید شما با موفقیت انجام شد!** ✅
از انتخاب شما سپاسگزاریم 🌟

🔐 **مشخصات اشتراک شما:**
━━━━━━━━━━━━━━━━━━━━━
🗓️ **نوع محصول:** {plan}
🔢 **تعداد:** {qty}
💰 **مبلغ پرداختی:** {final_amount} تومان
🔢 **کد پیگیری:** `{tracking}`
🕓 **مدت اعتبار:** 100 روز
━━━━━━━━━━━━━━━━━━━━━

🎮 **لینک کانفیگ (گانفیک) شما:**
`{link}`

⚠️ **نحوه استفاده:**
1️⃣ روی لینک فشار طولانی بده و کپی کن
2️⃣ در برنامه VPN خود وارد کن
3️⃣ Refresh/Update بزن
"""
            bot.send_message(user_id, full_text, parse_mode="Markdown", reply_markup=main_keyboard())
        elif message.content_type == 'document':
            file_id = message.document.file_id
            full_text = f"""
🎉 **خرید شما موفقیت‌آمیز بود!**
پلن: {plan} - تعداد: {qty} - کد پیگیری: {tracking}
فایل کانفیگ در زیر ارسال شده است.
"""
            bot.send_message(user_id, full_text, reply_markup=main_keyboard())
            bot.send_document(user_id, file_id)
        else:
            bot.send_message(user_id, f"✅ سفارش {plan} (تعداد {qty}) تایید شد. کد پیگیری: {tracking}", reply_markup=main_keyboard())
            bot.copy_message(user_id, ADMIN_IDS[0], message.message_id)
        
        db = get_db()
        cur = db.cursor()
        cur.execute("UPDATE orders SET status='done' WHERE order_id=?", (order_id,))
        expiry = int(time.time()) + 100 * 86400
        cur.execute("UPDATE users SET plan=?, expiry=? WHERE id=?", (plan, expiry, user_id))
        db.commit()
        cur.close()
        db.close()
        
        user_email = get_user_email(user_id)
        if user_email:
            try:
                msg_email = MIMEText(f"پلن {plan} تایید شد. کد پیگیری: {tracking}", "plain", "utf-8")
                msg_email["Subject"] = "✅ سفارش شما تایید شد - Jigar Tunnel"
                msg_email["From"] = f"Jigar Tunnel <{EMAIL}>"
                msg_email["To"] = user_email
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(EMAIL, APP_PASSWORD)
                server.sendmail(EMAIL, user_email, msg_email.as_string())
                server.quit()
            except:
                pass
        send_to_admins(f"✅ گانفیک برای کاربر {user_id} ارسال شد و ایمیل اطلاع‌رسانی فرستاده شد.")
    except Exception as e:
        send_to_admins(f"❌ خطا در ارسال گانفیک: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_") and not call.data.startswith("reject_agent_"))
def reject_order(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "شما ادمین نیستید!", show_alert=True)
        return
    
    parts = call.data.split("_")
    if len(parts) < 2:
        bot.answer_callback_query(call.id, "خطا در داده")
        return
    
    try:
        order_id = int(parts[1])
    except ValueError:
        bot.answer_callback_query(call.id, "خطا در شناسه سفارش")
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT user_id FROM orders WHERE order_id=?", (order_id,))
    row = cur.fetchone()
    if row:
        user_id = row[0]
        cur.execute("UPDATE orders SET status='rejected' WHERE order_id=?", (order_id,))
        db.commit()
        cur.close()
        db.close()
        try:
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
        except Exception as e:
            print(f"Error removing buttons: {e}")
        bot.send_message(user_id, "❌ سفارش شما رد شد. با پشتیبانی تماس بگیرید.", reply_markup=main_keyboard())
        bot.answer_callback_query(call.id, "رد شد")
    else:
        bot.answer_callback_query(call.id, "نامعتبر")
        cur.close()
        db.close()

# ================= تایید نمایندگی =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_agent_"))
def approve_agent(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "شما ادمین نیستید!", show_alert=True)
        return
    
    parts = call.data.split("_")
    if len(parts) < 3:
        bot.answer_callback_query(call.id, "خطا در داده")
        return
    
    try:
        request_id = int(parts[2])
    except ValueError:
        bot.answer_callback_query(call.id, "خطا در شناسه درخواست")
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT user_id, full_name, national_code, phone_number, daily_sales 
        FROM agent_requests WHERE id=? AND status='pending'
    """, (request_id,))
    row = cur.fetchone()
    
    if not row:
        bot.answer_callback_query(call.id, "درخواست یافت نشد یا قبلاً پردازش شده.")
        cur.close()
        db.close()
        return
    
    user_id, full_name, national_code, phone, daily_sales = row
    
    cur.execute("""
        UPDATE users 
        SET is_agent=1, agent_daily_sales=?, agent_full_name=?, agent_national_code=?, agent_phone=?, agent_approved_at=? 
        WHERE id=?
    """, (daily_sales, full_name, national_code, phone, int(time.time()), user_id))
    
    cur.execute("UPDATE agent_requests SET status='approved', approved_at=? WHERE id=?", (int(time.time()), request_id))
    db.commit()
    cur.close()
    db.close()
    
    try:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    except:
        pass
    
    bot.answer_callback_query(call.id, "✅ نماینده تایید شد")
    bot.send_message(call.message.chat.id, 
        f"✅ **نماینده جدید تایید شد**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **نام:** {full_name}\n"
        f"🆔 **کد ملی:** {national_code}\n"
        f"📞 **شماره:** {phone}\n"
        f"📊 **فروش روزانه:** {daily_sales}\n"
        f"🆔 **آیدی:** `{user_id}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 قیمت ویژه نمایندگی: ۸,۰۰۰ تومان/گیگ",
        parse_mode="Markdown")
    
    bot.send_message(user_id, 
        "🎉 **تبریک! درخواست نمایندگی شما تایید شد.**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **نام:** {full_name}\n"
        f"🆔 **کد ملی:** {national_code}\n"
        f"📞 **شماره تماس:** {phone}\n"
        f"📊 **فروش روزانه:** {daily_sales}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ شما اکنون یک نماینده رسمی JigarTunnel هستید.\n"
        "💰 **قیمت ویژه نمایندگی:** هر گیگ = ۸,۰۰۰ تومان\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🛒 از همین الان می‌توانید با قیمت نمایندگی خرید کنید.",
        parse_mode="Markdown", reply_markup=main_keyboard())

# ================= رد نمایندگی =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_agent_"))
def reject_agent(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "شما ادمین نیستید!", show_alert=True)
        return
    
    parts = call.data.split("_")
    if len(parts) < 3:
        bot.answer_callback_query(call.id, "خطا در داده")
        return
    
    try:
        request_id = int(parts[2])
    except ValueError:
        bot.answer_callback_query(call.id, "خطا در شناسه درخواست")
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT user_id, full_name FROM agent_requests WHERE id=? AND status='pending'", (request_id,))
    row = cur.fetchone()
    
    if not row:
        bot.answer_callback_query(call.id, "درخواست یافت نشد.")
        cur.close()
        db.close()
        return
    
    user_id, full_name = row
    cur.execute("UPDATE agent_requests SET status='rejected', rejected_at=? WHERE id=?", (int(time.time()), request_id))
    db.commit()
    cur.close()
    db.close()
    
    try:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    except:
        pass
    
    bot.answer_callback_query(call.id, "❌ رد شد")
    bot.send_message(call.message.chat.id, f"❌ درخواست نمایندگی کاربر {user_id} رد شد.")
    bot.send_message(user_id, 
        "❌ **درخواست نمایندگی شما رد شد.**\n"
        f"👤 **نام:** {full_name}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📞 در صورت نیاز با پشتیبانی تماس بگیرید.\n"
        "⚠️ دلیل احتمالی: مدارک ناقص یا نامعتبر.",
        parse_mode="Markdown", reply_markup=main_keyboard())

# ================= کیف پول =================
@bot.message_handler(func=lambda msg: msg.text == "💰 کیف پول")
@bot_enabled_for_users
def wallet_menu(msg):
    user_id = msg.from_user.id
    balance = get_user_balance(user_id)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ شارژ کیف پول", callback_data="charge_wallet"),
               InlineKeyboardButton("📜 تاریخچه تراکنش‌ها", callback_data="wallet_history"))
    bot.send_message(msg.chat.id, f"💰 **موجودی کیف پول شما:** {balance:,} تومان\n\nاز دکمه‌های زیر استفاده کنید:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "charge_wallet")
def charge_wallet(call):
    if not is_admin(call.from_user.id) and is_bot_disabled():
        bot.answer_callback_query(call.id, "ربات غیرفعال است", show_alert=True)
        return
    user_id = call.from_user.id
    
    card_text = f"""
💳 **شارژ کیف پول**

📌 **شماره کارت اول:**
`{CARD_NUMBER_1}`
👤 **به نام:** {CARD_NAME_1}

📌 **شماره کارت دوم:**
`{CARD_NUMBER_2}`
👤 **به نام:** {CARD_NAME_2}

⚠️ **پس از واریز، رسید را ارسال کنید.**
"""
    bot.send_message(call.message.chat.id, card_text, parse_mode="Markdown")
    msg = bot.send_message(call.message.chat.id, "📸 **لطفاً تصویر رسید را ارسال کنید:**", reply_markup=back_keyboard(), parse_mode="Markdown")
    bot.register_next_step_handler(msg, receive_charge_receipt, user_id)
    bot.answer_callback_query(call.id)

def receive_charge_receipt(msg, user_id):
    if msg.text == "🔙 بازگشت به منو":
        back_main(msg)
        return
    if not msg.photo:
        bot.send_message(msg.chat.id, "❌ فقط عکس.", reply_markup=main_keyboard())
        return
    photo_id = msg.photo[-1].file_id
    tracking = generate_tracking_code()
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO orders (user_id, plan, original_amount, final_amount, method, tracking_code, status, timestamp, receipt_photo) VALUES (?,?,?,?,?,?,?,?,?)",
                (user_id, "شارژ کیف پول", "0", "0", "charge", tracking, "pending_charge", int(time.time()), photo_id))
    db.commit()
    order_id = cur.lastrowid
    cur.close()
    db.close()
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ تایید شارژ", callback_data=f"approve_charge_{order_id}"),
               InlineKeyboardButton("❌ رد", callback_data=f"reject_charge_{order_id}"))
    caption = f"💰 **درخواست شارژ کیف پول**\n🆔 سفارش: {order_id}\n👤 کاربر: {user_id}\n🔢 کد پیگیری: {tracking}"
    send_photo_to_admins(photo_id, caption=caption, reply_markup=markup)
    bot.send_message(user_id, f"✅ **رسید شما ارسال شد.**\n🔢 کد پیگیری: {tracking}", parse_mode="Markdown", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_charge_"))
def approve_charge(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "شما ادمین نیستید!", show_alert=True)
        return
    order_id = int(call.data.split("_")[2])
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT user_id FROM orders WHERE order_id=? AND status='pending_charge'", (order_id,))
    row = cur.fetchone()
    if not row:
        bot.answer_callback_query(call.id, "سفارش یافت نشد یا قبلاً پردازش شده.")
        cur.close()
        db.close()
        return
    user_id = row[0]
    cur.close()
    db.close()
    
    try:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    except Exception as e:
        print(f"Error removing buttons: {e}")
    bot.send_message(call.message.chat.id, f"💰 **مبلغ شارژ را به تومان وارد کنید** (برای کاربر {user_id}):\n(برای برگشت مبلغ اشتباه، عدد منفی وارد کنید)")
    bot.register_next_step_handler(call.message, set_charge_amount, user_id, order_id)
    bot.answer_callback_query(call.id)

def set_charge_amount(msg, user_id, order_id):
    if not is_admin(msg.from_user.id):
        return
    try:
        amount = int(msg.text.strip())
    except:
        bot.send_message(msg.chat.id, "❌ مبلغ نامعتبر. لطفاً یک عدد صحیح وارد کنید.")
        bot.register_next_step_handler(msg, set_charge_amount, user_id, order_id)
        return
    if amount == 0:
        bot.send_message(msg.chat.id, "❌ مبلغ نمی‌تواند صفر باشد. دوباره وارد کنید:")
        bot.register_next_step_handler(msg, set_charge_amount, user_id, order_id)
        return
    update_balance(user_id, amount, f"شارژ/برگشت کیف پول به مبلغ {abs(amount)} تومان" + (" (شارژ)" if amount>0 else " (برگشت)"))
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE orders SET status='done', final_amount=? WHERE order_id=?", (str(abs(amount)), order_id))
    db.commit()
    cur.close()
    db.close()
    if amount > 0:
        bot.send_message(user_id, f"✅ **کیف پول شما به مبلغ {amount:,} تومان شارژ شد.**", parse_mode="Markdown")
        bot.send_message(msg.chat.id, f"✅ شارژ {amount:,} تومان برای کاربر {user_id} انجام شد.", parse_mode="Markdown")
    else:
        bot.send_message(user_id, f"⚠️ **مبلغ {abs(amount):,} تومان از کیف پول شما کسر شد.** (برگشت مبلغ اشتباه)", parse_mode="Markdown")
        bot.send_message(msg.chat.id, f"⚠️ کسر {abs(amount):,} تومان از کیف پول کاربر {user_id} انجام شد.", parse_mode="Markdown")
    send_to_admins(f"✅ سفارش شارژ کیف پول {order_id} برای کاربر {user_id} با مبلغ {abs(amount)} تومان تکمیل شد.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_charge_"))
def reject_charge(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "شما ادمین نیستید!", show_alert=True)
        return
    order_id = int(call.data.split("_")[2])
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT user_id FROM orders WHERE order_id=? AND status='pending_charge'", (order_id,))
    row = cur.fetchone()
    if not row:
        bot.answer_callback_query(call.id, "سفارش یافت نشد یا قبلاً پردازش شده.")
        cur.close()
        db.close()
        return
    user_id = row[0]
    cur.execute("UPDATE orders SET status='rejected' WHERE order_id=?", (order_id,))
    db.commit()
    cur.close()
    db.close()
    try:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    except Exception as e:
        print(f"Error removing buttons: {e}")
    bot.answer_callback_query(call.id, "رسید رد شد.")
    bot.send_message(user_id, "❌ درخواست شارژ کیف پول شما رد شد. لطفاً با پشتیبانی تماس بگیرید.", parse_mode="Markdown")
    send_to_admins(f"❌ درخواست شارژ کیف پول (سفارش {order_id}) توسط ادمین رد شد.")

@bot.callback_query_handler(func=lambda call: call.data == "wallet_history")
def wallet_history(call):
    if not is_admin(call.from_user.id) and is_bot_disabled():
        bot.answer_callback_query(call.id, "ربات غیرفعال است", show_alert=True)
        return
    user_id = call.from_user.id
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT amount, type, description, timestamp FROM balance_history WHERE user_id=? ORDER BY timestamp DESC LIMIT 20", (user_id,))
    rows = cur.fetchall()
    cur.close()
    db.close()
    if not rows:
        text = "📭 هیچ تراکنشی یافت نشد."
    else:
        text = "📜 **آخرین تراکنش‌ها:**\n\n"
        for r in rows:
            sign = "+" if r[1] == 'credit' else "-"
            text += f"{sign}{abs(r[0]):,} تومان | {r[2]} | {time.ctime(r[3])}\n"
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# ================= تیکت‌ها =================
@bot.message_handler(func=lambda msg: msg.text == "🎫 تیکت‌های من")
@bot_enabled_for_users
def my_tickets_menu(msg):
    user_id = msg.from_user.id
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT ticket_id, title, status, created_at FROM tickets WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    tickets = cur.fetchall()
    cur.close()
    db.close()
    text = "📋 **تیکت‌های شما:**\n\n" if tickets else "شما هیچ تیکتی ثبت نکرده‌اید.\n\n"
    for t in tickets:
        status = "🟢 باز" if t[2] == 'open' else "🔴 بسته"
        text += f"#{t[0]} - {t[1]} ({status}) - {time.ctime(t[3])}\n"
    bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=main_keyboard())
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ تیکت جدید", callback_data="new_ticket"),
               InlineKeyboardButton("📨 مشاهده تیکت", callback_data="view_ticket"))
    bot.send_message(msg.chat.id, "از دکمه‌های زیر استفاده کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "new_ticket")
def new_ticket_prompt(call):
    if not is_admin(call.from_user.id) and is_bot_disabled():
        bot.answer_callback_query(call.id, "ربات غیرفعال است", show_alert=True)
        return
    bot.send_message(call.message.chat.id, "✏️ **عنوان تیکت را وارد کنید:**", parse_mode="Markdown")
    bot.register_next_step_handler(call.message, get_ticket_title, call.from_user.id)
    bot.answer_callback_query(call.id)

def get_ticket_title(msg, user_id):
    title = msg.text.strip()
    if not title:
        bot.send_message(msg.chat.id, "❌ عنوان نمی‌تواند خالی باشد.")
        return
    bot.send_message(msg.chat.id, "📝 **متن سؤال یا مشکل خود را بنویسید:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_ticket_message, user_id, title)

def save_ticket_message(msg, user_id, title):
    message_text = msg.text.strip()
    ticket_id = random.randint(100000, 999999)
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO tickets (ticket_id, user_id, title, status, created_at) VALUES (?,?,?,?,?)",
                (ticket_id, user_id, title, 'open', int(time.time())))
    db.commit()
    cur.execute("INSERT INTO ticket_messages (ticket_id, sender_id, sender_role, message, timestamp) VALUES (?,?,?,?,?)",
                (ticket_id, user_id, 'user', message_text, int(time.time())))
    db.commit()
    cur.close()
    db.close()
    bot.send_message(msg.chat.id, f"✅ **تیکت شما با شماره `{ticket_id}` ثبت شد.**", parse_mode="Markdown", reply_markup=main_keyboard())
    send_to_admins(f"🆕 **تیکت جدید** #{ticket_id}\nعنوان: {title}\nاز کاربر: {user_id}\nمتن: {message_text}")

@bot.callback_query_handler(func=lambda call: call.data == "view_ticket")
def view_ticket_prompt(call):
    if not is_admin(call.from_user.id) and is_bot_disabled():
        bot.answer_callback_query(call.id, "ربات غیرفعال است", show_alert=True)
        return
    bot.send_message(call.message.chat.id, "🔢 **شماره تیکت را وارد کنید:**", reply_markup=back_keyboard(), parse_mode="Markdown")
    bot.register_next_step_handler(call.message, show_ticket_by_id, call.from_user.id)
    bot.answer_callback_query(call.id)

def show_ticket_by_id(msg, user_id):
    if msg.text == "🔙 بازگشت به منو":
        back_main(msg)
        return
    try:
        ticket_id = int(msg.text)
    except:
        bot.send_message(msg.chat.id, "❌ شماره نامعتبر.", reply_markup=main_keyboard())
        return
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT user_id, title, status FROM tickets WHERE ticket_id=?", (ticket_id,))
    ticket = cur.fetchone()
    if not ticket or ticket[0] != user_id:
        cur.close()
        db.close()
        bot.send_message(msg.chat.id, "❌ تیکت یافت نشد.", reply_markup=main_keyboard())
        return
    cur.execute("SELECT sender_role, message, timestamp FROM ticket_messages WHERE ticket_id=? ORDER BY timestamp ASC", (ticket_id,))
    messages = cur.fetchall()
    cur.close()
    db.close()
    text = f"💬 **تیکت #{ticket_id} - {ticket[1]}** ({'باز' if ticket[2]=='open' else 'بسته'})\n\n"
    for m in messages:
        role = "شما" if m[0] == 'user' else "پشتیبان"
        text += f"{role} ({time.ctime(m[2])}):\n{m[1]}\n\n"
    markup = None
    if ticket[2] == 'open':
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📨 پاسخ جدید", callback_data=f"reply_ticket_{ticket_id}"),
                   InlineKeyboardButton("🔒 بستن تیکت", callback_data=f"close_ticket_{ticket_id}"))
    bot.send_message(msg.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_ticket_"))
def reply_ticket_prompt(call):
    if not is_admin(call.from_user.id) and is_bot_disabled():
        bot.answer_callback_query(call.id, "ربات غیرفعال است", show_alert=True)
        return
    ticket_id = int(call.data.split("_")[2])
    user_id = call.from_user.id
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT status FROM tickets WHERE ticket_id=? AND user_id=?", (ticket_id, user_id))
    row = cur.fetchone()
    cur.close()
    db.close()
    if not row or row[0] != 'open':
        bot.answer_callback_query(call.id, "تیکت بسته است یا وجود ندارد.", show_alert=True)
        return
    bot.send_message(call.message.chat.id, "✏️ **پیام خود را بنویسید:**", parse_mode="Markdown")
    bot.register_next_step_handler(call.message, add_user_reply, ticket_id, user_id)
    bot.answer_callback_query(call.id)

def add_user_reply(msg, ticket_id, user_id):
    reply_text = msg.text.strip()
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO ticket_messages (ticket_id, sender_id, sender_role, message, timestamp) VALUES (?,?,?,?,?)",
                (ticket_id, user_id, 'user', reply_text, int(time.time())))
    db.commit()
    cur.close()
    db.close()
    bot.send_message(msg.chat.id, "✅ **پیام شما ارسال شد. پشتیبان پاسخ خواهد داد.**", reply_markup=main_keyboard())
    send_to_admins(f"📨 **پیام جدید در تیکت #{ticket_id}**\nاز کاربر {user_id}:\n{reply_text}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("close_ticket_"))
def close_ticket_user(call):
    if not is_admin(call.from_user.id) and is_bot_disabled():
        bot.answer_callback_query(call.id, "ربات غیرفعال است", show_alert=True)
        return
    ticket_id = int(call.data.split("_")[2])
    user_id = call.from_user.id
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE tickets SET status='closed', closed_at=? WHERE ticket_id=? AND user_id=?", (int(time.time()), ticket_id, user_id))
    if cur.rowcount:
        db.commit()
        bot.answer_callback_query(call.id, "✅ تیکت بسته شد.")
        bot.send_message(call.message.chat.id, f"🔒 **تیکت #{ticket_id} بسته شد.**", reply_markup=main_keyboard())
    else:
        bot.answer_callback_query(call.id, "خطا.", show_alert=True)
    cur.close()
    db.close()

# ================= سایر دکمه‌ها =================
@bot.message_handler(func=lambda msg: msg.text == "🛒 خرید اشتراک")
@bot_enabled_for_users
def handle_buy(msg):
    bot.send_message(msg.chat.id, "📦 **پلن‌های موجود (۱۰۰ روزه):**\n✅ 10 گیگ = ۹۰,۰۰۰ تومان\n✅ 20 گیگ = ۱۸۰,۰۰۰ تومان\n✅ 30 گیگ = ۲۷۰,۰۰۰ تومان\n✅ 50 گیگ = ۴۵۰,۰۰۰ تومان\n\nلطفاً یکی را انتخاب کن:", reply_markup=buy_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text.startswith("🗓️"))
def handle_plan(msg):
    user_id = msg.from_user.id
    if not is_admin(user_id) and is_bot_disabled():
        bot.send_message(user_id, f"🔴 **ربات در حال حاضر غیرفعال است.**\nعلت: {get_disable_reason()}\nلطفاً بعداً مراجعه کنید.", parse_mode="Markdown")
        return
    text = msg.text
    if "10 گیگ" in text:
        plan_key = "10"; plan_name = "10 گیگ"; amount_str = "90000"
    elif "20 گیگ" in text:
        plan_key = "20"; plan_name = "20 گیگ"; amount_str = "180000"
    elif "30 گیگ" in text:
        plan_key = "30"; plan_name = "30 گیگ"; amount_str = "270000"
    elif "50 گیگ" in text:
        plan_key = "50"; plan_name = "50 گیگ"; amount_str = "450000"
    else:
        return
    if not is_plan_available(plan_key):
        bot.send_message(msg.chat.id, f"❌ پلن {plan_key} گیگ ناموجود است.")
        return
    bot.send_message(user_id, "📦 **تعداد مورد نظر را وارد کن:** (پیش‌فرض 1)")
    bot.register_next_step_handler(msg, ask_quantity, plan_key, plan_name, amount_str)

def ask_quantity(message, plan_key, plan_name, amount_str):
    user_id = message.from_user.id
    try:
        qty = int(message.text.strip())
        if qty < 1:
            qty = 1
    except:
        qty = 1
    original_amount = int(amount_str) * qty
    bot.send_message(user_id, "🎫 **کد تخفیف داری؟ (ندارم را بفرست)**")
    bot.register_next_step_handler(message, ask_discount, plan_key, plan_name, original_amount, qty)

def ask_discount(message, plan_key, plan_name, original_amount, qty):
    user_id = message.from_user.id
    discount_code = message.text.strip()
    final_amount = original_amount
    applied = None
    if discount_code.lower() != "ندارم":
        final_amount, err = apply_discount_code(discount_code, original_amount)
        if err:
            bot.send_message(user_id, f"⚠️ {err}\nبدون تخفیف ادامه می‌دهید.")
        else:
            applied = discount_code
            consume_discount_code(discount_code)
    temp_purchase[user_id] = {
        "plan": plan_name,
        "original_amount": original_amount,
        "final_amount": final_amount,
        "plan_key": plan_key,
        "qty": qty,
        "discount_code": applied,
        "method": None
    }
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("💳 کارت به کارت", callback_data=f"pay_card_{plan_key}_{qty}_{applied if applied else ''}"),
               InlineKeyboardButton("💰 کیف پول", callback_data=f"pay_wallet_{plan_key}_{qty}_{applied if applied else ''}"))
    bot.send_message(user_id, f"🧾 **پلن:** {plan_name}\n📦 **تعداد:** {qty}\n💰 **مبلغ نهایی:** {final_amount:,} تومان\n\nروش پرداخت را انتخاب کنید:", reply_markup=markup, parse_mode="Markdown")

# ================= دکمه حساب کاربری =================
@bot.message_handler(func=lambda msg: msg.text == "👤 حساب کاربری")
@bot_enabled_for_users
def account_button(message):
    user_id = message.from_user.id
    email = get_user_email(user_id) or "ثبت نشده"
    balance = get_user_balance(user_id)
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT plan, expiry, is_agent, agent_full_name FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    cur.close()
    db.close()
    
    agent_status = "✅ نماینده" if row and row[2] == 1 else "❌ کاربر عادی"
    agent_name = f" ({row[3]})" if row and row[2] == 1 and row[3] else ""
    
    if row and row[0]:
        plan, expiry = row[0], row[1]
        remain = max(0, (expiry - int(time.time())) // 86400)
        text = f"""👤 **حساب کاربری شما**
━━━━━━━━━━━━━━━━━━━━━
📧 **ایمیل:** {email}
💰 **موجودی:** {balance:,} تومان
📦 **پلن فعال:** {plan}
⏳ **روزهای باقی‌مانده:** {remain}
🤝 **وضعیت:** {agent_status}{agent_name}"""
    else:
        text = f"""👤 **حساب کاربری شما**
━━━━━━━━━━━━━━━━━━━━━
📧 **ایمیل:** {email}
💰 **موجودی:** {balance:,} تومان
📦 **پلن فعال:** هیچ
🤝 **وضعیت:** {agent_status}{agent_name}"""
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔄 تمدید اشتراک", callback_data="buy_plans_inline"),
        InlineKeyboardButton("🔐 غیرفعال کردن حساب", callback_data="disable_account")
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "disable_account")
def disable_account(call):
    user_id = call.from_user.id
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE users SET disabled=1 WHERE id=?", (user_id,))
    db.commit()
    cur.close()
    db.close()
    bot.answer_callback_query(call.id, "حساب شما غیرفعال شد. در صورت نیاز با پشتیبانی تماس بگیرید.", show_alert=True)
    bot.send_message(call.message.chat.id, "🔐 **حساب کاربری شما غیرفعال شد.** برای فعالسازی مجدد با ادمین تماس بگیرید.", reply_markup=main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "📞 پشتیبانی")
def support_button(message):
    bot.send_message(message.chat.id, f"📞 **ارسال پیام به پشتیبان:**\n[کلیک کن](tg://user?id={ADMIN_IDS[0]})", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "ℹ️ درباره ما")
@bot_enabled_for_users
def about_button(message):
    about_text = f"""
ℹ️ **درباره {BOT_NAME}** 🔥
━━━━━━━━━━━━━━━━━━━━━
ما یه تیم حرفه‌ای در حوزه **شبکه و فیلترشکن** هستیم.

🎯 **هدف:** اینترنت آزاد، پایدار و امن برای همه

⚡ **خدمات:**
• سرورهای پرسرعت و با پینگ پایین
• پشتیبانی ۲۴ ساعته
• بدون محدودیت حجمی
• کانفیگ‌های اختصاصی

💰 **چرا ما؟**
• قیمت مناسب و رقابتی
• ارسال سریع گانفیک
• پرداخت آسان کارت به کارت
• امکان پرداخت از کیف پول

🛡️ حریم خصوصی اولویت ماست.

🤝 **همکاری:** اگر فروشنده هستید، از دکمه درخواست نمایندگی استفاده کنید.
"""
    bot.send_message(message.chat.id, about_text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📜 قوانین")
@bot_enabled_for_users
def rules_button(message):
    rules_text = f"""
🚨 **قوانین فروشگاه {BOT_NAME}** 🚨
━━━━━━━━━━━━━━━━━━━━━

1️⃣ **رسید جعلی ممنوع** → مسدودیت دائمی
2️⃣ **واریز دقیق مبلغ** → تأخیر در تحویل
3️⃣ **عدم انصراف پس از ارسال گانفیک**
4️⃣ **مسئولیت نگهداری کانفیگ با شماست**
5️⃣ **پشتیبانی فقط در ربات**
6️⃣ **تغییر قیمت‌ها محفوظ است**
7️⃣ **زمان ارسال گانفیک حداکثر 12 ساعت**
8️⃣ **بدون تأیید رسید، گانفیک ارسال نمی‌شود**

⚠️ **تخلف = مسدودیت دائمی**
"""
    bot.send_message(message.chat.id, rules_text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🔙 بازگشت به منو")
def back_main(message):
    bot.send_message(message.chat.id, "🔹 **منوی اصلی** 🔹", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "buy_plans_inline")
def buy_plans_inline(call):
    handle_buy(call.message)
    bot.answer_callback_query(call.id)

# ================= پنل مدیریت =================
@bot.message_handler(commands=['panel', 'admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ شما دسترسی به این بخش ندارید!")
        return
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 آمار", callback_data="admin_stats"),
        InlineKeyboardButton("📋 کاربران", callback_data="admin_users"),
        InlineKeyboardButton("🔍 جستجو", callback_data="admin_search"),
        InlineKeyboardButton("📝 سفارشات", callback_data="admin_orders"),
        InlineKeyboardButton("✉️ ارسال همگانی", callback_data="admin_broadcast"),
        InlineKeyboardButton("🎫 کد تخفیف", callback_data="admin_discounts"),
        InlineKeyboardButton("📦 وضعیت پلن‌ها", callback_data="admin_plans"),
        InlineKeyboardButton("⛔ مدیریت بن", callback_data="admin_ban"),
        InlineKeyboardButton("🎫 تیکت‌ها", callback_data="admin_tickets"),
        InlineKeyboardButton("💰 کیف پول", callback_data="admin_wallet"),
        InlineKeyboardButton("🔓 فعال‌سازی حساب", callback_data="admin_enable_account"),
        InlineKeyboardButton("🔒 خاموشی ربات", callback_data="admin_toggle_bot"),
        InlineKeyboardButton("🤝 مدیریت نمایندگی", callback_data="admin_agents")
    )
    bot.send_message(message.chat.id, "🔧 **پنل مدیریت Jigar Tunnel**\n━━━━━━━━━━━━━━━━━━━━━\n👤 ادمین عزیز خوش آمدید.", reply_markup=markup, parse_mode="Markdown")

# ================= بخش نمایندگی (بدون عکس) =================
@bot.message_handler(func=lambda msg: msg.text == "🤝 درخواست نمایندگی")
@bot_enabled_for_users
def request_agency(message):
    user_id = message.from_user.id
    
    if is_agent(user_id):
        bot.send_message(user_id, 
            "✅ **شما قبلاً نماینده هستید!**\n"
            "💰 قیمت ویژه نمایندگی: هر گیگ = ۸,۰۰۰ تومان",
            parse_mode="Markdown")
        return
    
    if has_pending_agent_request(user_id):
        bot.send_message(user_id, 
            "⏳ **شما قبلاً درخواست نمایندگی ثبت کردید.**\n"
            "🕐 منتظر تایید ادمین باشید.",
            parse_mode="Markdown")
        return
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("زیر 10 تا"), KeyboardButton("10 تا 50 تا"), KeyboardButton("بالای 50 تا"))
    markup.add(KeyboardButton("🔙 بازگشت به منو"))
    
    msg = bot.send_message(user_id, 
        "🤝 **فرم درخواست نمایندگی**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 **فروش روزانه شما چند تاست؟**\n"
        "⚠️ لطفاً دقیق وارد کنید تا سطح نمایندگی شما مشخص شود.",
        reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_agent_full_name, user_id)

def ask_agent_full_name(message, user_id):
    if message.text == "🔙 بازگشت به منو":
        back_main(message)
        return
    
    daily_sales = message.text
    if daily_sales not in ["زیر 10 تا", "10 تا 50 تا", "بالای 50 تا"]:
        bot.send_message(user_id, "❌ لطفاً یکی از گزینه‌ها را انتخاب کنید.")
        msg = bot.send_message(user_id, "📊 فروش روزانه شما چند تاست؟")
        bot.register_next_step_handler(msg, ask_agent_full_name, user_id)
        return
    
    temp_agent_data[user_id] = {"daily_sales": daily_sales}
    
    msg = bot.send_message(user_id, 
        "👤 **لطفاً نام و نام خانوادگی کامل خود را وارد کنید:**\n"
        "مثال: `علی محمدی`",
        reply_markup=back_keyboard(), parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_agent_national_code, user_id)

def ask_agent_national_code(message, user_id):
    if message.text == "🔙 بازگشت به منو":
        back_main(message)
        return
    
    full_name = message.text.strip()
    if len(full_name) < 3:
        bot.send_message(user_id, "❌ نام کامل معتبر نیست. لطفاً دوباره وارد کنید:")
        msg = bot.send_message(user_id, "👤 نام و نام خانوادگی:", reply_markup=back_keyboard())
        bot.register_next_step_handler(msg, ask_agent_national_code, user_id)
        return
    
    temp_agent_data[user_id]["full_name"] = full_name
    
    msg = bot.send_message(user_id, 
        "🆔 **لطفاً کد ملی خود را وارد کنید:**\n"
        "(۱۰ رقم بدون خط تیره)\n"
        "مثال: `۱۲۳۴۵۶۷۸۹۰`",
        reply_markup=back_keyboard(), parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_agent_phone, user_id)

def ask_agent_phone(message, user_id):
    if message.text == "🔙 بازگشت به منو":
        back_main(message)
        return
    
    national_code = message.text.strip()
    if not national_code.isdigit() or len(national_code) != 10:
        bot.send_message(user_id, "❌ کد ملی باید ۱۰ رقم باشد. لطفاً دوباره وارد کنید:")
        msg = bot.send_message(user_id, "🆔 کد ملی (۱۰ رقم):", reply_markup=back_keyboard())
        bot.register_next_step_handler(msg, ask_agent_phone, user_id)
        return
    
    temp_agent_data[user_id]["national_code"] = national_code
    
    msg = bot.send_message(user_id, 
        "📞 **لطفاً شماره تماس خود را وارد کنید:**\n"
        "مثال: `۰۹۱۲۳۴۵۶۷۸۹`",
        reply_markup=back_keyboard(), parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_agent_request, user_id)

def save_agent_request(message, user_id):
    if message.text == "🔙 بازگشت به منو":
        back_main(message)
        return
    
    phone = message.text.strip()
    if not phone.startswith("09") or len(phone) != 11 or not phone.isdigit():
        bot.send_message(user_id, "❌ شماره تماس نامعتبر. باید ۱۱ رقم و با ۰۹ شروع شود.")
        msg = bot.send_message(user_id, "📞 شماره تماس (۱۱ رقم):", reply_markup=back_keyboard())
        bot.register_next_step_handler(msg, save_agent_request, user_id)
        return
    
    temp_agent_data[user_id]["phone"] = phone
    
    data = temp_agent_data.get(user_id, {})
    full_name = data.get("full_name", "")
    national_code = data.get("national_code", "")
    daily_sales = data.get("daily_sales", "")
    
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO agent_requests 
        (user_id, full_name, national_code, phone_number, daily_sales, status, created_at)
        VALUES (?,?,?,?,?,?,?)
    """, (
        user_id,
        full_name,
        national_code,
        phone,
        daily_sales,
        'pending',
        int(time.time())
    ))
    db.commit()
    request_id = cur.lastrowid
    cur.close()
    db.close()
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ تایید نمایندگی", callback_data=f"approve_agent_{request_id}"),
        InlineKeyboardButton("❌ رد نمایندگی", callback_data=f"reject_agent_{request_id}")
    )
    
    caption = (
        f"🤝 **درخواست نمایندگی جدید**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 **آیدی کاربر:** `{user_id}`\n"
        f"👤 **نام و نام خانوادگی:** {full_name}\n"
        f"🆔 **کد ملی:** {national_code}\n"
        f"📞 **شماره تماس:** {phone}\n"
        f"📊 **فروش روزانه:** {daily_sales}\n"
        f"🕐 **زمان ثبت:** {time.ctime()}\n"
    )
    
    send_to_admins(caption, reply_markup=markup)
    
    bot.send_message(user_id, 
        "✅ **درخواست نمایندگی شما با موفقیت ثبت شد.**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **نام:** {full_name}\n"
        f"🆔 **کد ملی:** {national_code}\n"
        f"📞 **شماره:** {phone}\n"
        f"📊 **فروش روزانه:** {daily_sales}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "⏳ پس از بررسی توسط ادمین، نتیجه به شما اطلاع داده می‌شود.\n"
        "⏱️ زمان بررسی معمولاً ۲۴ تا ۴۸ ساعت است.",
        parse_mode="Markdown", reply_markup=main_keyboard())
    
    if user_id in temp_agent_data:
        del temp_agent_data[user_id]

# ================= مدیریت نمایندگی‌ها در پنل ادمین =================
@bot.callback_query_handler(func=lambda call: call.data == "admin_agents")
def admin_agents_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    db = get_db()
    cur = db.cursor()
    
    cur.execute("SELECT COUNT(*) FROM agent_requests WHERE status='pending'")
    pending_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM users WHERE is_agent=1")
    agents_count = cur.fetchone()[0]
    cur.close()
    db.close()
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f"📋 درخواست‌های در انتظار ({pending_count})", callback_data="view_agent_requests"),
        InlineKeyboardButton(f"🤝 لیست نماینده‌ها ({agents_count})", callback_data="list_agents_admin"),
        InlineKeyboardButton("🔍 اطلاعات کامل نماینده", callback_data="search_agent_info"),
        InlineKeyboardButton("🗑️ حذف نمایندگی", callback_data="remove_agent_menu"),
        InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="back_to_panel")
    )
    
    bot.send_message(
        call.message.chat.id,
        "🤝 **مدیریت نمایندگی‌ها**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🟡 **درخواست‌های در انتظار:** {pending_count}\n"
        f"✅ **نماینده‌های تایید شده:** {agents_count}",
        reply_markup=markup, parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

# ================= مشاهده درخواست‌های نمایندگی =================
@bot.callback_query_handler(func=lambda call: call.data == "view_agent_requests")
def view_agent_requests(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id, user_id, full_name, national_code, phone_number, daily_sales, created_at
        FROM agent_requests WHERE status='pending'
        ORDER BY created_at ASC
    """)
    requests = cur.fetchall()
    cur.close()
    db.close()
    
    if not requests:
        bot.send_message(call.message.chat.id, "📭 **هیچ درخواست در انتظاری وجود ندارد.**", parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return
    
    for req in requests:
        req_id, user_id, name, national, phone, sales, created = req
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✅ تایید", callback_data=f"approve_agent_{req_id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject_agent_{req_id}")
        )
        
        caption = (
            f"🤝 **درخواست نمایندگی**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **شماره:** {req_id}\n"
            f"👤 **نام:** {name}\n"
            f"🆔 **کد ملی:** {national}\n"
            f"📞 **شماره:** {phone}\n"
            f"📊 **فروش روزانه:** {sales}\n"
            f"🕐 **زمان ثبت:** {time.ctime(created)}\n"
        )
        
        bot.send_message(call.message.chat.id, caption, reply_markup=markup, parse_mode="Markdown")
    
    bot.answer_callback_query(call.id)

# ================= لیست نماینده‌ها در پنل ادمین =================
@bot.callback_query_handler(func=lambda call: call.data == "list_agents_admin")
def list_agents_admin(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id, agent_full_name, agent_national_code, agent_phone, 
               agent_daily_sales, agent_approved_at, balance, email
        FROM users WHERE is_agent=1
        ORDER BY agent_approved_at DESC
    """)
    agents = cur.fetchall()
    cur.close()
    db.close()
    
    if not agents:
        bot.send_message(call.message.chat.id, "📭 **هیچ نماینده‌ای ثبت نشده است.**", parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return
    
    text = "🤝 **لیست کامل نماینده‌ها:**\n━━━━━━━━━━━━━━━━━━━━━\n"
    for i, agent in enumerate(agents, 1):
        user_id, name, national, phone, sales, approved_at, balance, email = agent
        text += f"""
{i}. 👤 **{name}**
   🆔 آیدی: `{user_id}`
   🆔 کد ملی: {national if national else '-'}
   📞 شماره: {phone if phone else '-'}
   📊 فروش روزانه: {sales if sales else '-'}
   💰 موجودی: {balance:,} تومان
   📧 ایمیل: {email if email else '-'}
   🕐 تایید: {time.ctime(approved_at) if approved_at else 'ثبت نشده'}
   ───────────────────
"""
    
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# ================= جستجوی نماینده =================
@bot.callback_query_handler(func=lambda call: call.data == "search_agent_info")
def search_agent_prompt(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    msg = bot.send_message(call.message.chat.id, 
        "🔍 **آیدی عددی نماینده را وارد کنید:**",
        parse_mode="Markdown")
    bot.register_next_step_handler(msg, show_agent_full_info)
    bot.answer_callback_query(call.id)

def show_agent_full_info(message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        user_id = int(message.text.strip())
    except:
        bot.send_message(message.chat.id, "❌ آیدی نامعتبر.")
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id, email, balance, reg_date, plan, expiry, disabled,
               is_agent, agent_daily_sales, agent_full_name, agent_national_code, 
               agent_phone, agent_approved_at
        FROM users WHERE id=? AND is_agent=1
    """, (user_id,))
    agent = cur.fetchone()
    cur.close()
    db.close()
    
    if not agent:
        bot.send_message(message.chat.id, f"❌ کاربر {user_id} نماینده نیست یا یافت نشد.", parse_mode="Markdown")
        return
    
    (uid, email, balance, reg_date, plan, expiry, disabled,
     is_agent, daily_sales, full_name, national_code, phone, approved_at) = agent
    
    remain_days = 0
    if plan:
        remain_days = max(0, (expiry - int(time.time())) // 86400)
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM orders WHERE user_id=?", (user_id,))
    total_orders = cur.fetchone()[0]
    cur.execute("SELECT SUM(final_amount) FROM orders WHERE user_id=? AND status='done'", (user_id,))
    total_sales = cur.fetchone()[0] or 0
    cur.close()
    db.close()
    
    text = f"""
👤 **اطلاعات کامل نماینده**
━━━━━━━━━━━━━━━━━━━━━

📌 **اطلاعات شخصی:**
👤 نام و نام خانوادگی: {full_name}
🆔 کد ملی: {national_code}
📞 شماره تماس: {phone}
📊 فروش روزانه: {daily_sales}
🕐 تاریخ تایید: {time.ctime(approved_at) if approved_at else 'ثبت نشده'}

━━━━━━━━━━━━━━━━━━━━━
📌 **اطلاعات حساب:**
🆔 آیدی: `{uid}`
📧 ایمیل: {email if email else 'ثبت نشده'}
💰 موجودی کیف پول: {balance:,} تومان
📅 تاریخ ثبت نام: {time.ctime(reg_date)}

━━━━━━━━━━━━━━━━━━━━━
📌 **وضعیت اشتراک:**
📦 پلن فعال: {plan if plan else 'هیچ'}
⏳ روزهای باقی‌مانده: {remain_days}
🔓 وضعیت حساب: {'✅ فعال' if disabled == 0 else '🔒 غیرفعال'}

━━━━━━━━━━━━━━━━━━━━━
📊 **آمار فروش:**
📝 تعداد کل سفارشات: {total_orders}
💰 کل فروش: {total_sales:,} تومان

━━━━━━━━━━━━━━━━━━━━━
💰 **قیمت ویژه:** ۸,۰۰۰ تومان/گیگ
"""
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ================= حذف نمایندگی =================
@bot.callback_query_handler(func=lambda call: call.data == "remove_agent_menu")
def remove_agent_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    msg = bot.send_message(call.message.chat.id, 
        "🗑️ **حذف نمایندگی**\n"
        "لطفاً آیدی عددی نماینده را وارد کنید:\n"
        "مثال: `123456789`",
        parse_mode="Markdown")
    bot.register_next_step_handler(msg, remove_agent_by_id)
    bot.answer_callback_query(call.id)

def remove_agent_by_id(message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        user_id = int(message.text.strip())
    except:
        bot.send_message(message.chat.id, "❌ آیدی نامعتبر.")
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, agent_full_name FROM users WHERE id=? AND is_agent=1", (user_id,))
    row = cur.fetchone()
    
    if not row:
        bot.send_message(message.chat.id, f"❌ کاربر {user_id} نماینده نیست یا یافت نشد.")
        cur.close()
        db.close()
        return
    
    name = row[1]
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ بله حذف کن", callback_data=f"confirm_remove_agent_{user_id}"),
        InlineKeyboardButton("❌ انصراف", callback_data="cancel_remove_agent")
    )
    
    bot.send_message(message.chat.id, 
        f"⚠️ **آیا از حذف نمایندگی مطمئن هستید؟**\n"
        f"👤 **نام:** {name}\n"
        f"🆔 **آیدی:** `{user_id}`",
        reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_remove_agent_"))
def confirm_remove_agent(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    user_id = int(call.data.split("_")[3])
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT agent_full_name FROM users WHERE id=? AND is_agent=1", (user_id,))
    row = cur.fetchone()
    
    if not row:
        bot.send_message(call.message.chat.id, "❌ کاربر یافت نشد.")
        cur.close()
        db.close()
        bot.answer_callback_query(call.id)
        return
    
    name = row[0]
    
    cur.execute("""
        UPDATE users 
        SET is_agent=0, agent_daily_sales=NULL, agent_full_name=NULL, 
            agent_national_code=NULL, agent_phone=NULL, agent_approved_at=NULL 
        WHERE id=?
    """, (user_id,))
    db.commit()
    cur.close()
    db.close()
    
    bot.answer_callback_query(call.id, "✅ نمایندگی حذف شد")
    bot.send_message(call.message.chat.id, f"✅ نمایندگی کاربر {name} (آیدی: {user_id}) حذف شد.")
    bot.send_message(user_id, 
        "⚠️ **نمایندگی شما توسط ادمین حذف شد.**\n"
        "در صورت نیاز با پشتیبانی تماس بگیرید.",
        parse_mode="Markdown", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "cancel_remove_agent")
def cancel_remove_agent(call):
    bot.answer_callback_query(call.id, "انصراف")
    bot.send_message(call.message.chat.id, "عملیات لغو شد.")

# ================= بخش ارسال همگانی =================
@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
def admin_broadcast_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    total_users = get_total_users()
    total_agents = get_total_agents()
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f"📢 ارسال به همه کاربران ({total_users})", callback_data="broadcast_all"),
        InlineKeyboardButton(f"🤝 ارسال فقط به نماینده‌ها ({total_agents})", callback_data="broadcast_agents"),
        InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="back_to_panel")
    )
    
    bot.send_message(
        call.message.chat.id,
        "✉️ **ارسال همگانی**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **کل کاربران:** {total_users}\n"
        f"🤝 **نماینده‌ها:** {total_agents}\n"
        f"👤 **کاربران عادی:** {total_users - total_agents}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "لطفاً مخاطبان خود را انتخاب کنید:",
        reply_markup=markup, parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "broadcast_all")
def broadcast_all_prompt(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    total_users = get_total_users()
    msg = bot.send_message(
        call.message.chat.id,
        f"✉️ **ارسال به همه کاربران**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 تعداد کل کاربران فعال: **{total_users}**\n\n"
        f"📝 متن پیام خود را بنویسید (Markdown مجاز):",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_broadcast_all)
    bot.answer_callback_query(call.id)

def process_broadcast_all(message):
    if not is_admin(message.from_user.id):
        return
    
    text = message.text
    success = broadcast_to_users(text)
    
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO broadcast_history (message, recipients, target, timestamp) VALUES (?,?,?,?)",
                (text[:200], success, 'all', int(time.time())))
    db.commit()
    cur.close()
    db.close()
    
    bot.send_message(
        message.chat.id,
        f"✅ **ارسال همگانی انجام شد!**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📤 ارسال موفق: {success}\n"
        f"👥 کل کاربران: {get_total_users()}",
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "broadcast_agents")
def broadcast_agents_prompt(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    total_agents = get_total_agents()
    
    if total_agents == 0:
        bot.send_message(
            call.message.chat.id,
            "📭 **هیچ نماینده‌ای ثبت نشده است!**\n"
            "ابتدا باید نماینده‌ها تایید شوند.",
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id)
        return
    
    msg = bot.send_message(
        call.message.chat.id,
        f"🤝 **ارسال فقط به نماینده‌ها**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 تعداد نماینده‌های فعال: **{total_agents}**\n\n"
        f"📝 متن پیام خود را بنویسید (Markdown مجاز):",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_broadcast_agents)
    bot.answer_callback_query(call.id)

def process_broadcast_agents(message):
    if not is_admin(message.from_user.id):
        return
    
    text = message.text
    success = broadcast_to_agents(text)
    
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO broadcast_history (message, recipients, target, timestamp) VALUES (?,?,?,?)",
                (text[:200], success, 'agents', int(time.time())))
    db.commit()
    cur.close()
    db.close()
    
    bot.send_message(
        message.chat.id,
        f"✅ **ارسال به نماینده‌ها انجام شد!**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📤 ارسال موفق: {success}\n"
        f"🤝 کل نماینده‌ها: {get_total_agents()}",
        parse_mode="Markdown"
    )

# ================= دکمه بازگشت به پنل =================
@bot.callback_query_handler(func=lambda call: call.data == "back_to_panel")
def back_to_panel(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    admin_panel(call.message)
    bot.answer_callback_query(call.id)

# ================= سایر بخش‌های پنل ادمین =================
@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='pending'")
    pending = cur.fetchone()[0]
    cur.execute("SELECT SUM(final_amount) FROM orders WHERE status='done'")
    total_sales = cur.fetchone()[0] or 0
    cur.close()
    db.close()
    
    text = f"📊 **آمار کلی**\n👥 کاربران: {users}\n🕒 در انتظار: {pending}\n💰 فروش کل: {total_sales:,} تومان"
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_users")
def admin_users(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, email, balance, plan FROM users LIMIT 50")
    users = cur.fetchall()
    cur.close()
    db.close()
    
    text = "📋 **لیست کاربران (۵۰ مورد اخیر)**\n\n"
    for u in users:
        text += f"🆔 {u[0]} | 📧 {u[1] if u[1] else '-'} | 💰 {u[2]:,} | 📦 {u[3] if u[3] else '-'}\n"
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_search")
def admin_search(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    msg = bot.send_message(call.message.chat.id, "🔍 **آیدی عددی کاربر، ایمیل یا کد پیگیری را وارد کن:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, search_user)

def search_user(msg):
    if not is_admin(msg.from_user.id):
        return
    
    query = msg.text.strip()
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, email, balance, plan FROM users WHERE id=? OR email=?", (query, query))
    user = cur.fetchone()
    
    if user:
        user_id, email, balance, plan = user
        cur.execute("SELECT order_id, plan, final_amount, status, timestamp FROM orders WHERE user_id=? ORDER BY timestamp DESC LIMIT 1", (user_id,))
        order = cur.fetchone()
        text = f"👤 **کاربر**\n🆔 {user_id}\n📧 {email if email else '-'}\n💰 موجودی: {balance:,}\n📦 پلن: {plan if plan else 'ندارد'}\n"
        if order:
            oid, oplan, ofinal, ostatus, ots = order
            text += f"\n🆔 آخرین سفارش: {oid}\n📦 {oplan}\n💰 {ofinal}\n📌 وضعیت: {ostatus}\n🕓 {time.ctime(ots)}"
        else:
            text += "\n🛒 سفارشی ثبت نشده"
    else:
        cur.execute("SELECT user_id, plan, final_amount, tracking_code, status FROM orders WHERE tracking_code=?", (query,))
        order = cur.fetchone()
        if order:
            user_id, plan, ofinal, otrack, ostatus = order
            text = f"🔎 **سفارش با کد پیگیری**\n👤 کاربر: {user_id}\n📦 {plan}\n💰 {ofinal}\n🔢 کد: {otrack}\n📌 وضعیت: {ostatus}"
        else:
            text = "❌ یافت نشد"
    
    cur.close()
    db.close()
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_orders")
def admin_orders(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT order_id, user_id, plan, final_amount, status, timestamp FROM orders ORDER BY timestamp DESC LIMIT 30")
    orders = cur.fetchall()
    cur.close()
    db.close()
    
    text = "📝 **۳۰ سفارش اخیر**\n\n"
    for o in orders:
        text += f"🆔 {o[0]} | 👤 {o[1]} | {o[2]} | {o[3]:,} تومان | {o[4]} | {time.ctime(o[5])}\n"
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_discounts")
def admin_discounts_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("➕ ساخت کد تخفیف", callback_data="create_discount"),
               InlineKeyboardButton("📜 لیست کدها", callback_data="list_discounts"),
               InlineKeyboardButton("🗑️ حذف کد", callback_data="delete_discount"))
    bot.send_message(call.message.chat.id, "🎫 **مدیریت کدهای تخفیف**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "create_discount")
def create_discount_prompt(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    msg = bot.send_message(call.message.chat.id, "🎫 **فرمت:** `کد,نوع,مقدار,تعداد,انقضا(ثانیه)`\nمثال: `OFF20,percent,20,5,2592000`", parse_mode="Markdown")
    bot.register_next_step_handler(msg, create_discount_code)

def create_discount_code(msg):
    if not is_admin(msg.from_user.id):
        return
    
    parts = msg.text.split(",")
    if len(parts) != 5:
        bot.send_message(msg.chat.id, "❌ فرمت نامعتبر.")
        return
    
    code, dtype, value, uses_left, expiry_sec = parts
    if dtype not in ["percent","fixed"]:
        bot.send_message(msg.chat.id, "❌ نوع باید percent یا fixed باشد.")
        return
    
    try:
        value = int(value)
        uses_left = int(uses_left)
        expiry = int(time.time()) + int(expiry_sec)
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO discount_codes (code, type, value, uses_left, expiry, created_by) VALUES (?,?,?,?,?,?)",
                    (code, dtype, str(value), uses_left, expiry, msg.from_user.id))
        db.commit()
        cur.close()
        db.close()
        bot.send_message(msg.chat.id, f"✅ **کد {code} ساخته شد.**\nنوع: {dtype}\nمقدار: {value}\nتعداد باقیمانده: {uses_left}\nانقضا: {time.ctime(expiry)}", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(msg.chat.id, f"❌ خطا: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "list_discounts")
def list_discounts(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT code, type, value, uses_left, expiry FROM discount_codes")
    rows = cur.fetchall()
    cur.close()
    db.close()
    
    if not rows:
        bot.send_message(call.message.chat.id, "📜 هیچ کد تخفیفی موجود نیست.")
        return
    
    text = "📜 **کدهای تخفیف موجود:**\n\n"
    for r in rows:
        text += f"🔹 `{r[0]}` | {r[1]} | {r[2]} | باقی‌مانده: {r[3]} | انقضا: {time.ctime(r[4])}\n"
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "delete_discount")
def delete_discount_prompt(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    msg = bot.send_message(call.message.chat.id, "🗑️ **کد تخفیف را وارد کن:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, delete_discount_code)

def delete_discount_code(msg):
    if not is_admin(msg.from_user.id):
        return
    
    code = msg.text.strip()
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM discount_codes WHERE code=?", (code,))
    if cur.rowcount:
        db.commit()
        cur.close()
        db.close()
        bot.send_message(msg.chat.id, f"✅ کد `{code}` حذف شد.", parse_mode="Markdown")
    else:
        cur.close()
        db.close()
        bot.send_message(msg.chat.id, "❌ یافت نشد.")

@bot.callback_query_handler(func=lambda call: call.data == "admin_plans")
def admin_plans(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    text = "📦 **وضعیت پلن‌ها:**\n\n"
    for plan in ['10','20','30','50']:
        available = is_plan_available(plan)
        status = "✅ فعال" if available else "❌ غیرفعال"
        text += f"{plan} گیگ: {status}\n"
    
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    bot.send_message(call.message.chat.id, "🔢 **شماره پلن (10/20/30/50) را برای تغییر وضعیت وارد کن:**")
    bot.register_next_step_handler(call.message, toggle_plan_status)

def toggle_plan_status(msg):
    if not is_admin(msg.from_user.id):
        return
    
    plan = msg.text.strip()
    if plan not in ['10','20','30','50']:
        bot.send_message(msg.chat.id, "❌ نامعتبر.")
        return
    
    current = is_plan_available(plan)
    set_plan_availability(plan, not current)
    bot.send_message(msg.chat.id, f"✅ وضعیت پلن {plan} گیگ تغییر کرد.")

@bot.callback_query_handler(func=lambda call: call.data == "admin_ban")
def admin_ban_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("➕ بن کاربر", callback_data="ban_user"),
               InlineKeyboardButton("📋 لیست بن‌ها", callback_data="list_banned"),
               InlineKeyboardButton("🔓 آزاد کردن", callback_data="unban_user"))
    bot.send_message(call.message.chat.id, "⛔ **مدیریت مسدود شدگان**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "ban_user")
def ban_prompt(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    msg = bot.send_message(call.message.chat.id, "👤 **آیدی عددی کاربر و دلیل (اختیاری) را وارد کن:**\nمثال: `123456789 ارسال رسید فیک`", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_ban)

def process_ban(msg):
    if not is_admin(msg.from_user.id):
        return
    
    parts = msg.text.strip().split(maxsplit=1)
    if not parts:
        bot.send_message(msg.chat.id, "❌ فرمت نامعتبر.")
        return
    
    try:
        user_id = int(parts[0])
    except:
        bot.send_message(msg.chat.id, "❌ آیدی نامعتبر (باید عدد باشد).")
        return
    
    reason = parts[1] if len(parts) > 1 else "بدون دلیل"
    
    if user_id == msg.from_user.id:
        bot.send_message(msg.chat.id, "❌ نمی‌توانید خودتان را بن کنید.")
        return
    
    if is_admin(user_id):
        bot.send_message(msg.chat.id, "❌ نمی‌توانید ادمین را مسدود کنید.")
        return
    
    if is_user_banned(user_id):
        bot.send_message(msg.chat.id, f"⚠️ کاربر {user_id} قبلاً مسدود شده است.")
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO banned_users (user_id, banned_at, reason) VALUES (?,?,?)",
                (user_id, int(time.time()), reason))
    db.commit()
    cur.close()
    db.close()
    
    bot.send_message(msg.chat.id, f"✅ کاربر {user_id} با موفقیت مسدود شد.\nدلیل: {reason}")
    try:
        bot.send_message(user_id, f"⛔ **شما توسط ادمین مسدود شده‌اید.**\nدلیل: {reason}\nدر صورت اعتراض با پشتیبانی تماس بگیرید.", parse_mode="Markdown")
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "list_banned")
def list_banned(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT user_id, banned_at, reason FROM banned_users")
    banned = cur.fetchall()
    cur.close()
    db.close()
    
    if not banned:
        bot.send_message(call.message.chat.id, "📋 هیچ کاربر مسدودی وجود ندارد.")
        return
    
    text = "📋 **لیست کاربران مسدود شده:**\n\n"
    for uid, banned_at, reason in banned:
        text += f"🆔 {uid} | دلیل: {reason} | زمان: {time.ctime(banned_at)}\n"
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "unban_user")
def unban_prompt(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    msg = bot.send_message(call.message.chat.id, "🔓 **آیدی عددی کاربر را برای آزادسازی وارد کن:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_unban)

def process_unban(msg):
    if not is_admin(msg.from_user.id):
        return
    
    try:
        user_id = int(msg.text.strip())
    except:
        bot.send_message(msg.chat.id, "❌ آیدی نامعتبر.")
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM banned_users WHERE user_id=?", (user_id,))
    if cur.rowcount:
        db.commit()
        bot.send_message(msg.chat.id, f"✅ کاربر {user_id} از مسدودیت خارج شد.")
        try:
            bot.send_message(user_id, "✅ **شما توسط ادمین آزاد شدید. اکنون می‌توانید از ربات استفاده کنید.**", parse_mode="Markdown")
        except:
            pass
    else:
        bot.send_message(msg.chat.id, "❌ کاربر مورد نظر مسدود نبوده یا یافت نشد.")
    cur.close()
    db.close()

@bot.callback_query_handler(func=lambda call: call.data == "admin_tickets")
def admin_tickets(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT ticket_id, user_id, title, created_at FROM tickets WHERE status='open' ORDER BY created_at ASC")
    tickets = cur.fetchall()
    cur.close()
    db.close()
    
    if not tickets:
        bot.send_message(call.message.chat.id, "📭 **هیچ تیکت باز وجود ندارد.**", reply_markup=main_keyboard())
        return
    
    text = "📋 **تیکت‌های باز:**\n\n"
    for t in tickets:
        text += f"🆔 {t[0]} | 👤 {t[1]} | {t[2]} | {time.ctime(t[3])}\n"
    
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    bot.send_message(call.message.chat.id, "🔢 **برای پاسخ به تیکت، شماره آن را وارد کنید:**", reply_markup=back_keyboard())
    bot.register_next_step_handler(call.message, admin_reply_ticket)
    bot.answer_callback_query(call.id)

def admin_reply_ticket(msg):
    if not is_admin(msg.from_user.id):
        return
    
    if msg.text == "🔙 بازگشت به منو":
        back_main(msg)
        return
    
    try:
        ticket_id = int(msg.text.strip())
    except:
        bot.send_message(msg.chat.id, "❌ شماره نامعتبر.")
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT user_id, title, status FROM tickets WHERE ticket_id=?", (ticket_id,))
    ticket = cur.fetchone()
    
    if not ticket or ticket[2] != 'open':
        cur.close()
        db.close()
        bot.send_message(msg.chat.id, "❌ تیکت باز یافت نشد.")
        return
    
    user_id, title = ticket[0], ticket[1]
    cur.execute("SELECT sender_role, message, timestamp FROM ticket_messages WHERE ticket_id=? ORDER BY timestamp ASC", (ticket_id,))
    messages = cur.fetchall()
    cur.close()
    db.close()
    
    text = f"💬 **تیکت #{ticket_id} - {title}**\n\n"
    for m in messages:
        role = "کاربر" if m[0] == 'user' else "پشتیبان"
        text += f"{role} ({time.ctime(m[2])}):\n{m[1]}\n\n"
    
    bot.send_message(msg.chat.id, text)
    bot.send_message(msg.chat.id, "✏️ **پاسخ خود را بنویسید:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, send_admin_ticket_reply, ticket_id, user_id)

def send_admin_ticket_reply(msg, ticket_id, user_id):
    if not is_admin(msg.from_user.id):
        return
    
    answer = msg.text.strip()
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO ticket_messages (ticket_id, sender_id, sender_role, message, timestamp) VALUES (?,?,?,?,?)",
                (ticket_id, msg.from_user.id, 'admin', answer, int(time.time())))
    db.commit()
    cur.close()
    db.close()
    
    bot.send_message(msg.chat.id, f"✅ **پاسخ شما برای تیکت {ticket_id} ارسال شد.**")
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📨 پاسخ جدید", callback_data=f"reply_ticket_{ticket_id}"),
               InlineKeyboardButton("🔒 بستن تیکت", callback_data=f"close_ticket_{ticket_id}"))
    
    bot.send_message(user_id, f"✅ **پاسخ تیکت #{ticket_id}:**\n{answer}\n\nجهت پاسخ بیشتر یا بستن تیکت از دکمه‌ها استفاده کنید.", reply_markup=markup)
    
    user_email = get_user_email(user_id)
    if user_email:
        try:
            msg_email = MIMEText(f"پاسخ تیکت #{ticket_id}:\n{answer}", "plain", "utf-8")
            msg_email["Subject"] = f"پاسخ تیکت #{ticket_id}"
            msg_email["From"] = f"Jigar Tunnel <{EMAIL}>"
            msg_email["To"] = user_email
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(EMAIL, APP_PASSWORD)
            server.sendmail(EMAIL, user_email, msg_email.as_string())
            server.quit()
        except Exception as e:
            print(f"Email error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_wallet")
def admin_wallet(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    bot.send_message(call.message.chat.id, "💰 **مدیریت کیف پول**\n\n🔢 **آیدی کاربر را وارد کن:**", parse_mode="Markdown")
    bot.register_next_step_handler(call.message, admin_wallet_user)
    bot.answer_callback_query(call.id)

def admin_wallet_user(msg):
    if not is_admin(msg.from_user.id):
        return
    
    try:
        user_id = int(msg.text.strip())
    except:
        bot.send_message(msg.chat.id, "❌ نامعتبر.")
        return
    
    balance = get_user_balance(user_id)
    bot.send_message(msg.chat.id, f"👤 **کاربر {user_id}**\n💰 **موجودی:** {balance:,} تومان\n\nمبلغ جدید را وارد کن (مثبت برای شارژ، منفی برای برگشت مبلغ اشتباه):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, admin_wallet_amount, user_id)

def admin_wallet_amount(msg, user_id):
    if not is_admin(msg.from_user.id):
        return
    
    try:
        amount = int(msg.text.strip())
    except:
        bot.send_message(msg.chat.id, "❌ نامعتبر.")
        return
    
    if amount == 0:
        bot.send_message(msg.chat.id, "❌ صفر معتبر نیست.")
        return
    
    update_balance(user_id, amount, f"تغییر توسط ادمین: {amount} تومان")
    
    if amount > 0:
        bot.send_message(user_id, f"✅ **کیف پول شما به مبلغ {amount:,} تومان شارژ شد.**", parse_mode="Markdown")
    else:
        bot.send_message(user_id, f"⚠️ **مبلغ {abs(amount):,} تومان از کیف پول شما کسر شد.** (برگشت مبلغ اشتباه)", parse_mode="Markdown")
    
    bot.send_message(msg.chat.id, f"✅ **موجودی کاربر {user_id} به {get_user_balance(user_id):,} تومان تغییر کرد.**", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_enable_account")
def admin_enable_account_prompt(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    msg = bot.send_message(call.message.chat.id, "🔓 **لطفاً آیدی عددی کاربر را وارد کنید:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, admin_enable_account_process)

def admin_enable_account_process(msg):
    if not is_admin(msg.from_user.id):
        return
    
    try:
        user_id = int(msg.text.strip())
    except:
        bot.send_message(msg.chat.id, "❌ آیدی نامعتبر.")
        return
    
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE users SET disabled=0 WHERE id=?", (user_id,))
    db.commit()
    
    if cur.rowcount:
        bot.send_message(msg.chat.id, f"✅ کاربر {user_id} فعال شد.")
        try:
            bot.send_message(user_id, "✅ **حساب کاربری شما توسط ادمین فعال شد. اکنون می‌توانید از ربات استفاده کنید.**", parse_mode="Markdown")
        except:
            pass
    else:
        bot.send_message(msg.chat.id, "❌ کاربر یافت نشد یا قبلاً فعال است.")
    
    cur.close()
    db.close()

@bot.callback_query_handler(func=lambda call: call.data == "admin_toggle_bot")
def admin_toggle_bot(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "دسترسی غیرمجاز!", show_alert=True)
        return
    
    if is_bot_disabled():
        set_bot_disabled(False, "")
        bot.send_message(call.message.chat.id, "✅ **ربات با موفقیت فعال شد.**")
        send_to_admins("ربات فعال شد.")
    else:
        msg = bot.send_message(call.message.chat.id, "🔒 **خاموش کردن ربات**\nلطفاً رمز مدیریت را وارد کنید (رمز: AR_13900):")
        bot.register_next_step_handler(msg, ask_disable_reason)

def ask_disable_reason(msg):
    if not is_admin(msg.from_user.id):
        return
    
    if msg.text != "AR_13900":
        bot.send_message(msg.chat.id, "❌ رمز اشتباه است. عملیات لغو شد.")
        admin_panel(msg)
        return
    
    msg2 = bot.send_message(msg.chat.id, "علت خاموشی ربات را وارد کنید (مثلاً: در حال بروزرسانی):")
    bot.register_next_step_handler(msg2, perform_disable)

def perform_disable(msg):
    if not is_admin(msg.from_user.id):
        return
    
    reason = msg.text.strip()
    set_bot_disabled(True, reason)
    bot.send_message(msg.chat.id, f"🔴 ربات غیرفعال شد.\nعلت: {reason}")
    send_to_admins(f"ربات غیرفعال شد. علت: {reason}")

# ================= اجرا =================
print("✅ ربات Jigar Tunnel نسخه نهایی با نمایندگی و اطلاعات کامل اجرا شد.")

while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"⚠️ خطا: {e}")
        time.sleep(5)