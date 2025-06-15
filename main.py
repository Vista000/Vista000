from keepalive import keep_alive
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
)
import os
import time
import logging
import asyncio

keep_alive()

# --- تنظیمات لاگ ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- اطلاعات پایه ---
TOKEN = os.environ["TOKEN"]
ADMIN_ID = 458173350
SAMPLE_PATH, FULL_PATH = r"FREES", r"FULLS"

# --- پیام‌ها ---
bookMessage = """📚 کتابچه چیه؟  
1️⃣ اول فایل یه مقدمه کامل و تا-حدی-دلی داره، با همسنات مصاحبه کردم و راهکارهایی که برای 20 گرفتن دینی کمکشون کرده رو اونجا نوشتم. خیلیا گفتن با خوندن مقدمه توی ذهنشون جرقه خورده و ببیشتر به دینی علاقه‌مند شدن که باعث افتخارمونه!

2️⃣ چکیده‌ی درس‌ها، با کلمات رنگی رنگی و مثال‌هایی که به تفهیم مطلب کمک میکنن، هر رنگی یه معنی خاص داره
3️⃣ پاسخ تشریحی سوالات آخر درس (خود کتاب)

4️⃣ نمونه سوال متن درس، برای اینکه طراح اگه به سرش زد از متن سوال بده تو حرفه ای باشی
5️⃣ پاسخ‌ خیلی خیلی تشریحی! 

6️⃣ یه بخش جدید تازه اضافه شده به اسم #تعریفیات ! که جواب همه سوالات "فلان چیز را تعریف کنید" اونجاست! در پایان هر درس میتونی پیداش کنی 
➕ تعریفیات کل کتاب در پایان فایل! این یکی دیکه خیلی خفنه و مخصوص مرور شب امتحانه :)

* نکته مهم: #تعریفیات ! فعلا فقط برای پایه یازدهم در دسترسه. برای بقیه پایه ها به زودی اضافه میشه

💡 همین الان زیر 1 دقیقه می‌تونی کل فایل کتابچه رو تهیه‌ کنی! آماده‌ای؟"""

examMessage = """📝 آزمونچه چیه؟  
آزمونچه‌ها شامل سوالات تستی و تشریحی برای سنجش و تمرین بهتر مطالب کتابچه هستند.  
با داشتن آزمونچه می‌تونید خودتون رو بسنجید و برای امتحانات آماده بشید.  
توجه داشته باشید که آزمونچه‌ها فعلاً فقط برای پایه یازدهم فعال است."""

sampleReminder = "بهتره قبل از خرید نسخه کامل، درس اول تا سوم مخصوص پایه خودت رو رایگان دانلود کنی!"

paymentInfo = """💳 دمت گرم که یه قدم جدی به سمت نمره 20 برداشتی!  
برای دریافت نسخه کامل، فقط کافیه 79 هزارتومن واریز کنی اینجا 👇 و رسیدش رو هم همین‌جا ارسال کنی:

💳 5859 8312 3017 6678

🟡 ربات خودش رسید رو میفرسته برای ادمین. بعد از تایید ادمین، فایل کامل بدون هیچ مشکلی برات ارسال میشه. :>"""

FULL_BOOKLETS = {
    "نهم": "KetabcheFull9.pdf",
    "دهم": "KetabcheFull10.pdf",
    "یازدهم": "KetabcheFull11.pdf",
}
FULL_EXAMS = {"یازدهم": "AzmooncheFull11.pdf"}  # فقط یازدهم فعال است

# --- کیبوردها ---
mainKeyboard = ReplyKeyboardMarkup(
    [["نهم", "دهم"], ["یازدهم", "دوازدهم"], ["ℹ️ معرفی"]], resize_keyboard=True
)
choiceKeyboard = ReplyKeyboardMarkup(
    [["📚 کتابچه", "📝 آزمونچه"], ["🔙 بازگشت"]], resize_keyboard=True
)
readyKeyboard = ReplyKeyboardMarkup(
    [["✅ معلومه که آماده‌م!"], ["🔙 بازگشت"]], resize_keyboard=True
)
backOnlyKeyboard = ReplyKeyboardMarkup([["🔙 بازگشت"]], resize_keyboard=True)

# --- وضعیت کاربران ---
user_grades, user_ready, user_mode = {}, {}, {}


# --- فایل‌ها ---
def get_sample_filename(grade, mode):
    mapping = {
        "book": {
            "نهم": "Ketabche9Sample.pdf",
            "دهم": "Ketabche10Sample.pdf",
            "یازدهم": "Ketabche11Sample.pdf",
        },
        "exam": {
            "یازدهم": "Azmoonche11Sample.pdf",
        },  # فقط یازدهم فعال است
    }
    filename = mapping[mode].get(grade, "")
    return os.path.join(SAMPLE_PATH, filename)


def get_full_filename(grade, mode):
    mapping = FULL_BOOKLETS if mode == "book" else FULL_EXAMS
    filename = mapping.get(grade, "")
    return os.path.join(FULL_PATH, filename)


# --- هندلر پیام‌ها ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.text.strip() if message and message.text else None
    chat_id = str(update.effective_chat.id)

    if not text:
        return  # اگر متن نیست، هیچی نکن

    if text == "/start":
        await message.reply_text(
            "🎉 به ربات ویستانشر خوش اومدی!\nلطفاً پایه تحصیلی‌ت رو انتخاب کن:",
            reply_markup=mainKeyboard,
        )

    elif text in ["نهم", "دهم", "یازدهم", "دوازدهم"]:
        user_grades[chat_id] = text
        if text == "دوازدهم":
            await message.reply_text("❌ فعلاً محتوای خاصی برای پایه دوازدهم آماده نیست.")
        else:
            await message.reply_text(
                f"✅ پایه‌ی شما ({text}) ثبت شد.\nحالا انتخاب کن که دنبال چی هستی:",
                reply_markup=choiceKeyboard,
            )

    elif text in ["📚 کتابچه", "📝 آزمونچه"]:
        grade = user_grades.get(chat_id)
        if not grade:
            await message.reply_text("⛔ لطفاً ابتدا پایه تحصیلی خود را مشخص کن.")
            return
        mode = "book" if "کتابچه" in text else "exam"
        if mode == "exam" and grade != "یازدهم":
            await message.reply_text(
                "❌ آزمونچه در حال حاضر فقط برای پایه یازدهم فعاله.",
                reply_markup=backOnlyKeyboard,
            )
            return

        user_mode[chat_id] = mode
        await message.reply_text(bookMessage if mode == "book" else examMessage)
        await context.bot.send_message(chat_id=chat_id, text=sampleReminder)

        filepath = get_sample_filename(grade, mode)
        if os.path.exists(filepath):
            try:
                with open(filepath, "rb") as doc:
                    await context.bot.send_document(
                        chat_id=chat_id, document=doc, caption="📄 نمونه فایل رو ببین!"
                    )
                await asyncio.sleep(0.5)
                if get_full_filename(grade, mode):
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="آماده‌ای برای دریافت نسخه کامل؟ 👇",
                        reply_markup=readyKeyboard,
                    )
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="⚠️ نسخه کامل فعلاً آماده نیست.",
                        reply_markup=backOnlyKeyboard,
                    )
            except Exception as e:
                print(f"[ERROR] Sample send fail: {e}")
                await message.reply_text("❌ مشکل در ارسال فایل. لطفاً به ادمین پیام بده.")
        else:
            await message.reply_text("❌ فایل نمونه موجود نیست. لطفاً به ادمین پیام بده.")

    elif text == "✅ معلومه که آماده‌م!":
        grade, mode = user_grades.get(chat_id), user_mode.get(chat_id)
        if not get_full_filename(grade, mode):
            await message.reply_text(
                "⛔ نسخه کامل برای این پایه فعلاً آماده نیست.", reply_markup=backOnlyKeyboard
            )
        else:
            user_ready[chat_id] = True
            await message.reply_text(paymentInfo)

    elif text == "ℹ️ معرفی":
        await message.reply_text(
            "ما در ویستانشر محتوای دینی زرتشتی برای دانش‌آموزان تولید می‌کنیم. 📘🌟"
        )

    elif text == "🔙 بازگشت":
        await message.reply_text("بازگشتی موفقیت‌آمیز 😄", reply_markup=mainKeyboard)

    elif user_ready.get(chat_id):
        try:
            await context.bot.send_message(
                ADMIN_ID, f"📥 رسید از کاربر {chat_id} دریافت شد:"
            )
            await context.bot.forward_message(
                chat_id=ADMIN_ID, from_chat_id=int(chat_id), message_id=message.message_id
            )
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text="📌 برای تأیید پرداخت، روی دکمه زیر بزن:",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("تأیید پرداخت", callback_data=f"confirm_{chat_id}")]]
                ),
            )
            await message.reply_text("✅ رسیدت توسط بات برای ادمین ارسال شد.")
            user_ready[chat_id] = False
        except Exception as e:
            print(f"[ERROR] رسید ارسال نشد: {e}")
            await message.reply_text("❌ خطا در ارسال رسید. لطفاً دوباره امتحان کن.")

    elif chat_id != str(ADMIN_ID):
        await message.reply_text("📩 پیام شما ثبت شد و به ادمین ارسال می‌شود.")
        await context.bot.forward_message(
            chat_id=ADMIN_ID, from_chat_id=int(chat_id), message_id=message.message_id
        )


# --- تأیید ادمین ---
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("confirm_") and str(query.message.chat.id) == str(ADMIN_ID):
        target_id = query.data.split("_")[1]
        grade, mode = user_grades.get(target_id), user_mode.get(target_id)
        filepath = get_full_filename(grade, mode)

        if filepath and os.path.exists(filepath):
            try:
                with open(filepath, "rb") as doc:
                    await context.bot.send_document(
                        chat_id=int(target_id),
                        document=doc,
                        caption="📦 نسخه کامل آماده‌ست. موفق باشی! 🌟",
                    )
                await context.bot.send_message(
                    chat_id=int(target_id),
                    text=(
                        " ✅ پرداختت تأیید شد و فایل برات ارسال شد. هرسوالی داشتی میتونی خیلی راحت از ادمین بپرسی.امیدوارم بخونی، خوشت بیاد و حتما بهم پیام بدی! 😊"
                    ),
                )
            except Exception as e:
                print(f"[ERROR] Full file send fail: {e}")


# --- اجرای ربات ---
def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", handle_message))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    application.run_polling()


if __name__ == "__main__":
    main()
