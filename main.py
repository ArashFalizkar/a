#7286317589:AAGQzHVEkMsnwaH1NB6hOA5Y4bn8vo7pJu0
#7042785861:AAGqpupr0ple996Nqsfn_ZHmiuy5w4RST3E
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# فایل ذخیره‌سازی داده‌ها
DATA_FILE = "simple_data.json"

# بارگذاری داده‌ها
def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"purchases": [], "balances": {}}

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
        "/add [محصول] [مبلغ] [خریدار] [شرکت‌کنندگان] - ثبت خرید\n"
        "/list - مشاهده خریدها\n"
        "/balances - مشاهده مانده حساب\n"
    )
    await update.message.reply_text(response)

# ثبت خرید
async def add_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 4:
            await update.message.reply_text("لطفاً اطلاعات کامل وارد کنید: /add [محصول] [مبلغ] [خریدار] [شرکت‌کنندگان]")
            return

        item = args[0]
        amount = int(args[1])
        buyer = args[2]
        participants = args[3:]

        # افزودن خرید به لیست
        purchase = {
            "item": item,
            "amount": amount,
            "buyer": buyer,
            "participants": participants,
        }
        data["purchases"].append(purchase)

        # محاسبه سهم‌ها
        share = amount / len(participants)
        for person in participants:
            if person not in data["balances"]:
                data["balances"][person] = 0
            if person == buyer:
                data["balances"][person] += amount - share
            else:
                data["balances"][person] -= share

        save_data(data)
        await update.message.reply_text(f"خرید {item} به مبلغ {amount} ثبت شد.")
    except ValueError:
        await update.message.reply_text("مبلغ باید به صورت عدد وارد شود.")

# مشاهده لیست خریدها
async def list_purchases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data["purchases"]:
        await update.message.reply_text("هیچ خریدی ثبت نشده است.")
        return

    response = "لیست خریدها:\n"
    for i, purchase in enumerate(data["purchases"], start=1):
        response += f"{i}. {purchase['item']} - {purchase['amount']} تومان - خریدار: {purchase['buyer']} - شرکت‌کنندگان: {', '.join(purchase['participants'])}\n"
    await update.message.reply_text(response)

# مشاهده مانده حساب‌ها
async def balances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data["balances"]:
        await update.message.reply_text("هیچ اطلاعاتی موجود نیست.")
        return

    response = "مانده حساب افراد:\n"
    for person, balance in data["balances"].items():
        response += f"{person}: {'+' if balance > 0 else ''}{balance} تومان\n"
    await update.message.reply_text(response)

# اجرای ربات
if __name__ == '__main__':
    app = ApplicationBuilder().token("7042785861:AAGqpupr0ple996Nqsfn_ZHmiuy5w4RST3E").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_purchase))
    app.add_handler(CommandHandler("list", list_purchases))
    app.add_handler(CommandHandler("balances", balances))

    print("ربات در حال اجرا است...")
    app.run_polling()
