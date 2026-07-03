import logging
import random
import string
import os
import asyncio
import yt_dlp
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta, timezone
from telegram import Update, Bot, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ChatPermissions
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# ==========================================
# ⚙️ إعدادات البوت الأساسية 
# ==========================================
TOKEN = "8702640145:AAHyLv6r3xfyf9x-dptwim6_BrnJSbWYpmY"
OWNER_ID = 8038919535  # ⚠️ استبدل هذا الرقم بآيدي حسابك الحقيقي
ADMIN_PASS = "0658"    # كلمة المرور للوحة تحكم الأدمن

MAINTENANCE_MODE = False

# ==========================================
# 🌐 سيرفر الفحص الوهمي لتجنب إغلاق Render للبوت
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running successfully on Render!")

    def log_message(self, format, *args):
        return  # لمنع ملء الـ Logs

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"✓ Health check server started on port {port}")
    server.serve_forever()

# ==========================================
# 📜 قائمة الـ 30 آية قرآنية مزخرفة
# ==========================================
QURAN_VERSES = [
    "✨ ﴿ اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ﴾ ✨",
    "📖 ﴿ إِنَّ مَعَ الْعُسْرِ يُسْرًا ﴾ 📖",
    "✨ ﴿ أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ ﴾ ✨",
    "📖 ﴿ وَقُلْ رَبِّ زِدْنِي عِلْمًا ﴾ 📖",
    "✨ ﴿ وَمَنْ يَتَوَكَّلْ عَلَى اللَّهِ فَهُوَ حَسْبُهُ ﴾ ✨",
    "📖 ﴿ إِنَّ اللَّهَ مَعَ الصَّابِرِينَ ﴾ 📖",
    "✨ ﴿ وَإِذَا سَأَلَكَ عِبَادِي عَنِّي فَإِنِّي قَرِيبٌ ﴾ ✨",
    "📖 ﴿ وَلَسَوْفَ يُعْطِيكَ رَبُّكَ فَتَرْضَىٰ ﴾ 📖",
    "✨ ﴿ إِنَّ اللَّهَ وَمَلَائِكَتَهُ يُصَلُّونَ عَلَى النَّبِيِّ ﴾ ✨",
    "📖 ﴿ فَاذْكُرُونِي أَذْكُرْكُمْ وَاشْكُرُوا لِي وَلَا تَكْفُرُونِ ﴾ 📖",
    "✨ ﴿ لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا ﴾ 📖",
    "📖 ﴿ وَاعْتَصِمُوا بِحَبْلِ اللَّهِ جَمِيعًا وَلَا تَفَرَّقُوا ﴾ ✨",
    "✨ ﴿ قُلْ هُوَ اللَّهُ أَحَدٌ ﴾ 📖",
    "📖 ﴿ وَمَا تَوْفِيقِي إِلَّا بِاللَّهِ ﴾ ✨",
    "✨ ﴿ إِنَّ أَكْرَمَكُمْ عِنْدَ اللَّهِ أَتْقَاكُمْ ﴾ 📖",
    "📖 ﴿ وَأُفَوِّضُ أَمْرِي إِلَى اللَّهِ ﴾ ✨",
    "✨ ﴿ وَجَعَلْنَا مِنَ الْمَاءِ كُلَّ شَيْءٍ حَيٍّ ﴾ 📖",
    "📖 ﴿ فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ ﴾ ✨",
    "✨ ﴿ هَلْ جَزَاءُ الْإِحْسَانِ إِلَّا الْإِحْسَانُ ﴾ 📖",
    "📖 ﴿ وَعَسَىٰ أَنْ تَكْرَهُوا شَيْئًا وَهُوَ خَيْرٌ لَكُمْ ﴾ ✨",
    "✨ ﴿ وَالَّذِينَ جَاهَدُوا فِينَا لَنَهْدِيَنَّهُمْ سُبُلَنَا ﴾ 📖",
    "📖 ﴿ رَبَّنَا لَا تُزِغْ قُلُوبَنَا بَعْدَ إِذْ هَدَيْتَنَا ﴾ ✨",
    "✨ ﴿ وَقُلْ جَاءَ الْحَقُّ وَزَهَقَ الْبَاطِلُ ﴾ 📖",
    "📖 ﴿ إِنَّ الْحَسَنَاتِ يُذْهِبْنَا السَّيِّئَاتِ ﴾ ✨",
    "✨ ﴿ وَاخْفِضْ لَهُمَا جَنَاحَ الذُّلِّ مِنَ الرَّحْمَةِ ﴾ 📖",
    "📖 ﴿ وَلَا تَحْسَبَنَّ اللَّهَ غَافِلًا عَمَّا يَعْمَلُ الظَّالِمُونَ ﴾ ✨",
    "✨ ﴿ نَبِّئْ عِبَادِي أَنِّي أَنَا الْغَفُورُ الرَّحِيمُ ﴾ 📖",
    "📖 ﴿ ادْعُونِي أَسْتَجِبْ لَكُمْ ﴾ ✨",
    "✨ ﴿ وَإِنْ تَعُدُّوا نِعْمَةَ اللَّهِ لَا تُحْصُوهَا ﴾ 📖",
    "📖 ﴿ قُلْ يَا عِبَادِيَ الَّذِينَ أَسْرَفُوا عَلَىٰ أَنْفُسِهِمْ لَا تَقْنَطُوا مِنْ رَحْمَةِ اللَّهِ ﴾ ✨"
]

# ==========================================
# 🛡️ تصميم القوائم التفاعلية للأزرار
# ==========================================
def get_main_menu():
    keyboard = [
        [KeyboardButton("📥 تحميل"), KeyboardButton("✨ زخرفة")],
        [KeyboardButton("👑 أدمن"), KeyboardButton("ℹ️ معلومات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_panel():
    keyboard = [
        [InlineKeyboardButton("📢 بث جماعي", callback_data="bc_menu"), InlineKeyboardButton("📖 بث آية", callback_data="verse_menu")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats"), InlineKeyboardButton("⚙️ وضع الصيانة", callback_data="mnt")],
        [InlineKeyboardButton("🚫 إغلاق اللوحة", callback_data="close")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==========================================
# 🔧 دالات المساعدة وإدارة البيانات 
# ==========================================
async def post_init(application):
    commands = [
        BotCommand("start", "بدء تشغيل البوت والترحيب"),
        BotCommand("help", "عرض قائمة المساعدة والدعم"),
        BotCommand("info", "عرض حسابك والمعرف الشخصي"),
        BotCommand("getkey", "توليد وإنشاء مفتاح ZADC جديد")
    ]
    await application.bot.set_my_commands(commands)

def save_chat_id(chat_id, name="مستخدم تليجرام"):
    try:
        if not os.path.exists("chats.txt"):
            with open("chats.txt", "w", encoding="utf-8") as f:
                f.write("")
        with open("chats.txt", "r+", encoding="utf-8") as f:
            content = f.read()
            if str(chat_id) not in content:
                f.write(f"{chat_id}|{name}\n")
    except Exception as e:
        print(f"Error saving chat ID: {e}")

def get_chat_display_name(update: Update):
    if not update or not update.effective_chat:
        return "غير معروف"
    chat = update.effective_chat
    if chat.title:
        return f"[مجموعة] {chat.title}"
    else:
        first = chat.first_name or ""
        last = chat.last_name or ""
        username = f" (@{chat.username})" if chat.username else ""
        return f"{first} {last}{username}".strip() or "مستخدم تليجرام"

def find_downloaded_file(download_dir, video_id):
    if not os.path.exists(download_dir):
        return None
    for f in os.listdir(download_dir):
        if f.startswith(video_id):
            return os.path.join(download_dir, f)
    return None

async def run_broadcast_async(bot, message):
    if not os.path.exists("chats.txt"):
        return 0
    with open("chats.txt", "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    count = 0
    for line in lines:
        if not line.strip(): continue
        c_id = line.split("|")[0] if "|" in line else line
        try:
            await bot.send_message(chat_id=int(c_id), text=message, parse_mode='HTML')
            count += 1
        except Exception:
            pass
    return count

# ==========================================
# 👑 [أوامر التحكم السرية الخاصة بالمالك عبر الأوامر النصية]
# ==========================================
async def owner_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    if not context.args:
        await update.message.reply_text("❌ الاستخدام الصحيح: <code>/bc الرسالة هنا</code>", parse_mode='HTML')
        return
    broadcast_msg = " ".join(context.args)
    status_msg = await update.message.reply_text("📢 جاري إرسال البث الجماعي...")
    count = await run_broadcast_async(context.bot, broadcast_msg)
    await status_msg.edit_text(f"✅ تم بنجاح بث رسالتك إلى {count} مستخدم ومجموعة!")

async def owner_verse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    if not context.args:
        await update.message.reply_text("❌ الاستخدام الصحيح: <code>/verse رقم_الآية(1-30)</code>", parse_mode='HTML')
        return
    try:
        v_num = int(context.args[0])
        if 1 <= v_num <= 30:
            selected_verse = QURAN_VERSES[v_num - 1]
            decorated_message = (
                f"✨ 📜 <b>آيَةٌ قُرْآنِيَّةٌ كَرِيمَةٌ تُنِيرُ القُلُوبْ</b> 📜 ✨\n"
                f"╬════════════════════════╬\n\n"
                f"✨ <b>{selected_verse}</b> ✨\n\n"
                f"╬════════════════════════╬\n"
                f"تأملها واذكر الله العظيم 🌹"
            )
            status_msg = await update.message.reply_text(f"⏳ جاري بث الآية رقم {v_num}...")
            count = await run_broadcast_async(context.bot, decorated_message)
            await status_msg.edit_text(f"✅ تم بث الآية الكريمة بنجاح إلى {count} مستخدم ومجموعة!")
        else:
            await update.message.reply_text("❌ الرقم خاطئ، اختر رقم بين 1 و 30.")
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال رقم صحيح فقط.")

async def owner_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    if os.path.exists("chats.txt"):
        with open("chats.txt", "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        total = len(lines)
        result = f"📊 <b>إحصائيات البوت النشطة الحالية:</b>\n📈 إجمالي المشتركين: <b>{total}</b>\n-----------------------------------------\n"
        for index, line in enumerate(lines, 1):
            c_id, c_name = line.split("|", 1) if "|" in line else (line, "مستخدم")
            result += f"{index}. <code>{c_id}</code> | {c_name}\n"
        if len(result) > 4000:
            result = result[:3900] + "\n\n⚠️ تم اختصار القائمة لكبر حجم البيانات."
        await update.message.reply_text(result, parse_mode='HTML')
    else:
        await update.message.reply_text("❌ لا يوجد أي مستخدمين مسجلين حالياً.")

async def owner_maintenance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MAINTENANCE_MODE
    if update.effective_user.id != OWNER_ID: return
    MAINTENANCE_MODE = not MAINTENANCE_MODE
    status = "🔴 [مفعّل - البوت مغلق للعامة]" if MAINTENANCE_MODE else "🟢 [معطّل - البوت يعمل للجميع]"
    await update.message.reply_text(f"⚙️ تم تحديث وضع الصيانة بنجاح:\n{status}")

# ==========================================
# 👥 [أوامر وخدمات المستخدمين العامة]
# ==========================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if MAINTENANCE_MODE and update.effective_user.id != OWNER_ID: return
    save_chat_id(update.effective_chat.id, get_chat_display_name(update))
    help_text = (
        "✨ <b>قائمة خدمات البوت المتكاملة</b> ✨\n\n"
        "📥 <b>تحميل الفيديوهات:</b> أرسل رابط الفيديو مباشرة وسأقوم بتحميله.\n\n"
        "🎵 <b>تحميل الأغاني:</b> اكتب كلمة (يوت) متبوعة باسم الأغنية.\n\n"
        "✏️ <b>زخرفة الأسماء:</b> اكتب كلمة (زخرفة) متبوعة بالاسم.\n\n"
        "🛡️ <b>صلاحيات المشرفين:</b> قم بالرد بكلمة (كتم) لإظهار لوحة التحكم أو (طرد) للحظر."
    )
    await update.message.reply_text(help_text, reply_markup=get_main_menu(), parse_mode='HTML')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if MAINTENANCE_MODE and update.effective_user.id != OWNER_ID: return
    save_chat_id(update.effective_chat.id, get_chat_display_name(update))
    await update.message.reply_text("🎯 أهلاً بك في بوت الخدمات الشامل! استخدم الأزرار بالأسفل لتصفح الخدمات أو أرسل /help لمعرفة الميزات.", reply_markup=get_main_menu())

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if MAINTENANCE_MODE and update.effective_user.id != OWNER_ID: return
    save_chat_id(update.effective_chat.id, get_chat_display_name(update))
    user = update.effective_user
    info_text = f"👤 <b>معلوماتك شخصياً:</b>\nالاسم: {user.first_name}\n🆔 الآيدي: <code>{user.id}</code>"
    await update.message.reply_text(info_text, parse_mode='HTML')

async def generate_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if MAINTENANCE_MODE and update.effective_user.id != OWNER_ID: return
    save_chat_id(update.effective_chat.id, get_chat_display_name(update))
    key = f"ZADC_{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
    await update.message.reply_text(f"🔑 <b>المفتاح الجديد:</b>\n<code>{key}</code>", parse_mode='HTML')

async def welcome_new_members_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (MAINTENANCE_MODE and update.effective_user.id != OWNER_ID) or not update.message or not update.message.new_chat_members:
        return
    save_chat_id(update.effective_chat.id, get_chat_display_name(update))
    for member in update.message.new_chat_members:
        if member.id == context.bot.id: return
        user_mention = f'<a href="tg://user?id={member.id}">{member.first_name}</a>'
        current_time = datetime.now().strftime("%Y-%m-%d ⚡ %I:%M:%S %p")
        welcome_text = (
            f"👑 ✨ <b>تَرْحِيبٌ مَلَكِيٌّ فَاخِرٌ بِالعُضْوِ الجَدِيدْ</b> ✨ 👑\n"
            f"👑 ━━━━━━━━━━━━━━━━━━━━━━━━━ 👑\n\n"
            f"👋 <b>أهلاً ومرحباً بك يا بطل في المجموعة، نورتنا وشرفتنا بقدومك الميمون!</b> ✨\n\n"
            f"👤 <b>العضو الكريم:</b> {user_mention}\n"
            f"🆔 <b>الآيدي الشخصي:</b> <code>{member.id}</code>\n"
            f"📅 <b>تاريخ ووقت الدخول:</b> <code>{current_time}</code>\n\n"
            f"👑 ━━━━━━━━━━━━━━━━━━━━━━━━━ 👑\n"
            f"💬 تذكر دائماً ذكر الله والتفاعل الراقي 🌹\n"
            f"⚙️ لمعرفة خدمات وأوامر البوت، أرسل: <code>/help</code>"
        )
        await update.message.reply_text(welcome_text, parse_mode='HTML')

# ==========================================
# 📥 الدالة المركزية لمعالجة كافة النصوص والتحميل والزخرفة ولوحة التحكم
# ==========================================
async def core_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if MAINTENANCE_MODE and update.effective_user.id != OWNER_ID: return
    if not update.message or not update.message.text: return
    
    save_chat_id(update.effective_chat.id, get_chat_display_name(update))
    text_received = update.message.text.strip()
    chat_id = update.effective_chat.id

    # 1. معالجة انتظار الرسالة الجماعية من لوحة التحكم (المالك)
    if context.user_data.get('waiting_bc_msg'):
        context.user_data['waiting_bc_msg'] = False
        status_msg = await update.message.reply_text("📢 جاري إرسال البث الجماعي المكتوب...")
        count = await run_broadcast_async(context.bot, text_received)
        await status_msg.reply_text(f"✅ تم بث رسالتك بنجاح إلى {count} مستخدم ومجموعة!")
        return

    # 2. معالجة انتظار رقم الآية من لوحة التحكم (المالك)
    if context.user_data.get('waiting_verse_num'):
        context.user_data['waiting_verse_num'] = False
        try:
            v_num = int(text_received)
            if 1 <= v_num <= 30:
                selected_verse = QURAN_VERSES[v_num - 1]
                decorated_message = (
                    f"✨ 📜 <b>آيَةٌ قُرْآنِيَّةٌ كَرِيمَةٌ تُنِيرُ القُلُوبْ</b> 📜 ✨\n"
                    f"╬════════════════════════╬\n\n"
                    f"✨ <b>{selected_verse}</b> ✨\n\n"
                    f"╬════════════════════════╬\n"
                    f"تأملها واذكر الله العظيم 🌹"
                )
                status_msg = await update.message.reply_text(f"⏳ جاري بث الآية رقم {v_num} من لوحة التحكم...")
                count = await run_broadcast_async(context.bot, decorated_message)
                await status_msg.reply_text(f"✅ تم بث الآية الكريمة بنجاح إلى {count} مستخدم ومجموعة!")
            else:
                await update.message.reply_text("❌ الرقم خاطئ، اختر رقم بين 1 و 30.")
        except ValueError:
            await update.message.reply_text("❌ يرجى إدخال رقم صحيح فقط.")
        return

    # 3. نظام زر الأدمن الرئيسي وطلب كلمة السر
    if text_received == "👑 أدمن":
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ هذا الزر مخصص لمالك البوت فقط!")
            return
        await update.message.reply_text("🔑 <b>يرجى إدخال كلمة المرور للوحة تحكم المالك:</b>", parse_mode='HTML')
        context.user_data['waiting_pass'] = True
        return

    if context.user_data.get('waiting_pass'):
        if text_received == ADMIN_PASS:
            context.user_data['waiting_pass'] = False
            await update.message.reply_text(
                "🖥️ <b>لوحة تحكم المالك الشاملة (Termux Style):</b>\nاختر أحد الإجراءات من القائمة التفاعلية أدناه:",
                reply_markup=get_admin_panel(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text("❌ كلمة السر خاطئة! تم إلغاء العملية لحمايتك.")
            context.user_data['waiting_pass'] = False
        return

    # 4. معالجة أزرار القائمة الرئيسية العامة
    if text_received == "📥 تحميل":
        await update.message.reply_text("📥 <b>قسم التحميل المتكامل:</b>\nأرسل رابط أي فيديو مباشرة (يوتيوب، تيك توك، فيسبوك) للتحميل الفوري مقطع فيديو، أو اكتب كلمة (يوت) متبوعة باسم الأغنية لتحميلها ملف صوتي.", parse_mode='HTML')
        return

    if text_received == "✨ زخرفة":
        await update.message.reply_text("✏️ <b>قسم الزخرفة الاحترافي:</b>\nاكتب كلمة (زخرفة) متبوعة بالاسم الذي تريده.\nمثال: <code>زخرفة الأسطورة</code>", parse_mode='HTML')
        return

    if text_received == "ℹ️ معلومات":
        user = update.effective_user
        info_text = f"👤 <b>معلوماتك شخصياً:</b>\nالاسم: {user.first_name}\n🆔 الآيدي: <code>{user.id}</code>"
        await update.message.reply_text(info_text, parse_mode='HTML')
        return

    # 5. الرد التلقائي المزخرف على السلام
    if text_received in ["سلام", "سلام عليكم", "السلام عليكم", "السلام عليكم ورحمة الله", "السلام عليكم ورحمة الله وبركاته"]:
        user_mention = f'<a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>'
        greeting_reply = (
            f"✨ 💎 <b>『 وَعَلَيْكُمُ السَّلَامُ وَرَحْمَةُ اللهِ تَعَالَىٰ وَبَرَكَاتُهُ 』</b> 💎 ✨\n"
            f"╬════════════════════════╬\n"
            f"أهلاً وسهلاً بك يا غالي {user_mention} 🌸 نورت المجموعة وشرفتنا بحضورك المتميز!"
        )
        await update.message.reply_text(greeting_reply, parse_mode='HTML')
        return

    # 6. قسم المشرفين في المجموعات (كتم وطرد عبر النصوص)
    if text_received in ["كتم", "طرد", "/mute", "/ban"] and update.message.reply_to_message:
        admin_id = update.effective_user.id
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=admin_id)
        if member.status in ['administrator', 'creator']:
            target_user = update.message.reply_to_message.from_user
            user_mention = f'<a href="tg://user?id={target_user.id}">{target_user.first_name}</a>'
            
            if text_received in ["طرد", "/ban"]:
                try:
                    await context.bot.ban_chat_member(chat_id=chat_id, user_id=target_user.id)
                    await update.message.reply_text(f"🚷 تم طرد العضو {user_mention} نهائياً.", parse_mode='HTML')
                except Exception:
                    await update.message.reply_text("❌ فشل الطرد. تأكد من صلاحيات البوت.")
                return

            if text_received in ["كتم", "/mute"]:
                keyboard = [
                    [
                        InlineKeyboardButton("1 دقيقة", callback_data=f"mute_1m_{target_user.id}"),
                        InlineKeyboardButton("15 دقيقة", callback_data=f"mute_15m_{target_user.id}"),
                        InlineKeyboardButton("ساعة", callback_data=f"mute_1h_{target_user.id}")
                    ],
                    [
                        InlineKeyboardButton("يوم", callback_data=f"mute_1d_{target_user.id}"),
                        InlineKeyboardButton("يومين", callback_data=f"mute_2d_{target_user.id}")
                    ],
                    [InlineKeyboardButton("🚷 طرد نهائي", callback_data=f"kick_{target_user.id}")]
                ]
                await update.message.reply_text(
                    text=f"📋 <b>قائمة التحكم بالعضو:</b> {user_mention}\nاختر الإجراء المناسب للحظر أو الكتم المحدود:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                return

    # 7. قسم الزخرفات الأسطورية الشاملة
    if text_received.startswith("زخرف ") or text_received.startswith("زخرفة "):
        parts = text_received.split(" ", 1)
        if len(parts) < 2 or not parts[1].strip():
            await update.message.reply_text("❌ يرجى كتابة ال
