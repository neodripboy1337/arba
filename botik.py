import logging
import os
from datetime import datetime, timedelta, timezone

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
TOKEN = "8456401419:AAGiLcNR3c9lrTxo6MsqIf0P1F0kHC3URtU"  # при желании потом пересоздай
ADMIN_CHAT_ID = -1003389712669  # группа для отстука заявок
OWNER_ID = 7843476011           # твой личный ID для /broadcast

WEBHOOK_URL = "https://arba-9ajo.onrender.com/webhook"

# Состояния анкеты
CAPTCHA, NAME, EXPERIENCE, COMMENT = range(4)

# Антиспам: сколько ждать между заявками
MIN_APPLICATION_INTERVAL = timedelta(hours=1)

# Логи
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# === ХЭНДЛЕРЫ ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие и стартовое меню."""
    keyboard = [["Оставить заявку"], ["Что за обучение?"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    text = (
        "Привет! 👋\n\n"
        "Это помощник программы **PRO Маркетинг: Практика Google Ads**.\n"
        "Здесь ты можешь оставить заявку на обучение и получить консультацию от специалиста.\n\n"
        "Если хочешь разобраться в запуске кампаний с нуля и научиться работать с рекламой структурно — "
        "оставь короткую заявку.\n\n"
        "Нажми «Оставить заявку», чтобы начать."
    )

    await update.message.reply_text(
        text, reply_markup=reply_markup, disable_web_page_preview=True
    )

    # добавляем чат в подписчики для рассылок
    subs = context.application.bot_data.setdefault("subscribers", set())
    subs.add(update.effective_chat.id)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Рассказывает о программе."""
    text = (
        "О программе **PRO Маркетинг: Практика Google Ads** 📘\n\n"
        "Мы разбираем путь “с нуля”, включая:\n"
        "• подготовку рекламных аккаунтов и рабочей среды\n"
        "• настройку поисковых кампаний\n"
        "• работу с КМС и видеорекламой\n"
        "• аналитику и оптимизацию\n"
        "• разбор частых ошибок начинающих специалистов\n\n"
        "Программа подходит тем, кто хочет уверенно работать с Google Ads для своих проектов "
        "или развиваться как специалист.\n\n"
        "Если хочешь понять, подходит ли формат под твои задачи — оставь заявку."
    )

    await update.message.reply_text(text)


async def start_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт анкеты: антиспам + капча."""
    user_id = update.effective_user.id
    now = datetime.now(timezone.utc)
    last_apps = context.application.bot_data.get("last_applications", {})

    last_time = last_apps.get(user_id)
    if last_time and now - last_time < MIN_APPLICATION_INTERVAL:
        remaining = MIN_APPLICATION_INTERVAL - (now - last_time)
        minutes = int(remaining.total_seconds() // 60) + 1

        await update.message.reply_text(
            f"Заявка уже была отправлена недавно 🙌\n"
            f"Попробуй ещё раз через ~{minutes} мин ⏳"
        )
        return ConversationHandler.END

    # Капча
    keyboard = [["7", "3", "9"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    context.user_data["captcha_answer"] = "7"

    await update.message.reply_text(
        "Короткая проверка 🙂\n\nСколько будет 3 + 4?",
        reply_markup=markup,
    )

    return CAPTCHA


async def check_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка ответа на капчу."""
    correct = context.user_data.get("captcha_answer")
    answer = update.message.text.strip()

    if answer != correct:
        await update.message.reply_text(
            "Похоже, ответ неверный 🤔\n"
            "Если это была ошибка — попробуй отправить заявку позже."
        )
        context.user_data.clear()
        return ConversationHandler.END

    await update.message.reply_text(
        "Отлично, продолжаем ✅\n\n"
        "1️⃣ Напиши, пожалуйста, как тебя зовут.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 1 — имя."""
    context.user_data["name"] = update.message.text.strip()

    await update.message.reply_text(
        "2️⃣ Расскажи немного о своём опыте в рекламе или маркетинге.\n\n"
        "Например:\n"
        "• новичок\n"
        "• запускал рекламу в других системах\n"
        "• есть опыт работы в маркетинге\n"
        "• немного знаком с рекламными инструментами Google\n\n"
        "Пиши так, как есть."
    )
    return EXPERIENCE


async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 2 — опыт."""
    context.user_data["experience"] = update.message.text.strip()

    await update.message.reply_text(
        "3️⃣ И последний шаг.\n\n"
        "Какая у тебя цель?\n"
        "• хочу научиться готовить рабочие аккаунты для дальнейшей рекламы\n"
        "• хочу разобраться в запуске кампаний с нуля\n"
        "• хочу уверенно работать в Google Ads\n"
        "• хочу понимать аналитику и оптимизацию\n\n"
        "Пиши своими словами."
    )
    return COMMENT


async def finish_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Финальный шаг — отправка заявки админу."""
    context.user_data["comment"] = update.message.text.strip()

    user = update.effective_user
    chat = update.effective_chat
    ud = context.user_data

    text = (
        "📩 Новая заявка | PRO Маркетинг: Практика Google Ads\n\n"
        f"Имя: {ud['name']}\n"
        f"Опыт: {ud['experience']}\n"
        f"Цель: {ud['comment']}\n\n"
        f"TG ID: {user.id}\n"
    )
    if user.username:
        text += f"Username: @{user.username}\n"
    text += f"Chat ID: {chat.id}"

    try:
        await context.bot.send_message(ADMIN_CHAT_ID, text)
    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")

    # обновляем время последней заявки
    now = datetime.now(timezone.utc)
    last_apps = context.application.bot_data.setdefault("last_applications", {})
    last_apps[user.id] = now

    await update.message.reply_text(
        "Спасибо! Заявка отправлена ✅\n\n"
        "Специалист свяжется с тобой в ближайшее время, чтобы уточнить цели "
        "и рассказать о формате обучения.\n\n"
        "Если появятся вопросы — можешь писать сюда."
    )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Анкета остановлена. Если захочешь вернуться — напиши /start.")
    return ConversationHandler.END


# === РАССЫЛКА ===

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Эта команда доступна только владельцу.")
        return

    subs = context.application.bot_data.get("subscribers", set())
    if not subs:
        await update.message.reply_text("Пока нет подписчиков.")
        return

    if not context.args:
        await update.message.reply_text(
            "Напиши текст рассылки после команды.\n\n"
            "Пример:\n"
            "/broadcast Обновление по программе PRO Маркетинг."
        )
        return

    text = " ".join(context.args)
    delivered = 0

    for chat_id in list(subs):
        try:
            await context.bot.send_message(chat_id, text)
            delivered += 1
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение в {chat_id}: {e}")

    await update.message.reply_text(f"Рассылка отправлена в {delivered} чатов.")


# === ЗАПУСК — WEBHOOK ДЛЯ RENDER ===

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Оставить заявку$"), start_application)],
        states={
            CAPTCHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_captcha)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_experience)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_application)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^Что за обучение\\?$"), info))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(conv)

    port = int(os.environ.get("PORT", "8433"))
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="webhook",
        webhook_url=WEBHOOK_URL,
    )


if __name__ == "__main__":
    main()


