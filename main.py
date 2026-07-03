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
    "✨ ﴿ اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ﴾ ✨",
    "📖 ﴿ إِنَّ مَعَ الْعُسْرِ يُسْرًا ﴾ 📖",
    "✨ ﴿ أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ ﴾ ✨",
    "📖 ﴿ وَقُلْ رَبِّ زِدْنِي عِلْمًا ﴾ 📖",
    "✨ ﴿ وَمَنْ يَتَوَكَّلْ عَلَى اللَّهِ فَهُوَ حَسْبُهُ ﴾ ✨",
    "📖 ﴿ إِنَّ اللَّهَ مَعَ الصَّابِرِينَ ﴾ 📖",
    "✨ ﴿ وَإِذَا سَأَلَكَ عِبَادِي عَنِّي فَإِنِّي قَرِيبٌ ﴾ ✨",
    "📖 ﴿ وَلَسَوْفَ يُعْطِيكَ رَبُّكَ فَتَرْضَىٰ ﴾ 📖",
    "✨ ﴿ إِنَّ اللَّهَ وَمَلَائِكَتَهُ يُصَلُّونَ عَلَى النَّبِيِّ ﴾ ✨",
    "📖 ﴿ فَاذْكُرُونِي أَذْكُرْكُمْ وَاشْكُرُوا لِي وَلَا تَكْفُرُونِ ﴾ 📖",
    "✨ ﴿ لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا ﴾ 📖",
    "📖 ﴿ وَاعْتَصِمُوا بِحَبْلِ اللَّهِ جَمِيعًا وَلَا تَفَرَّقُوا ﴾ ✨",
    "✨ ﴿ قُلْ هُوَ اللَّهُ أَحَدٌ ﴾ 📖",
    "📖 ﴿ وَمَا تَوْفِيقِي إِلَّا بِاللَّهِ ﴾ ✨",
    "✨ ﴿ إِنَّ أَكْرَمَكُمْ عِنْدَ اللَّهِ أَتْقَاكُمْ ﴾ 📖",
    "📖 ﴿ وَأُفَوِّضُ أَمْرِي إِلَى اللَّهِ ﴾ ✨",
    "✨ ﴿ وَجَعَلْنَا مِنَ الْمَاءِ كُلَّ شَيْءٍ حَيٍّ ﴾ 📖",
    "📖 ﴿ فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ ﴾ ✨",
    "✨ ﴿ هَلْ جَزَاءُ الْإِحْسَانِ إِلَّا الْإِحْسَانُ ﴾ 📖",
    "📖 ﴿ وَعَسَىٰ أَنْ تَكْرَهُوا شَيْئًا وَهُوَ خَيْرٌ لَكُمْ ﴾ ✨",
    "✨ ﴿ وَالَّذِينَ جَاهَدُوا فِينَا لَنَهْدِيَنَّهُمْ سُبُلَنَا ﴾ 📖",
    "📖 ﴿ رَبَّنَا لَا تُزِغْ قُلُوبَنَا بَعْدَ إِذْ هَدَيْتَنَا ﴾ ✨",
    "✨ ﴿ وَقُلْ جَاءَ الْحَقُّ وَزَهَقَ الْبَاطِلُ ﴾ 📖",
    "📖 ﴿ إِنَّ الْحَسَنَاتِ يُذْهِبْنَا السَّيِّئَاتِ ﴾ ✨",
    "✨ ﴿ وَاخْفِضْ لَهُمَا جَنَاحَ الذُّلِّ مِنَ الرَّحْمَةِ ﴾ 📖",
    "📖 ﴿ وَلَا تَحْسَبَنَّ اللَّهَ غَافِلًا عَمَّا يَعْمَلُ الظَّالِمُونَ ﴾ ✨",
    "✨ ﴿ نَبِّئْ عِبَادِي أَنِّي أَنَا الْغَفُورُ الرَّحِيمُ ﴾ 📖",
    "📖 ﴿ ادْعُونِي أَسْتَجِبْ لَكُمْ ﴾ ✨",
    "✨ ﴿ وَإِنْ تَعُدُّوا نِعْمَةَ اللَّهِ لَا تُحْصُوهَا ﴾ 📖",
    "📖 ﴿ قُلْ يَا عِبَادِيَ الَّذِينَ أَسْرَفُوا عَلَىٰ أَنْفُسِهِمْ لَا تَقْنَطُوا مِنْ رَحْمَةِ اللَّهِ ﴾ ✨"
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
        BotCommand("getkey", "توليد وإنشاء مفتاح ZADC جديد"),
        BotCommand("admin", "🔐 لوحة تحكم الأدمن (للمالك فقط)")
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
# 👑 أمر /admin الجديد - نقطة الدخول للوحة التحكم
# ==========================================
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الأمر الجديد /admin - يطلب كلمة المرور أولاً"""
    if MAINTENANCE_MODE and update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🔴 البوت في وضع الصيانة حالياً. حاول لاحقاً.")
        return
    
    # التحقق من أن المستخدم هو المالك
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص لمالك البوت فقط!")
        return
    
    # طلب كلمة المرور
    await update.message.reply_text(
        "🔐 <b>لوحة تحكم المالك</b>\n\n"
        "🔑 <b>يرجى إدخال كلمة المرور للمتابعة:</b>\n\n"
        "⚠️ لديك 60 ثانية فقط لإدخال كلمة المرور.",
        parse_mode='HTML'
    )
    context.user_data['waiting_pass'] = True

# ==========================================
# 👑 أوامر البث الجماعي والآيات للمالك
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
                f"✨ 📜 <b>آيَةٌ قُرْآنِيَّةٌ كَرِيمَةٌ تُنِيرُ القُلُوبْ</b> 📜 ✨\n"
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
# 👥 أوامر وخدمات المستخدمين العامة
# ==========================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if MAINTENANCE_MODE and update.effective_user.id != OWNER_ID: return
    save_chat_id(update.effective_chat.id, get_chat_display_name(update))
    help_text = (
        "✨ <b>قائمة خدمات البوت المتكاملة</b> ✨\n\n"
        "📥 <b>تحميل الفيديوهات:</b> أرسل رابط الفيديو مباشرة وسأقوم بتحميله.\n\n"
        "🎵 <b>تحميل الأغاني:</b> اكتب كلمة (يوت) متبوعة باسم الأغنية.\n\n"
        "✏️ <b>زخرفة الأسماء:</b> اكتب كلمة (زخرفة) متبوعة بالاسم.\n\n"
        "🛡️ <b>صلاحيات المشرفين:</b> قم بالرد بكلمة (كتم) لإظهار لوحة التحكم أو (طرد) للحظر.\n\n"
        "🔐 <b>للمالك:</b> استخدم /admin للوصول إلى لوحة التحكم."
    )
    await update.message.reply_text(help_text, reply_markup=get_main_menu(), parse_mode='HTML')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if MAINTENANCE_MODE and update.effective_user.id != OWNER_ID: return
    save_chat_id(update.effective_chat.id, get_chat_display_name(update))
    welcome_msg = (
        "🎯 <b>أهلاً بك في بوت الخدمات الشامل!</b>\n\n"
        "استخدم الأزرار بالأسفل لتصفح الخدمات أو أرسل /help لمعرفة الميزات.\n\n"
        "📌 <b>للمالك:</b> استخدم /admin للوصول إلى لوحة التحكم."
    )
    await update.message.reply_text(welcome_msg, reply_markup=get_main_menu(), parse_mode='HTML')

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

# ==========================================
# 🎨 قسم الزخرفة
# ==========================================
def decorate_name(name):
    """دالة الزخرفة المتكاملة"""
    decorations = [
        f"『{name}』", f"♔{name}♔", f"◈{name}◈", f"彡{name}彡",
        f"『☠』{name}『☠』", f"♛{name}♛", f"ツ{name}ツ", f"✿{name}✿"
    ]
    return "\n".join([f"{i+1}. {d}" for i, d in enumerate(decorations)])

# ==========================================
# 🎯 معالج الأزرار التفاعلية (Callback Query Handler)
# ==========================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # التحقق من أن المستخدم هو المالك
    if query.from_user.id != OWNER_ID:
        await query.edit_message_text("❌ هذه الأزرار مخصصة لمالك البوت فقط!")
        return

    if data == "bc_menu":
        await query.edit_message_text(
            "📢 <b>بث جماعي - أرسل رسالتك الآن</b>\n\n"
            "أرسل الرسالة التي تريد بثها لجميع المستخدمين.\n"
            "⚠️ لديك 60 ثانية فقط.",
            parse_mode='HTML'
        )
        context.user_data['waiting_bc_msg'] = True

    elif data == "verse_menu":
        await query.edit_message_text(
            "📖 <b>بث آية قرآنية - اختر رقم الآية</b>\n\n"
            "أرسل رقم الآية من 1 إلى 30.\n"
            "⚠️ لديك 60 ثانية فقط.",
            parse_mode='HTML'
        )
        context.user_data['waiting_verse_num'] = True

    elif data == "stats":
        if os.path.exists("chats.txt"):
            with open("chats.txt", "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            total = len(lines)
            await query.edit_message_text(
                f"📊 <b>إحصائيات البوت</b>\n\n"
                f"📈 إجمالي المشتركين: <b>{total}</b>\n"
                f"🟢 البوت يعمل بشكل طبيعي.",
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text("❌ لا يوجد أي مستخدمين مسجلين حالياً.")

    elif data == "mnt":
        global MAINTENANCE_MODE
        MAINTENANCE_MODE = not MAINTENANCE_MODE
        status = "🔴 مفعّل" if MAINTENANCE_MODE else "🟢 معطّل"
        await query.edit_message_text(f"⚙️ وضع الصيانة: {status}")

    elif data == "close":
        await query.edit_message_text("🚫 تم إغلاق لوحة التحكم.")
        context.user_data.clear()

    # معالجة أزرار الكتم والطرد للمشرفين
    elif data.startswith("mute_"):
        parts = data.split("_")
        if len(parts) >= 3:
            duration_type = parts[1]
            target_id = int(parts[2])
            chat_id = query.message.chat_id
            admin_id = query.from_user.id

            # التحقق من صلاحيات المشرف
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=admin_id)
            if member.status not in ['administrator', 'creator']:
                await query.edit_message_text("❌ ليس لديك صلاحيات كافية.")
                return

            # تحديد مدة الكتم
            durations = {
                "1m": timedelta(minutes=1),
                "15m": timedelta(minutes=15),
                "1h": timedelta(hours=1),
                "1d": timedelta(days=1),
                "2d": timedelta(days=2)
            }
            
            if duration_type in durations:
                until = datetime.now(timezone.utc) + durations[duration_type]
                try:
                    await context.bot.restrict_chat_member(
                        chat_id=chat_id,
                        user_id=target_id,
                        until_date=until,
                        permissions=ChatPermissions(can_send_messages=False)
                    )
                    user_mention = f'<a href="tg://user?id={target_id}">المستخدم</a>'
                    await query.edit_message_text(
                        f"✅ تم كتم {user_mention} لمدة {duration_type}.",
                        parse_mode='HTML'
                    )
                except Exception:
                    await query.edit_message_text("❌ فشل الكتم. تأكد من صلاحيات البوت.")

    elif data.startswith("kick_"):
        target_id = int(data.split("_")[1])
        chat_id = query.message.chat_id
        try:
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=target_id)
            user_mention = f'<a href="tg://user?id={target_id}">المستخدم</a>'
            await query.edit_message_text(
                f"🚷 تم طرد {user_mention} نهائياً.",
                parse_mode='HTML'
            )
        except Exception:
            await query.edit_message_text("❌ فشل الطرد. تأكد من صلاحيات البوت.")

# ==========================================
# 📥 الدالة المركزية لمعالجة كافة النصوص
# ==========================================
async def core_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if MAINTENANCE_MODE and update.effective_user.id != OWNER_ID: return
    if not update.message or not update.message.text: return
    
    save_chat_id(update.effective_chat.id, get_chat_display_name(update))
    text_received = update.message.text.strip()
    chat_id = update.effective_chat.id

    # معالجة انتظار الرسالة الجماعية من لوحة التحكم
    if context.user_data.get('waiting_bc_msg'):
        if update.effective_user.id != OWNER_ID: return
        context.user_data['waiting_bc_msg'] = False
        status_msg = await update.message.reply_text("📢 جاري إرسال البث الجماعي...")
        count = await run_broadcast_async(context.bot, text_received)
        await status_msg.edit_text(f"✅ تم بث رسالتك بنجاح إلى {count} مستخدم ومجموعة!")
        return

    # معالجة انتظار رقم الآية من لوحة التحكم
    if context.user_data.get('waiting_verse_num'):
        if update.effective_user.id != OWNER_ID: return
        context.user_data['waiting_verse_num'] = False
        try:
            v_num = int(text_received)
            if 1 <= v_num <= 30:
                selected_verse = QURAN_VERSES[v_num - 1]
                decorated_message = (
                    f"✨ 📜 <b>آيَةٌ قُرْآنِيَّةٌ كَرِيمَةٌ تُنِيرُ القُلُوبْ</b> 📜 ✨\n"
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
        return

    # نظام كلمة المرور للوحة التحكم (زر أدمن أو /admin)
    if context.user_data.get('waiting_pass'):
        if update.effective_user.id != OWNER_ID: return
        if text_received == ADMIN_PASS:
            context.user_data['waiting_pass'] = False
            await update.message.reply_text(
                "🖥️ <b>لوحة تحكم المالك الشاملة:</b>\nاختر أحد الإجراءات من القائمة التفاعلية أدناه:",
                reply_markup=get_admin_panel(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text("❌ كلمة السر خاطئة! تم إلغاء العملية.")
            context.user_data['waiting_pass'] = False
        return

    # معالجة أزرار القائمة الرئيسية
    if text_received == "👑 أدمن":
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ هذا الزر مخصص لمالك البوت فقط!")
            return
        await update.message.reply_text(
            "🔐 <b>لوحة تحكم المالك</b>\n\n"
            "🔑 <b>يرجى إدخال كلمة المرور للمتابعة:</b>",
            parse_mode='HTML'
        )
        context.user_data['waiting_pass'] = True
        return

    if text_received == "📥 تحميل":
        await update.message.reply_text(
            "📥 <b>قسم التحميل المتكامل:</b>\n\n"
            "🎬 أرسل رابط الفيديو مباشرة للتحميل.\n"
            "🎵 اكتب (يوت) + اسم الأغنية لتحميلها.",
            parse_mode='HTML'
        )
        return

    if text_received == "✨ زخرفة":
        await update.message.reply_text(
            "✏️ <b>قسم الزخرفة الاحترافي:</b>\n\n"
            "اكتب كلمة (زخرفة) متبوعة بالاسم الذي تريده.\n"
            "مثال: <code>زخرفة الأسطورة</code>",
            parse_mode='HTML'
        )
        return

    if text_received == "ℹ️ معلومات":
        user = update.effective_user
        info_text = f"👤 <b>معلوماتك شخصياً:</b>\nالاسم: {user.first_name}\n🆔 الآيدي: <code>{user.id}</code>"
        await update.message.reply_text(info_text, parse_mode='HTML')
        return

    # الرد على السلام
    if text_received in ["سلام", "سلام عليكم", "السلام عليكم", "السلام عليكم ورحمة الله", "السلام عليكم ورحمة الله وبركاته"]:
        user_mention = f'<a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>'
        greeting_reply = (
            f"✨ 💎 <b>『 وَعَلَيْكُمُ السَّلَامُ وَرَحْمَةُ اللهِ تَعَالَىٰ وَبَرَكَاتُهُ 』</b> 💎 ✨\n"
            f"╬════════════════════════╬\n"
            f"أهلاً وسهلاً بك يا غالي {user_mention} 🌸 نورت المجموعة!"
        )
        await update.message.reply_text(greeting_reply, parse_mode='HTML')
        return

    # قسم الزخرفة
    if text_received.startswith("زخرف ") or text_received.startswith("زخرفة "):
        parts = text_received.split(" ", 1)
        if len(parts) < 2 or not parts[1].strip():
            await update.message.reply_text("❌ يرجى كتابة الاسم المراد زخرفته.\nمثال: زخرفة أحمد")
            return
        name = parts[1].strip()
        decorated = decorate_name(name)
        result_text = (
            f"✨ <b>زخرفة الاسم:</b> {name}\n\n"
            f"{decorated}\n\n"
            f"اختر الزخرفة التي تعجبك! ✨"
        )
        await update.message.reply_text(result_text, parse_mode='HTML')
        return

    # هنا يمكن إضافة منطق التحميل وباقي الميزات

# ==========================================
# 🚀 الدالة الرئيسية لتشغيل البوت
# ==========================================
def main():
    # بدء سيرفر الفحص الصحي
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    # إعداد البوت
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    # تسجيل الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("getkey", generate_key))
    app.add_handler(CommandHandler("admin", admin_command))  # الأمر الجديد
    app.add_handler(CommandHandler("bc", owner_broadcast_command))
    app.add_handler(CommandHandler("verse", owner_verse_command))
    app.add_handler(CommandHandler("stats", owner_stats_command))
    app.add_handler(CommandHandler("mnt", owner_maintenance_command))
    
    # تسجيل المعالجات
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, core_text_handler))
    
    # بدء البوت
    print("🚀 البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
