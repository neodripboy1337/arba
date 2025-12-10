import logging
import os

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
TOKEN = "7683416658:AAEv9wC3TXJgqtUICdQjzBoDVddOMK3gCKc"   # твой токен (лучше потом ревокнуть и заменить)
ADMIN_CHAT_ID = 4750705274                                  # твой chat_id

# URL твоего сервиса на Render
WEBHOOK_URL = "https://arba-aj3m.onrender.com/webhook"

# Состояния анкеты
NAME, CONTACT, EXPERIENCE, COMMENT = range(4)

# Логи
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# === ХЭНДЛЕРЫ ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first = update.effective_user.first_name or ""
    keyboard = [["Оставить заявку"], ["Что за обучение?"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
    )

    text = (
        f"Привет, {user_first}!\n\n"
        "Я бот для записи на обучение арбитражу трафика.\n"
        "Нажми «Оставить заявку», чтобы заполнить короткую форму."
    )

    await update.message.reply_text(text, reply_markup=reply_markup)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📚 Обучение арбитражу трафика включает:\n\n"
        "• Анализ источников трафика\n"
        "• Настройку рекламных связок\n"
        "• Работа с трекерами и аналитикой\n"
        "• Разборы кейсов\n"
        "• Помощь в запуске первых кампаний\n\n"
        "Чтобы оставить заявку — нажми «Оставить заявку»."
    )
    await update.message.reply_text(text)


async def start_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "1️⃣ Как тебя зовут?\n"
        "(Напиши имя и, если хочешь, фамилию)",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("2️⃣ Оставь контакт для связи (@юзернейм или номер):")
    return CONTACT


async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact"] = update.message.text.strip()
    await update.message.reply_text(
        "3️⃣ Есть ли опыт в арбитраже или рекламе?\n"
        "(если нет — просто напиши «нет опыта»)"
    )
    return EXPERIENCE


async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["experience"] = update.message.text.strip()
    await update.message.reply_text(
        "4️⃣ Добавь комментарий (что ожидаешь от обучения, удобное время созвона).\n"
        "Если нечего добавить — напиши «без комментариев»."
    )
    return COMMENT


async def finish_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["comment"] = update.message.text.strip()

    user = update.effective_user
    ud = context.user_data

    application_text = (
        "📝 *Новая заявка на обучение арбитражу трафика*\n\n"
        f"👤 Имя: {ud['name']}\n"
        f"📞 Контакт: {ud['contact']}\n"
        f"📊 Опыт: {ud['experience']}\n"
        f"💬 Комментарий: {ud['comment']}\n\n"
        f"TG ID: `{user.id}`\n"
        + (f"Username: @{user.username}" if user.username else "")
    )

    # Отправляем заявку админу
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=application_text,
        )
    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")

    # Ответ пользователю
    await update.message.reply_text(
        "Спасибо! 🙌 Твоя заявка отправлена.\n"
        "Куратор свяжется с тобой в ближайшее время!"
    )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Заполнение заявки отменено. Напиши /start, чтобы начать заново.")
    return ConversationHandler.END


def main():
    application = ApplicationBuilder().token(TOKEN).build()

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

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^Что за обучение\\?$"), info))
    application.add_handler(conv_handler)

    # Webhook-режим для Render Web Service
    port = int(os.environ.get("PORT", "8443"))

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="webhook",
        webhook_url=WEBHOOK_URL,
    )


if __name__ == "__main__":
    main()

