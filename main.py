import logging
import random
import string
import os
import asyncio
import yt_dlp
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta, timezone
from telegram import Update, Bot, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# ==========================================
# ⚙️ إعدادات البوت الأساسية (قم بتعديلها)
# ==========================================
TOKEN = "8702640145:AAHyLv6r3xfyf9x-dptwim6_BrnJSbWYpmY"
OWNER_ID = 8038919535  # ⚠️ استبدل هذا الرقم بآيدي حسابك الحقيقي في تليجرام لتتحكم بالبوت

# وضع الصيانة الافتراضي
MAINTENANCE_MODE = False

# ==========================================
# 🌐 سيرفر الفحص الوهمي لتجنب إغلاق Render للبوت
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running successfully on Render Web Service!")

    def log_message(self, format, *args):
        return  # لمنع ملء الـ Logs بطلبات الفحص المتكررة

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
    "✨ ﴿ وَمَنْ يَتَوَكَّلْ عَلَى اللَّهِ فَهو حَسْبُهُ ﴾ ✨",
    "📖 ﴿ إِنَّ اللَّهَ مَعَ الصَّابِرِينَ ﴾ 📖",
    "✨ ﴿ وَإِذَا سَأَلَكَ عِبَادِي عَنِّي فَإِنِّي قَرِيبٌ ﴾ ✨",
    "📖 ﴿ وَلَسَوْفَ يُعْطِيكَ رَبُّكَ فَتَرْضَىٰ ﴾ 📖",
    "✨ ﴿ إِنَّ اللَّهَ وَمَلَائِكَتَهُ يُصَلُّونَ عَلَى النَّبِيِّ ﴾ ✨",
    "📖 ﴿ فَاذْكُرُونِي أَذْكُرْكُمْ وَاشْكُرُوا لِي وَلَا تَكْفُرُونِ ﴾ 📖",
    "✨ ﴿ لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا ﴾ 📖",
    "📖 ﴿ وَاعْتَصِمُوا بِحَبْلِ اللَّهِ جَمِيعًا وَلَا تَفَرَّقُوا ﴾ ✨",
    "✨ ﴿ قُلْ هُوَ اللَّهُ أَحَدٌ ﴾ 📖",
    "📖 ﴿ وَمَا Tَوْفِيقِي إِلَّا بِاللَّهِ ﴾ ✨",
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
    "✨ ﴿ نَبِّئْ عِبَادِي أَنِّي أَنَا الْغَفُورُ الرَّ الرحيمُ ﴾ 📖",
    "📖 ﴿ ادْعُونِي أَسْتَجِبْ لَكُمْ ﴾ ✨",
    "✨ ﴿ وَإِنْ تَعُدُّوا نِعْمَةَ اللَّهِ لَا تُحْصُوهَا ﴾ 📖",
    "📖 ﴿ قُلْ يَا عِبَادِيَ الَّذِينَ أَسْرَفُوا عَلَىٰ أَنْفُسِهِمْ لَا تَقْنَطُوا مِنْ رَحْمَةِ اللَّهِ ﴾ ✨"
]

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
    lines = []
    if os.path.exists("chats.txt"):
        with open("chats.txt", "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    
    exists = False
    for line in lines:
        if line.startswith(str(chat_id)):
            exists = True
            break
            
    if not exists:
        with open("chats.txt", "a", encoding="utf-8") as f:
            f.write(f"{chat_id}|{name}\n")

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
    if os.path.exists("chats.txt"):
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
    return 0

# ==========================================
# 👑 [أوامر التحكم السرية الخاصة بالمالك]
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
    await update.message.reply_text(help_text, parse_mode='HTML')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if MAINTENANCE_MODE and update.effective_user.id != OWNER_ID: return
    save_chat_id(update.effective_chat.id, get_chat_display_name(update))
    await update.message.reply_text("🎯 أهلاً بك في بوت الخدمات الشامل! أرسل /help لمعرفة كل الميزات المتوفرة.")

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
# 📥 الدالة المركزية لمعالجة كافة النصوص والتحميل والزخرفة
# ==========================================
async def core_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if MAINTENANCE_MODE and update.effective_user.id != OWNER_ID: return
    if not update.message or not update.message.text: return
    
    save_chat_id(update.effective_chat.id, get_chat_display_name(update))
    text_received = update.message.text.strip()
    chat_id = update.effective_chat.id

    # الرد التلقائي المزخرف على السلام
    if text_received in ["سلام", "سلام عليكم", "السلام عليكم", "السلام عليكم ورحمة الله", "السلام عليكم ورحمة الله وبركاته"]:
        user_mention = f'<a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>'
        greeting_reply = (
            f"✨ 💎 <b>『 وَعَلَيْكُمُ السَّلَامُ وَرَحْمَةُ اللهِ تَعَالَىٰ وَبَرَكَاتُهُ 』</b> 💎 ✨\n"
            f"╬════════════════════════╬\n"
            f"أهلاً وسهلاً بك يا غالي {user_mention} 🌸 نورت المجموعة وشرفتنا بحضورك المتميز!"
        )
        await update.message.reply_text(greeting_reply, parse_mode='HTML')
        return

    # قسم المشرفين (كتم وطرد)
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

    # 🔥 [قسم الزخرفات الأسطورية الشاملة المحدثة ديناميكياً] 🔥
    if text_received.startswith("زخرف ") or text_received.startswith("زخرفة "):
        parts = text_received.split(" ", 1)
        if len(parts) < 2 or not parts[1].strip():
            await update.message.reply_text("❌ يرجى كتابة الاسم بعد كلمة زخرف. مثال: <code>زخرفة أحمد</code>", parse_mode='HTML')
            return
        
        name = parts[1].strip()
        styles = [
            f"{name}™✓", f"亗 {name} 亗", f"〆{name}〆", f"々{name}★", f"ズ{name}气",
            f"么{name}米", f"♜{name}♜", f"⚡{name}⚡", f"⚔️{name}⚔️", f"👑{name}👑",
            f"꧁★{name}★꧂", f"꧁☬{name}☬꧂", f"⫷{name}⫸", f"◤{name}◥", f"【{name}】",
            f"░{name}░", f"⧼{name}⧽", f"╾{name}╼", f"ِٰ༻{name}༺", f"ּ{name}ּ",
            f"𓆩 {name} 𓆪", f"𓍼 {name} 𓍯", f"★彡 {name} 彡★", f"°•. {name} .•°",
            f" ── {name} ── ", f"╬═ {name} ═╬", f"☠️ {name} ☠️", f"『{name}』", f"↱{name}↰"
        ]
        
        result = "⚔️ <b>إليك تشكيلة الزخرفات الاحترافية الشاملة (اضغط على الاسم للنسخ الفوري):</b>\n\n"
        for index, style in enumerate(styles, 1):
            result += f"{index} . <code>{style}</code>\n"
        await update.message.reply_text(result, parse_mode='HTML')
        return

    # قسم تنزيل الموسيقى والآوديو عبر الأوامر النصية (يوت)
    if text_received.startswith("يوت "):
        query = text_received.replace("يوت ", "", 1).strip()
        if not query:
            await update.message.reply_text("❌ اكتب اسم الأغنية بعد الكلمة. مثال: <code>يوت تملي معاك</code>", parse_mode='HTML')
            return
        
        status_msg = await update.message.reply_text("🔎 <b>جاري البحث عن الأغنية وتحميلها، يرجى الانتظار...</b>", parse_mode='HTML')
        download_dir = "downloads"
        os.makedirs(download_dir, exist_ok=True)
        video_id = f"audio_{int(datetime.now().timestamp())}"
        
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': f'{download_dir}/{video_id}.%(ext)s',
            'default_search': 'ytsearch1',
            'max_filesize': 48 * 1024 * 1024,
            'quiet': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, query, download=True)
                title = info['entries'][0].get('title', 'Audio') if 'entries' in info else info.get('title', 'Audio')
                
            file_path = find_downloaded_file(download_dir, video_id)
            if file_path and os.path.exists(file_path):
                await status_msg.edit_text("⚡ <b>جاري رفع وإرسال الملف الصوتي الآن...</b>", parse_mode='HTML')
                with open(file_path, 'rb') as audio_file:
                    await update.message.reply_audio(audio=audio_file, title=title, caption=f"🎵 تم تحميل طلبك بنجاح: <b>{title}</b>", parse_mode='HTML')
                try: await status_msg.delete()
                except Exception: pass
                os.remove(file_path)
            else:
                await status_msg.edit_text("❌ عذراً، تعذر العثور على الأغنية أو تحميلها.")
        except Exception:
            try: await status_msg.edit_text("❌ حدث خطأ أثناء البحث والتحميل.")
            except Exception: pass
        return

    # قسم تحميل الفيديوهات التلقائي عند إرسال أي رابط
    if "http://" in text_received or "https://" in text_received:
        urls = [word for word in text_received.split() if word.startswith("http://") or word.startswith("https://")]
        if not urls: return
        url = urls[0]
        
        status_msg = await update.message.reply_text("📥 <b>تم رصد رابط! جاري جلب الفيديو وتحميله، انتظر ثواني...</b>", parse_mode='HTML')
        download_dir = "downloads"
        os.makedirs(download_dir, exist_ok=True)
        video_id = f"vid_{int(datetime.now().timestamp())}"
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': f'{download_dir}/{video_id}.%(ext)s',
            'max_filesize': 48 * 1024 * 1024,
            'quiet': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=True)
                title = info.get('title', 'Video')
                
            file_path = find_downloaded_file(download_dir, video_id)
            if file_path and os.path.exists(file_path):
                await status_msg.edit_text("⚡ <b>جاري رفع وإرسال مقطع الفيديو الآن...</b>", parse_mode='HTML')
                with open(file_path, 'rb') as video_file:
                    await update.message.reply_video(video=video_file, caption=f"🎬 <b>{title}</b>\n\nتم التحميل بنجاح ✅", parse_mode='HTML')
                try: await status_msg.delete()
                except Exception: pass
                os.remove(file_path)
            else:
                await status_msg.edit_text("❌ عذراً، حجم الفيديو كبير جداً أو الموقع غير مدعوم.")
        except Exception:
            try: await status_msg.edit_text("❌ فشل تحميل الفيديو.")
            except Exception: pass
        return

# ==========================================
# 🕹️ دالة معالجة نقرات أزرار التحكم بالمشرفين
# ==========================================
async def admin_menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    clicker_id = query.from_user.id
    
    member = await context.bot.get_chat_member(chat_id=chat_id, user_id=clicker_id)
    if member.status not in ['administrator', 'creator']:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ هذه الأزرار مخصصة للمشرفين فقط!")
        return

    data = query.data.split("_")
    action = data[0]

    if action == "kick":
        target_user_id = int(data[1])
        try:
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=target_user_id)
            await query.edit_message_text("🚷 <b>تم طرد العضو نهائياً من المجموعة بنجاح.</b>", parse_mode='HTML')
        except Exception:
            await query.edit_message_text("❌ لم أتمكن من طرد العضو.")
        return

    if action == "mute":
        duration_type = data[1]
        target_user_id = int(data[2])
        now = datetime.now(timezone.utc)
        
        if duration_type == "1m": until = now + timedelta(minutes=1); txt = "1 دقيقة"
        elif duration_type == "15m": until = now + timedelta(minutes=15); txt = "15 دقيقة"
        elif duration_type == "1h": until = now + timedelta(hours=1); txt = "ساعة واحدة"
        elif duration_type == "1d": until = now + timedelta(days=1); txt = "يوم واحد"
        elif duration_type == "2d": until = now + timedelta(days=2); txt = "يومين"
            
        permissions = ChatPermissions(can_send_messages=False)
        try:
            await context.bot.restrict_chat_member(chat_id=chat_id, user_id=target_user_id, permissions=permissions, until_date=until)
            await query.edit_message_text(f"🔒 <b>تم كتم العضو بنجاح لمدة ({txt}).</b>", parse_mode='HTML')
        except Exception:
            await query.edit_message_text(f"❌ لم أتمكن من كتم العضو.")

# ==========================================
# 🚀 نقطة التشغيل الرئيسية (معدلة ومصلحة لتجنب خطأ الـ Event Loop في Render)
# ==========================================
async def main():
    # تشغيل السيرفر الوهمي في Thread منفصل لعدم تعطيل البوت
    threading.Thread(target=run_health_check_server, daemon=True).start()

    # بناء تطبيق تليجرام
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    # إضافة الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("getkey", generate_key))
    
    # ربط أوامر التحكم السرية للمالك (تكتبها في خاص البوت)
    app.add_handler(CommandHandler("bc", owner_broadcast_command))
    app.add_handler(CommandHandler("verse", owner_verse_command))
    app.add_handler(CommandHandler("stats", owner_stats_command))
    app.add_handler(CommandHandler("mnt", owner_maintenance_command))
    
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, core_text_handler))
    app.add_handler(CallbackQueryHandler(admin_menu_click))
    
    print("🤖 Bot is completely optimized and running natively for Render Web Services...")
    
    # تهيئة وتشغيل البوت بطريقة متوافقة مع الـ Event loop
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # إبقاء البوت قيد التشغيل
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        # هذه هي الدالة السحرية التي تمنع ظهور خطأ RuntimeError
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
