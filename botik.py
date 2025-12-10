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
TOKEN = "7683416658:AAEv9wC3TXJgqtUICdQjzBoDVddOMK3gCKc"  # при желании потом пересоздай
ADMIN_CHAT_ID = -1003389712669  # группа для отстука заявок
OWNER_ID = 7843476011           # твой личный аккаунт, кто может делать /broadcast

# URL твоего сервиса на Render
WEBHOOK_URL = "https://arba-aj3m.onrender.com/webhook"

# Состояния анкеты
CAPTCHA, NAME, EXPERIENCE, COMMENT = range(4)

# Ограничение: как часто один пользователь может отправлять заявку
MIN_APPLICATION_INTERVAL = timedelta(hours=1)

# Логи
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# === ХЭНДЛЕРЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие и главное меню."""
    user_first = update.effective_user.first_name or "друг"
    keyboard = [["Оставить заявку"], ["Что за обучение?"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
    )

    text = (
        f"Привет, {user_first} 👋\n\n"
        "Ты в боте программы **PRO Залив: Старт в Google Ads**.\n\n"
        "Если хочешь спокойно и системно зайти в белый арбитраж через Google Ads — "
        "оставь короткую заявку, и куратор свяжется с тобой.\n\n"
        "Нажми «Оставить заявку», чтобы начать."
    )

    await update.message.reply_text(text, reply_markup=reply_markup, disable_web_page_preview=True)

    # сохраняем чат как подписчика для будущих рассылок
    subs = context.application.bot_data.setdefault("subscribers", set())
    subs.add(update.effective_chat.id)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Краткое описание обучения."""
    text = (
        "🔥 PRO Залив: Старт в Google Ads\n\n"
        "Что даёт программа:\n"
        "• Понимание, как работает арбитраж в белую через Google Ads\n"
        "• Настройка поисковых кампаний, КМС и YouTube под офферы\n"
        "• Структура аккаунта, кампаний и групп объявлений без хаоса\n"
        "• Как считать математику и анализировать связки\n"
        "• Разбор типичных ошибок новичков и рабочих кейсов\n\n"
        "Формат: разборы, практика, сопровождение куратора.\n"
        "Если хочешь залететь в тему — жми «Оставить заявку» и заполни форму 🙂"
    )
    await update.message.reply_text(text)


async def start_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт анкеты: антиспам + капча."""
    user_id = update.effective_user.id
    now = datetime.now(timezone.utc)
    last_applications = context.application.bot_data.get("last_applications", {})

    last_time = last_applications.get(user_id)
    if last_time and now - last_time < MIN_APPLICATION_INTERVAL:
        remaining = MIN_APPLICATION_INTERVAL - (now - last_time)
        minutes = int(remaining.total_seconds() // 60) + 1
        await update.message.reply_text(
            "Ты уже оставлял заявку совсем недавно 🙌\n"
            f"Давай без спама — попробуй ещё раз через ~{minutes} мин ⏳"
        )
        return ConversationHandler.END

    # анти-клоун капча
    keyboard = [["7", "3", "9"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    context.user_data["captcha_answer"] = "7"

    await update.message.reply_text(
        "Быстро проверим, что ты человек, а не бот 🙂\n\n"
        "Сколько будет 3 + 4?",
        reply_markup=reply_markup,
    )
    return CAPTCHA


async def check_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка ответа на капчу."""
    correct = context.user_data.get("captcha_answer", "7")
    answer = (update.message.text or "").strip()

    if answer != correct:
        await update.message.reply_text(
            "Ответ не подходит 🤔\n"
            "Если ты реально человек, просто нажми «Оставить заявку» ещё раз чуть позже."
        )
        context.user_data.clear()
        return ConversationHandler.END

    await update.message.reply_text(
        "Отлично, поехали ✅\n\n"
        "1️⃣ Напиши, как тебя зовут.\n"
        "Можно просто имя или имя + фамилия.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 1 — имя."""
    context.user_data["name"] = (update.message.text or "").strip()
    await update.message.reply_text(
        "2️⃣ Расскажи коротко про свой опыт в трафике/рекламе:\n\n"
        "• Полный ноль\n"
        "• Пробовал запускать рекламу (FB, Google, другие)\n"
        "• Работаю в маркетинге / арбитраже\n\n"
        "Пиши как есть, без приукрашивания 🙂"
    )
    return EXPERIENCE


async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 2 — опыт."""
    context.user_data["experience"] = (update.message.text or "").strip()
    await update.message.reply_text(
        "3️⃣ Чего хочешь от «PRO Залив: Старт в Google Ads»?\n\n"
        "Например:\n"
        "• Хочу с нуля понять Google Ads и запустить первые связки\n"
        "• Есть бюджет, хочу системный подход и разбор от куратора\n"
        "• Хочу уйти из серого арбитража в белый\n\n"
        "Пиши своими словами."
    )
    return COMMENT


async def finish_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Финальный шаг — сохраняем заявку и шлём её в админ-чат (группу)."""
    context.user_data["comment"] = (update.message.text or "").strip()

    user = update.effective_user
    chat = update.effective_chat
    ud = context.user_data

    application_text = (
        "📝 Заявка | PRO Залив: Старт в Google Ads\n\n"
        f"Имя: {ud.get('name')}\n"
        f"Опыт: {ud.get('experience')}\n"
        f"Запрос/цель: {ud.get('comment')}\n\n"
        f"TG ID: {user.id}\n"
    )
    if user.username:
        application_text += f"Username: @{user.username}\n"
    application_text += f"Chat ID: {chat.id}"

    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=application_text,
        )
    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")

    # обновляем время последней заявки для антиспама
    now = datetime.now(timezone.utc)
    last_applications = context.application.bot_data.setdefault("last_applications", {})
    last_applications[user.id] = now

    await update.message.reply_text(
        "Готово, заявка отправлена ✅\n\n"
        "Куратор из PRO Залив свяжется с тобой в ближайшее время.\n"
        "Если захочешь что-то добавить — просто напиши сюда ещё одно сообщение."
    )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена анкеты."""
    context.user_data.clear()
    await update.message.reply_text(
        "Заполнение заявки остановлено.\n"
        "Если захочешь вернуться — напиши /start."
    )
    return ConversationHandler.END


# === РАССЫЛКА ДЛЯ АДМИНА ===

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /broadcast для рассылки по всем, кто писал боту."""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Эта команда доступна только владельцу бота.")
        return

    subs = context.application.bot_data.get("subscribers", set())
    if not subs:
        await update.message.reply_text("Пока нет ни одного подписчика для рассылки.")
        return

    if not context.args:
        await update.message.reply_text(
            "Напиши текст рассылки после команды.\n\n"
            "Пример:\n"
            "/broadcast Привет! Это апдейт по PRO Залив: Старт в Google Ads."
        )
        return

    text = " ".join(context.args)
    sent = 0

    for chat_id in list(subs):
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            sent += 1
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение в чат {chat_id}: {e}")

    await update.message.reply_text(f"Рассылка отправлена в {sent} чатов.")


# === ЗАПУСК ПРИЛОЖЕНИЯ ===

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Оставить заявку$"), start_application)
        ],
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
    application.add_handler(conv_handler)

    port = int(os.environ.get("PORT", "8443"))

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="webhook",
        webhook_url=WEBHOOK_URL,
    )


if __name__ == "__main__":
    main()
