#7286317589:AAGQzHVEkMsnwaH1NB6hOA5Y4bn8vo7pJu0
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler

# فایل ذخیره‌سازی داده‌ها
DATA_FILE = "data.json"

# مراحل مکالمه
ITEM, AMOUNT, BUYER, PARTICIPANTS, EDIT_ITEM, EDIT_FIELD, EDIT_VALUE = range(7)

# بارگذاری داده‌ها از فایل
def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"purchases": [], "balances": {}, "members": []}

# ذخیره داده‌ها در فایل
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# داده‌های برنامه
data = load_data()

# شروع مکالمه
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = "سلام! لیست دستورات:\n"
    response += "/add - ثبت خرید جدید\n"
    response += "/list - مشاهده لیست خریدها\n"
    response += "/balances - مشاهده مانده حساب‌ها\n"
    response += "/members - مدیریت اعضا\n"
    response += "/edit - ویرایش خریدها\n"
    await update.message.reply_text(response)

# مدیریت اعضا
async def manage_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    members = data.get("members", [])
    response = "لیست اعضا:\n" + "\n".join(members) if members else "هیچ عضوی ثبت نشده است."
    response += "\n\nبرای اضافه کردن عضو، دستور زیر را ارسال کنید:\n/add_member [نام عضو]"
    await update.message.reply_text(response)

async def add_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member_name = " ".join(context.args)
    if not member_name:
        await update.message.reply_text("لطفاً نام عضو را وارد کنید.")
        return
    if member_name in data["members"]:
        await update.message.reply_text("این عضو قبلاً ثبت شده است.")
        return
    data["members"].append(member_name)
    save_data(data)
    await update.message.reply_text(f"عضو {member_name} با موفقیت اضافه شد.")

# شروع ثبت خرید
async def add_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفاً نام محصول را وارد کنید:")
    return ITEM

# دریافت نام محصول
async def get_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["item"] = update.message.text
    await update.message.reply_text("لطفاً مبلغ خرید را وارد کنید:")
    return AMOUNT

# دریافت مبلغ
async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["amount"] = int(update.message.text)
        await update.message.reply_text("لطفاً نام خریدار را وارد کنید:")
        return BUYER
    except ValueError:
        await update.message.reply_text("لطفاً مبلغ را به صورت عدد وارد کنید:")
        return AMOUNT

# دریافت نام خریدار
async def get_buyer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buyer = update.message.text
    if buyer not in data["members"]:
        await update.message.reply_text("این خریدار در لیست اعضا نیست. لطفاً ابتدا عضو را اضافه کنید.")
        return BUYER
    context.user_data["buyer"] = buyer
    await update.message.reply_text("لطفاً نام افرادی که در خرید شرکت داشتند را با فاصله وارد کنید (مثال: آرش علی سارا):")
    return PARTICIPANTS

# دریافت اعضا و ثبت خرید
async def get_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    participants = update.message.text.split()
    invalid_members = [p for p in participants if p not in data["members"]]
    if invalid_members:
        await update.message.reply_text(f"اعضای زیر در لیست اعضا نیستند: {', '.join(invalid_members)}\nلطفاً ابتدا آن‌ها را اضافه کنید.")
        return PARTICIPANTS

    context.user_data["participants"] = participants
    item = context.user_data["item"]
    amount = context.user_data["amount"]
    buyer = context.user_data["buyer"]

    # تولید کد یکتا
    purchase_id = len(data["purchases"]) + 1
    purchase = {
        "id": purchase_id,
        "item": item,
        "amount": amount,
        "date": update.message.date.strftime("%Y-%m-%d"),
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
    await update.message.reply_text(f"خرید {item} به مبلغ {amount} تومان ثبت شد.\nکد خرید: {purchase_id}")
    return ConversationHandler.END

# مشاهده لیست خریدها
async def list_purchases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data["purchases"]:
        await update.message.reply_text("هیچ خریدی ثبت نشده است.")
        return
    response = "لیست خریدها:\n"
    for purchase in data["purchases"]:
        response += f"{purchase['id']}. {purchase['item']} - {purchase['amount']} تومان - خریدار: {purchase['buyer']} - تاریخ: {purchase['date']}\n"
    await update.message.reply_text(response)

# ویرایش خرید
async def edit_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفاً کد خریدی که می‌خواهید ویرایش کنید را وارد کنید:")
    return EDIT_ITEM

async def get_edit_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        purchase_id = int(update.message.text)
        purchase = next((p for p in data["purchases"] if p["id"] == purchase_id), None)
        if not purchase:
            await update.message.reply_text("خرید با این کد یافت نشد.")
            return EDIT_ITEM
        context.user_data["edit_item"] = purchase
        await update.message.reply_text("لطفاً فیلدی که می‌خواهید ویرایش کنید را وارد کنید (item, amount, buyer, participants):")
        return EDIT_FIELD
    except ValueError:
        await update.message.reply_text("لطفاً کد خرید را به درستی وارد کنید.")
        return EDIT_ITEM

async def get_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = update.message.text
    if field not in ["item", "amount", "buyer", "participants"]:
        await update.message.reply_text("فیلد نامعتبر است. لطفاً دوباره تلاش کنید.")
        return EDIT_FIELD
    context.user_data["edit_field"] = field
    await update.message.reply_text("لطفاً مقدار جدید را وارد کنید:")
    return EDIT_VALUE

async def get_edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = context.user_data["edit_field"]
    purchase = context.user_data["edit_item"]
    new_value = update.message.text

    if field == "amount":
        try:
            new_value = int(new_value)
        except ValueError:
            await update.message.reply_text("لطفاً مقدار عددی صحیح وارد کنید.")
            return EDIT_VALUE

    purchase[field] = new_value
    save_data(data)
    await update.message.reply_text(f"فیلد {field} با موفقیت ویرایش شد.")
    return ConversationHandler.END

# مشاهده مانده حساب‌ها
async def balances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data["balances"]:
        await update.message.reply_text("هیچ اطلاعاتی موجود نیست.")
        return
    response = "مانده حساب افراد:\n"
    for person, balance in data["balances"].items():
        response += f"{person}: {'+' if balance > 0 else ''}{balance} تومان\n"
    await update.message.reply_text(response)

# لغو مکالمه
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("فرایند لغو شد.")
    return ConversationHandler.END

# اجرای برنامه
if __name__ == '__main__':
    app = ApplicationBuilder().token("7286317589:AAGQzHVEkMsnwaH1NB6hOA5Y4bn8vo7pJu0").build()

    # تعریف مکالمه‌ها
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add_purchase)],
        states={
            ITEM: [MessageHandler(filters.TEXT, get_item)],
            AMOUNT: [MessageHandler(filters.TEXT, get_amount)],
            BUYER: [MessageHandler(filters.TEXT, get_buyer)],
            PARTICIPANTS: [MessageHandler(filters.TEXT, get_participants)],
            EDIT_ITEM: [MessageHandler(filters.TEXT, get_edit_item)],
            EDIT_FIELD: [MessageHandler(filters.TEXT, get_edit_field)],
            EDIT_VALUE: [MessageHandler(filters.TEXT, get_edit_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

        # ثبت دستورات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_purchase))
    app.add_handler(CommandHandler("list", list_purchases))
    app.add_handler(CommandHandler("balances", balances))
    app.add_handler(CommandHandler("members", manage_members))
    app.add_handler(CommandHandler("add_member", add_member))
    app.add_handler(CommandHandler("edit", edit_purchase))
    app.add_handler(conv_handler)

    print("ربات در حال اجرا است...")
    app.run_polling()
