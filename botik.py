import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# === НАСТРОЙКИ ===
TOKEN = "7683416658:AAEv9wC3TXJgqtUICdQjzBoDVddOMK3gCKc"
ADMIN_CHAT_ID = 4750705274   # сюда твой chat_id (ЦИФРАМИ, без кавычек)

NAME, CONTACT, EXPERIENCE, COMMENT = range(4)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first = update.effective_user.first_name or ""
    keyboard = [["Оставить заявку"], ["Что за обучение?"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=False
    )

    text = (
        f"Привет, {user_first}!\n\n"
        "Я бот для записи на обучение арбитражу трафика.\n\n"
        "Нажми «Оставить заявку», и я задам несколько вопросов. "
        "После этого отправлю заявку куратору."
    )

    await update.message.reply_text(text, reply_markup=reply_markup)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Кратко об обучении по арбитражу трафика:\n\n"
        "• Разбор источников трафика и офферов\n"
        "• Настройка связок, трекеров, аналитики\n"
        "• Практика с кураторами и разборы кейсов\n"
        "• Помощь с первым запуском\n\n"
        "Если хочешь оставить заявку — нажми «Оставить заявку» 👍"
    )
    await update.message.reply_text(text)


async def start_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Отлично! Давай познакомимся.\n\n"
        "1️⃣ Как тебя зовут?\n"
        "(Напиши имя и, если хочешь, фамилию)",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(
        "2️⃣ Оставь, пожалуйста, контакт для связи:\n"
        "— @юзернейм или номер телефона"
    )
    return CONTACT


async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact"] = update.message.text.strip()
    await update.message.reply_text(
        "3️⃣ Есть ли у тебя опыт в арбитраже/рекламе?\n"
        "Кратко опиши (или напиши «нет опыта»)."
    )
    return EXPERIENCE


async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["experience"] = update.message.text.strip()
    await update.message.reply_text(
        "4️⃣ Напиши, пожалуйста, дополнительный комментарий:\n"
        "что ты ожидаешь от обучения, удобное время созвона и т.п.\n"
        "Если нечего добавить — напиши «без комментариев»."
    )
    return COMMENT


async def finish_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["comment"] = update.message.text.strip()

    user = update.effective_user
    ud = context.user_data

    application_text = (
        "📝 *Новая заявка на обучение арбитражу трафика*\n\n"
        f"👤 Имя: {ud.get('name')}\n"
        f"📞 Контакт: {ud.get('contact')}\n"
        f"📊 Опыт: {ud.get('experience')}\n"
        f"💬 Комментарий: {ud.get('comment')}\n\n"
        f"TG ID: `{user.id}`"
        + (f"\nUsername: @{user.username}" if user.username else "")
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=application_text,
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Не удалось отправить заявку админу: {e}")

    await update.message.reply_text(
        "Спасибо! 🙌 Твоя заявка отправлена.\n"
        "Куратор свяжется с тобой в ближайшее время."
    )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Заполнение заявки отменено. Если захочешь продолжить — напиши /start."
    )
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Оставить заявку$"), start_application)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_experience)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_application)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^Что за обучение\\?$"), info))
    app.add_handler(conv_handler)

    app.run_polling()


if __name__ == "__main__":
    main()
