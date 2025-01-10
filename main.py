#7286317589:AAGQzHVEkMsnwaH1NB6hOA5Y4bn8vo7pJu0
# 7042785861:AAGqpupr0ple996Nqsfn_ZHmiuy5w4RST3E
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import json

# Global Variables
orders = []
accounts = {"ارش": 0, "راضی": 0, "کدیور": 0, "یدالله": 0, "سینا": 0}

# File Operations
def save_data():
    with open("data.json", "w") as file:
        json.dump({"orders": orders, "accounts": accounts}, file, ensure_ascii=False, indent=4)

def load_data():
    global orders, accounts
    try:
        with open("data.json", "r") as file:
            data = json.load(file)
            orders = data["orders"]
            accounts = data["accounts"]
    except FileNotFoundError:
        orders = []
        accounts = {"ارش": 0, "راضی": 0, "کدیور": 0, "یدالله": 0, "سینا": 0}

# Calculate Shares
def calculate_shares(item, amount, buyer, participants):
    global accounts
    split_amount = amount / len(participants)
    for participant in participants:
        if participant != buyer:
            accounts[participant] -= split_amount
    accounts[buyer] += amount - split_amount * (len(participants) - 1)

# Start Command
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("ثبت خرید", callback_data="register_purchase")],
        [InlineKeyboardButton("لیست سفارش‌ها", callback_data="list_orders")],
        [InlineKeyboardButton("حذف سفارش", callback_data="delete_order")],
        [InlineKeyboardButton("ویرایش سفارش", callback_data="edit_order")],
        [InlineKeyboardButton("مشاهده حساب‌ها", callback_data="view_accounts")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("لطفاً یک گزینه را انتخاب کنید:", reply_markup=reply_markup)

# Button Handler
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == "register_purchase":
        query.message.reply_text("چه چیزی خرید شده است؟")
        context.user_data["state"] = "ask_item"
    elif query.data == "list_orders":
        if orders:
            message = "لیست سفارش‌ها:\n" + "\n".join([f"کد {i+1}: {o['item']} - {o['amount']} تومان" for i, o in enumerate(orders)])
        else:
            message = "هیچ سفارشی ثبت نشده است."
        query.message.reply_text(message)
    elif query.data == "delete_order":
        query.message.reply_text("کد سفارش برای حذف را وارد کنید:")
        context.user_data["state"] = "ask_delete_order"
    elif query.data == "edit_order":
        query.message.reply_text("کد سفارش برای ویرایش را وارد کنید:")
        context.user_data["state"] = "ask_edit_order"
    elif query.data == "view_accounts":
        message = "حساب‌ها:\n" + "\n".join([f"{name}: {balance} تومان" for name, balance in accounts.items()])
        query.message.reply_text(message)

# Message Handler
def message_handler(update: Update, context: CallbackContext):
    state = context.user_data.get("state")
    if state == "ask_item":
        context.user_data["item"] = update.message.text
        update.message.reply_text("مبلغ خرید را وارد کنید:")
        context.user_data["state"] = "ask_amount"
    elif state == "ask_amount":
        try:
            context.user_data["amount"] = int(update.message.text)
            update.message.reply_text("چه کسی خرید کرده؟ (ارش، راضی، کدیور، یدالله، سینا)")
            context.user_data["state"] = "ask_buyer"
        except ValueError:
            update.message.reply_text("لطفاً مبلغ معتبر وارد کنید:")
    elif state == "ask_buyer":
        buyer = update.message.text
        if buyer in accounts:
            context.user_data["buyer"] = buyer
            update.message.reply_text("چه افرادی در این خرید بودند؟ با کاما جدا کنید (ارش، راضی، کدیور، یدالله، سینا):")
            context.user_data["state"] = "ask_participants"
        else:
            update.message.reply_text("نام وارد شده معتبر نیست. دوباره تلاش کنید:")
    elif state == "ask_participants":
        participants = [p.strip() for p in update.message.text.split(",") if p.strip() in accounts]
        if participants:
            item = context.user_data["item"]
            amount = context.user_data["amount"]
            buyer = context.user_data["buyer"]
            orders.append({"item": item, "amount": amount, "buyer": buyer, "participants": participants})
            calculate_shares(item, amount, buyer, participants)
            save_data()
            update.message.reply_text(f"خرید ثبت شد:\nنام خرید: {item}\nمبلغ: {amount}\nخریدار: {buyer}\nاعضا: {', '.join(participants)}")
            context.user_data.clear()
        else:
            update.message.reply_text("لطفاً حداقل یک عضو معتبر وارد کنید:")
    elif state == "ask_delete_order":
        try:
            order_index = int(update.message.text) - 1
            if 0 <= order_index < len(orders):
                deleted_order = orders.pop(order_index)
                save_data()
                update.message.reply_text(f"سفارش با کد {order_index + 1} حذف شد: {deleted_order['item']}")
            else:
                update.message.reply_text("کد سفارش نامعتبر است:")
        except ValueError:
            update.message.reply_text("لطفاً کد معتبر وارد کنید:")
    elif state == "ask_edit_order":
        try:
            order_index = int(update.message.text) - 1
            if 0 <= order_index < len(orders):
                context.user_data["edit_index"] = order_index
                order = orders[order_index]
                update.message.reply_text(f"نام فعلی: {order['item']}\nنام جدید را وارد کنید:")
                context.user_data["state"] = "edit_item"
            else:
                update.message.reply_text("کد سفارش نامعتبر است:")
        except ValueError:
            update.message.reply_text("لطفاً کد معتبر وارد کنید:")
    elif state == "edit_item":
        order_index = context.user_data["edit_index"]
        orders[order_index]["item"] = update.message.text
        update.message.reply_text(f"مبلغ فعلی: {orders[order_index]['amount']}\nمبلغ جدید را وارد کنید:")
        context.user_data["state"] = "edit_amount"
    elif state == "edit_amount":
        try:
            order_index = context.user_data["edit_index"]
            orders[order_index]["amount"] = int(update.message.text)
            update.message.reply_text(f"خریدار فعلی: {orders[order_index]['buyer']}\nخریدار جدید را وارد کنید:")
            context.user_data["state"] = "edit_buyer"
        except ValueError:
            update.message.reply_text("لطفاً مبلغ معتبر وارد کنید:")
    elif state == "edit_buyer":
        order_index = context.user_data["edit_index"]
        buyer = update.message.text
        if buyer in accounts:
            orders[order_index]["buyer"] = buyer
            update.message.reply_text(f"اعضای فعلی: {', '.join(orders[order_index]['participants'])}\nاعضای جدید را وارد کنید با کاما جدا کنید:")
            context.user_data["state"] = "edit_participants"
        else:
            update.message.reply_text("نام وارد شده معتبر نیست. دوباره تلاش کنید:")
    elif state == "edit_participants":
        order_index = context.user_data["edit_index"]
        participants = [p.strip() for p in update.message.text.split(",") if p.strip() in accounts]
        if participants:
            orders[order_index]["participants"] = participants
            save_data()
            update.message.reply_text("ویرایش سفارش با موفقیت انجام شد.")
            context.user_data.clear()
        else:
            update.message.reply_text("لطفاً حداقل یک عضو معتبر وارد کنید:")

# Main Function
def main():
    load_data()
    updater = Updater("7042785861:AAGqpupr0ple996Nqsfn_ZHmiuy5w4RST3E")
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
