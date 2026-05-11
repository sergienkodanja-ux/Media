import os
import random
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# --------------------- НАСТРОЙКИ ---------------------
BOT_TOKEN = os.environ.get("8674676600:AAHndeOE2Ia2ZNUvr-uSboIbfH7yHpySEmQ", "8674676600:AAHndeOE2Ia2ZNUvr-uSboIbfH7yHpySEmQ")
ADMIN_IDS = [8350956257, 8108645611, 7297564960]  # Замените на реальные ID

# Ссылки для кнопок
PRIVACY_URL = "https://example.com/privacy"
CHANNEL_URL = "https://t.me/lexoravisuals"
DEV_BLOG_URL = "https://t.me/lexora_dev"

# --------------------- ХРАНИЛИЩА ---------------------
awaiting_application = set()
applications = {}  # s_id -> {user_id, username, text}

# --------------------- ФУНКЦИИ ---------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие с кнопками."""
    keyboard = [
        [InlineKeyboardButton("СТАТЬ ПАРТНЁРОМ", callback_data="become_partner")],
        [
            InlineKeyboardButton("Конфиденциальность", url=PRIVACY_URL),
            InlineKeyboardButton("Телеграм канал", url=CHANNEL_URL),
        ],
        [InlineKeyboardButton("Dev Blog", url=DEV_BLOG_URL)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Я пиар-менеджер Lexora Visuals.\n"
        "Чтобы стать медиа партнёром и получать эксклюзивный контент, "
        "выбери ниже кнопку СТАТЬ ПАРТНЁРОМ и заполни форму!",
        reply_markup=reply_markup,
    )

async def start_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Переводит пользователя в режим ожидания заявки.
    Вызывается при нажатии кнопки или по команде /media.
    """
    user_id = update.effective_user.id
    # Отправляем два сообщения-инструкции
    await update.message.reply_text("Заполни форму ниже!")
    await update.message.reply_text(
        "1. Ваш username в Telegram: \n"
        "2. Как вас зовут: \n"
        "3. Ссылка на канал YouTube/TikTok: (ссылка) \n"
        "4. Размер аудитории (50 подписчиков, 800 просмотров): \n"
        "5. Почему именно мы?: \n"
        "6. Вы согласны с политикой конфиденциальности?: "
    )
    awaiting_application.add(user_id)

# Кнопка "СТАТЬ ПАРТНЁРОМ"
async def become_partner_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Используем ту же логику
    await query.message.reply_text("Заполни форму ниже!")
    await query.message.reply_text(
        "1. Ваш username в Telegram: @nezexy\n"
        "2. Как вас зовут: \n"
        "3. Ссылка на канал YouTube/TikTok: (ссылка)\n"
        "4. Размер аудитории (50 подписчиков, 800 просмотров): \n"
        "5. Почему именно мы?: \n"
        "6. вы согласны с политикой конфиденциальности?: "
    )
    awaiting_application.add(query.from_user.id)

# Команда /media (дублёр кнопки)
async def media_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_application(update, context)

async def handle_application_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Принимает текстовое сообщение от пользователя, который находится в режиме ожидания.
    """
    user = update.message.from_user
    user_id = user.id

    if user_id not in awaiting_application:
        return  # Не в режиме ожидания — игнорируем

    awaiting_application.discard(user_id)

    # Генерируем уникальный 4-значный S-ID
    while True:
        s_id = str(random.randint(1000, 9999))
        if s_id not in applications:
            break

    applications[s_id] = {
        "user_id": user_id,
        "username": user.username,
        "text": update.message.text,
    }

    # Экранируем текст, чтобы символы вроде < или > не сломали HTML-разметку бота
    safe_user_text = html.escape(update.message.text)

    # Сообщение администраторам
    admin_text = (
        f"Пользователь @{user.username or '—'} (ID: {user_id}) подал заявку.\n"
        f"Его форма ниже:\n\n"
        f"<blockquote>{safe_user_text}</blockquote>\n\n"
        f"<b>S-ID: {s_id}</b> (нажмите, чтобы скопировать: <code>{s_id}</code>)\n\n"
        f"<i>Если кнопки не работают, пропишите вручную:\n"
        f"/Yes {s_id}  — для одобрения\n"
        f"/No {s_id}   — для отклонения</i>"
    )
    keyboard = [
        [
            InlineKeyboardButton("✅ Одобрить!", callback_data=f"appr_{s_id}"),
            InlineKeyboardButton("❌ Отклонить!", callback_data=f"rej_{s_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
        except Exception as e:
            print(f"Ошибка отправки админу {admin_id}: {e}")

    await update.message.reply_text("✅ Ваша заявка отправлена! Ожидайте ответа.")

async def handle_admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок 'Одобрить' / 'Отклонить'."""
    query = update.callback_query
    admin_id = query.from_user.id
    if admin_id not in ADMIN_IDS:
        await query.answer("Нет прав", show_alert=True)
        return

    data = query.data
    if not (data.startswith("appr_") or data.startswith("rej_")):
        return

    action, s_id = data.split("_", 1)
    app = applications.pop(s_id, None)
    if not app:
        await query.answer("Заявка уже обработана или не найдена.", show_alert=True)
        return

    user_id = app["user_id"]
    if action == "appr":
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 Твоя заявка на сотрудничество принята! Скоро с тобой свяжется администратор бота!",
            )
        except Exception as e:
            print(f"Ошибка одобрения {user_id}: {e}")
        await query.edit_message_text(
            query.message.text + "\n\n✅ <b>ОДОБРЕНО</b>",
            parse_mode="HTML",
        )
    else:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="😔 Простите, но ваша заявка была отклонена. Попробуйте в следующий раз. Если это ошибка, свяжитесь с техподдержкой: /tex ваш вопрос/сообщение",
            )
        except Exception as e:
            print(f"Ошибка отказа {user_id}: {e}")
        await query.edit_message_text(
            query.message.text + "\n\n❌ <b>ОТКЛОНЕНО</b>",
            parse_mode="HTML",
        )
    await query.answer()

async def yes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ручное одобрение командой /Yes S-ID (для админов)."""
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Команда только для администраторов.")
        return
    if not context.args:
        await update.message.reply_text("❗ Использование: /Yes <S-ID>")
        return
    s_id = context.args[0]
    app = applications.pop(s_id, None)
    if not app:
        await update.message.reply_text("❌ Заявка с таким S-ID не найдена.")
        return
    try:
        await context.bot.send_message(
            chat_id=app["user_id"],
            text="🎉 Твоя заявка на сотрудничество принята! Скоро с тобой свяжется администратор бота!",
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка уведомления: {e}")
        return
    await update.message.reply_text(f"✅ Заявка {s_id} одобрена.")

async def no_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ручное отклонение командой /No S-ID (для админов)."""
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Команда только для администраторов.")
        return
    if not context.args:
        await update.message.reply_text("❗ Использование: /No <S-ID>")
        return
    s_id = context.args[0]
    app = applications.pop(s_id, None)
    if not app:
        await update.message.reply_text("❌ Заявка с таким S-ID не найдена.")
        return
    try:
        await context.bot.send_message(
            chat_id=app["user_id"],
            text="😔 Простите, но ваша заявка была отклонена. Попробуйте в следующий раз. Если это ошибка, свяжитесь с техподдержкой: /tex ваш вопрос/сообщение",
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка уведомления: {e}")
        return
    await update.message.reply_text(f"❌ Заявка {s_id} отклонена.")

async def tex_command_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пересылает текстовое сообщение администраторам."""
    user = update.message.from_user
    message_text = update.message.text[4:].strip()
    if not message_text:
        await update.message.reply_text("❗ Напишите вопрос или сообщение после /tex")
        return
    header = f"Сообщение от @{user.username or '—'} (ID: {user.id}):\n\n"
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=header + message_text)
        except Exception as e:
            print(f"Ошибка отправки /tex админу {admin_id}: {e}")
    await update.message.reply_text("✅ Ваше сообщение отправлено администраторам.")

async def tex_media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пересылает медиа (с подписью /tex) администраторам."""
    user = update.message.from_user
    msg = update.message
    caption = msg.caption or ""
    message_text = caption[4:].strip() if len(caption) > 4 else ""
    header = f"Сообщение от @{user.username or '—'} (ID: {user.id})"
    if message_text:
        header += f":\n{message_text}"

    for admin_id in ADMIN_IDS:
        try:
            if msg.photo:
                await context.bot.send_photo(admin_id, msg.photo[-1].file_id, caption=header)
            elif msg.video:
                await context.bot.send_video(admin_id, msg.video.file_id, caption=header)
            elif msg.document:
                await context.bot.send_document(admin_id, msg.document.file_id, caption=header)
            else:
                await msg.forward(admin_id)
        except Exception as e:
            print(f"Ошибка пересылки медиа админу {admin_id}: {e}")
    await update.message.reply_text("✅ Ваше медиасообщение отправлено администраторам.")

# --------------------- ЗАПУСК ---------------------
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("media", media_command))  # команда /media
    application.add_handler(CallbackQueryHandler(become_partner_callback, pattern="^become_partner$"))
    application.add_handler(CallbackQueryHandler(handle_admin_decision, pattern="^(appr_|rej_)"))

    # Текстовое сообщение для заполнения формы (только когда пользователь в awaiting_application)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_application_text
    ))

    application.add_handler(CommandHandler("yes", yes_command))
    application.add_handler(CommandHandler("no", no_command))
    application.add_handler(CommandHandler("tex", tex_command_text))
    application.add_handler(MessageHandler(
        filters.CAPTION & filters.Regex(r'^/tex'), tex_media_handler
    ))

    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
