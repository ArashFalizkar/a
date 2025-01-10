#7286317589:AAGQzHVEkMsnwaH1NB6hOA5Y4bn8vo7pJu0
# 7042785861:AAGqpupr0ple996Nqsfn_ZHmiuy5w4RST3E
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# فایل ذخیره‌سازی داده‌ها
DATA_FILE = "enhanced_data.json"

# لیست افراد مجاز
AUTHORIZED_MEMBERS = ["عرفان کدیور", "عرفان راضی", "یدالله", "سینا", "ارش"]

# بارگذاری داده‌ها
def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"purchases": [], "current_input": {}}

# ذخیره داده‌ها
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# داده‌های برنامه
data = load_data()

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = (
        "سلام! لیست دستورات:\n"
        "/add - ثبت خرید جدید\n"
        "/list - مشاهده خریدها\n"
        "/edit - ویرایش یک خرید\n"
        "/delete - حذف یک خرید\n"
        "/balances - مشاهده مانده حساب\n"
        "لیست اعضای مجاز: " + ", ".join(AUTHORIZED_MEMBERS)
    )
    await update.message.reply_text(response)

# مرحله اول ثبت خرید
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data["current_input"][update.effective_user.id] = {}
    save_data(data)
    await update.message.reply_text("نام محصول را وارد کنید:")

# مدیریت مراحل ثبت خرید
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in data["current_input"]:
        await update.message.reply_text("لطفاً با دستور /add ثبت خرید را شروع کنید.")
        return

    current_input = data["current_input"][user_id]
    if "item" not in current_input:
        current_input["item"] = update.message.text
        save_data(data)
        await update.message.reply_text("مبلغ خرید را وارد کنید:")
    elif "amount" not in current_input:
        try:
            current_input["amount"] = int(update.message.text)
            save_data(data)
            keyboard = [[member] for member in AUTHORIZED_MEMBERS]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text("نام خریدار را انتخاب کنید:", reply_markup=reply_markup)
        except ValueError:
            await update.message.reply_text("لطفاً مبلغ را به صورت عدد وارد کنید.")
    elif "buyer" not in current_input:
        if update.message.text in AUTHORIZED_MEMBERS:
            current_input["buyer"] = update.message.text
            save_data(data)
            keyboard = [[member] for member in AUTHORIZED_MEMBERS]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text("نام شرکت‌کنندگان را یکی‌یکی وارد کنید (پایان با /done):", reply_markup=reply_markup)
        else:
            await update.message.reply_text("لطفاً از لیست افراد مجاز انتخاب کنید.")
    elif "participants" not in current_input:
        if "participants" not in current_input:
            current_input["participants"] = []

        if update.message.text == "/done":
            if not current_input["participants"]:
                await update.message.reply_text("لطفاً حداقل یک شرکت‌کننده اضافه کنید.")
            else:
                data["purchases"].append(current_input)
                del data["current_input"][user_id]
                save_data(data)
                await update.message.reply_text("خرید ثبت شد!")
        elif update.message.text in AUTHORIZED_MEMBERS:
            if update.message.text not in current_input["participants"]:
                current_input["participants"].append(update.message.text)
                save_data(data)
                await update.message.reply_text(f"{update.message.text} اضافه شد. شرکت‌کنندگان فعلی: {', '.join(current_input['participants'])}")
            else:
                await update.message.reply_text("این فرد قبلاً اضافه شده است.")
        else:
            await update.message.reply_text("لطفاً از لیست افراد مجاز انتخاب کنید.")

# مشاهده لیست خریدها
async def list_purchases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data["purchases"]:
        await update.message.reply_text("هیچ خریدی ثبت نشده است.")
        return

    response = "لیست خریدها:\n"
    for i, purchase in enumerate(data["purchases"], start=1):
        response += f"{i}. {purchase['item']} - {purchase['amount']} تومان - خریدار: {purchase['buyer']} - شرکت‌کنندگان: {', '.join(purchase['participants'])}\n"
    await update.message.reply_text(response)

# حذف خرید
async def delete_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data["purchases"]:
        await update.message.reply_text("هیچ خریدی برای حذف وجود ندارد.")
        return

    response = "کدام خرید را می‌خواهید حذف کنید؟\n"
    for i, purchase in enumerate(data["purchases"], start=1):
        response += f"{i}. {purchase['item']} - {purchase['amount']} تومان\n"
    await update.message.reply_text(response)
    context.user_data["action"] = "delete"

# ویرایش خرید
async def edit_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data["purchases"]:
        await update.message.reply_text("هیچ خریدی برای ویرایش وجود ندارد.")
        return

    response = "کدام خرید را می‌خواهید ویرایش کنید؟\n"
    for i, purchase in enumerate(data["purchases"], start=1):
        response += f"{i}. {purchase['item']} - {purchase['amount']} تومان\n"
    await update.message.reply_text(response)
    context.user_data["action"] = "edit"

# حذف/ویرایش عملیات
async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "action" not in context.user_data:
        await update.message.reply_text("لطفاً ابتدا عملیات موردنظر را مشخص کنید.")
        return

    action = context.user_data["action"]
    try:
        index = int(update.message.text) - 1
        if index < 0 or index >= len(data["purchases"]):
            await update.message.reply_text("شماره واردشده نامعتبر است.")
            return

        if action == "delete":
            deleted_purchase = data["purchases"].pop(index)
            save_data(data)
            await update.message.reply_text(f"خرید {deleted_purchase['item']} حذف شد.")
        elif action == "edit":
            context.user_data["edit_index"] = index
            data["current_input"][update.effective_user.id] = data["purchases"][index]
            await update.message.reply_text("ویرایش آغاز شد. لطفاً اطلاعات جدید را وارد کنید.")
        del context.user_data["action"]
    except ValueError:
        await update.message.reply_text("لطفاً یک شماره معتبر وارد کنید.")

# اجرای ربات
if __name__ == '__main__':
    app = ApplicationBuilder().token("7042785861:AAGqpupr0ple996Nqsfn_ZHmiuy5w4RST3E").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_start))
    app.add_handler(CommandHandler("list", list_purchases))
    app.add_handler(CommandHandler("delete", delete_purchase))
    app.add_handler(CommandHandler("edit", edit_purchase))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^\d+$'), handle_action))

    print("ربات در حال اجرا است...")
    app.run_polling()
