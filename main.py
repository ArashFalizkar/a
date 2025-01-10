#7286317589:AAGQzHVEkMsnwaH1NB6hOA5Y4bn8vo7pJu0
# 7042785861:AAGqpupr0ple996Nqsfn_ZHmiuy5w4RST3E
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler

# فایل ذخیره‌سازی داده‌ها
DATA_FILE = "data.json"

# مراحل مکالمه
SELECT_ACTION, ITEM, AMOUNT, BUYER, PARTICIPANTS, EDIT_OR_DELETE, EDIT_ITEM, EDIT_AMOUNT, EDIT_BUYER, EDIT_PARTICIPANTS = range(10)

# بارگذاری داده‌ها از فایل
def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"purchases": [], "balances": {}}

# ذخیره داده‌ها در فایل
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# داده‌های برنامه
data = load_data()

# شروع مکالمه
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    actions = [["افزودن خرید", "مشاهده خریدها"], ["ویرایش یا حذف خرید", "مشاهده مانده حساب"]]
    await update.message.reply_text(
        "سلام! لطفاً یک عملیات انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(actions, one_time_keyboard=True)
    )
    return SELECT_ACTION

# انتخاب عملیات
async def select_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = update.message.text
    if user_choice == "افزودن خرید":
        await update.message.reply_text("لطفاً نام محصول را وارد کنید:")
        return ITEM
    elif user_choice == "مشاهده خریدها":
        await list_purchases(update, context)
        return ConversationHandler.END
    elif user_choice == "ویرایش یا حذف خرید":
        await edit_or_delete_prompt(update, context)
        return EDIT_OR_DELETE
    elif user_choice == "مشاهده مانده حساب":
        await balances(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("انتخاب نامعتبر است. لطفاً دوباره تلاش کنید.")
        return SELECT_ACTION

# شروع ثبت خرید
async def get_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["item"] = update.message.text
    await update.message.reply_text("لطفاً مبلغ خرید را وارد کنید:")
    return AMOUNT

# دریافت مبلغ
async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["amount"] = int(update.message.text)
        buyers = [["عرفان", "کدیور", "عرفان راضی"], ["یدالله", "سینا", "ارش"]]
        await update.message.reply_text(
            "لطفاً نام خریدار را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(buyers, one_time_keyboard=True)
        )
        return BUYER
    except ValueError:
        await update.message.reply_text("لطفاً مبلغ را به صورت عدد وارد کنید:")
        return AMOUNT

# دریافت نام خریدار
async def get_buyer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["buyer"] = update.message.text
    await update.message.reply_text("لطفاً نام افرادی که در خرید شرکت داشتند را با فاصله وارد کنید (مثال: عرفان سینا ارش):")
    return PARTICIPANTS

# دریافت اعضا و ثبت خرید
async def get_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global data
    participants = update.message.text.split()
    context.user_data["participants"] = participants

    item = context.user_data["item"]
    amount = context.user_data["amount"]
    buyer = context.user_data["buyer"]

    # ذخیره خرید در داده‌ها
    purchase = {
        "id": len(data["purchases"]) + 1,
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

    # ذخیره‌سازی داده‌ها
    save_data(data)

    await update.message.reply_text(f"خرید {item} به مبلغ {amount} تومان ثبت شد.")
    return ConversationHandler.END

# مشاهده لیست خریدها
async def list_purchases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global data
    if not data["purchases"]:
        await update.message.reply_text("هیچ خریدی ثبت نشده است.")
        return
    response = "لیست خریدها:\n"
    for purchase in data["purchases"]:
        response += f"{purchase['id']}. {purchase['item']} - {purchase['amount']} تومان - خریدار: {purchase['buyer']}\n"
    await update.message.reply_text(response)

# مشاهده مانده حساب‌ها
async def balances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global data
    if not data["balances"]:
        await update.message.reply_text("هیچ اطلاعاتی موجود نیست.")
        return
    response = "مانده حساب افراد:\n"
    for person, balance in data["balances"].items():
        response += f"{person}: {'+' if balance > 0 else ''}{balance} تومان\n"
    await update.message.reply_text(response)

# ویرایش یا حذف خرید
async def edit_or_delete_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global data
    if not data["purchases"]:
        await update.message.reply_text("هیچ خریدی برای ویرایش یا حذف موجود نیست.")
        return ConversationHandler.END

    response = "برای ویرایش یا حذف، شناسه خرید را وارد کنید:\n"
    for purchase in data["purchases"]:
        response += f"{purchase['id']}. {purchase['item']} - {purchase['amount']} تومان\n"
    await update.message.reply_text(response)
    return EDIT_OR_DELETE

# عملیات ویرایش یا حذف
async def edit_or_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global data
    try:
        purchase_id = int(update.message.text)
        purchase = next((p for p in data["purchases"] if p["id"] == purchase_id), None)
        if not purchase:
            await update.message.reply_text("شناسه نامعتبر است. لطفاً دوباره تلاش کنید.")
            return EDIT_OR_DELETE

        actions = [["ویرایش", "حذف"]]
        context.user_data["edit_purchase"] = purchase
        await update.message.reply_text(
            f"خرید انتخاب شده: {purchase['item']} - {purchase['amount']} تومان\nعملیات مورد نظر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(actions, one_time_keyboard=True)
        )
        return SELECT_ACTION
    except ValueError:
        await update.message.reply_text("شناسه باید عدد باشد. لطفاً دوباره تلاش کنید.")
        return EDIT_OR_DELETE

# ویرایش خرید
async def edit_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    purchase = context.user_data.get("edit_purchase")
    if not purchase:
        await update.message.reply_text("هیچ خریدی برای ویرایش پیدا نشد.")
        return ConversationHandler.END
    
    action = update.message.text
    if action == "ویرایش":
        await update.message.reply_text("لطفاً انتخاب کنید که کدام بخش را ویرایش کنید: محصول، مبلغ، خریدار، یا افراد شرکت‌کننده")
        return EDIT_ITEM
    elif action == "حذف":
        data["purchases"].remove(purchase)
        save_data(data)
        await update.message.reply_text(f"خرید {purchase['item']} حذف شد.")
        return ConversationHandler.END

# ویرایش محصول
async def edit_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["edit_purchase"]["item"] = update.message.text
    await update.message.reply_text("محصول به روزرسانی شد. برای ویرایش مبلغ، لطفاً مبلغ جدید را وارد کنید:")
    return EDIT_AMOUNT

# ویرایش مبلغ
async def edit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["edit_purchase"]["amount"] = int(update.message.text)
        await update.message.reply_text("مبلغ به روزرسانی شد. برای ویرایش خریدار، لطفاً نام خریدار جدید را وارد کنید:")
        return EDIT_BUYER
    except ValueError:
        await update.message.reply_text("لطفاً مبلغ را به صورت عدد وارد کنید:")
        return EDIT_AMOUNT

# ویرایش خریدار
async def edit_buyer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["edit_purchase"]["buyer"] = update.message.text
    await update.message.reply_text("خریدار به روزرسانی شد. برای ویرایش افراد شرکت‌کننده، لطفاً نام افراد جدید را وارد کنید:")
    return EDIT_PARTICIPANTS

# ویرایش افراد شرکت‌کننده
async def edit_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    participants = update.message.text.split()
    context.user_data["edit_purchase"]["participants"] = participants

    # به روز رسانی سهم‌ها
    purchase = context.user_data["edit_purchase"]
    amount = purchase["amount"]
    participants = purchase["participants"]
    share = amount / len(participants)
    
    for person in participants:
        if person not in data["balances"]:
            data["balances"][person] = 0
        if person == purchase["buyer"]:
            data["balances"][person] += amount - share
        else:
            data["balances"][person] -= share
    
    # ذخیره‌سازی داده‌ها
    save_data(data)
    await update.message.reply_text(f"خرید {purchase['item']} به روزرسانی شد.")
    return ConversationHandler.END

# لغو مکالمه
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END

# اجرای برنامه
if __name__ == '__main__':
    app = ApplicationBuilder().token("7042785861:AAGqpupr0ple996Nqsfn_ZHmiuy5w4RST3E").build()

    # تعریف مکالمه
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_ACTION: [MessageHandler(filters.TEXT, select_action)],
            ITEM: [MessageHandler(filters.TEXT, get_item)],
            AMOUNT: [MessageHandler(filters.TEXT, get_amount)],
            BUYER: [MessageHandler(filters.TEXT, get_buyer)],
            PARTICIPANTS: [MessageHandler(filters.TEXT, get_participants)],
            EDIT_OR_DELETE: [MessageHandler(filters.TEXT, edit_or_delete)],
            EDIT_ITEM: [MessageHandler(filters.TEXT, edit_item)],
            EDIT_AMOUNT: [MessageHandler(filters.TEXT, edit_amount)],
            EDIT_BUYER: [MessageHandler(filters.TEXT, edit_buyer)],
            EDIT_PARTICIPANTS: [MessageHandler(filters.TEXT, edit_participants)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ثبت دستورات
    app.add_handler(conv_handler)
    app.run_polling()

