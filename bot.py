import os
import random
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
BOT_TOKEN = "8674676600:AAHndeOE2Ia2ZNUvr-uSboIbfH7yHpySEmQ"
ADMIN_IDS = [8350956257, 8108645611, 7297564960]

PRIVACY_URL = "https://example.com/privacy"
CHANNEL_URL = "https://t.me/lexoravisuals"
DEV_BLOG_URL = "https://t.me/lexora_dev"

# --------------------- ХРАНИЛИЩА ---------------------
awaiting_application = set()
applications = {}  # s_id -> {user_id, username, text}

# --------------------- КОМАНДА /start ---------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("СТАТЬ ПАРТНЁРОМ", callback_data="become_partner")],
        [
            InlineKeyboardButton("Конфиденциальность", url=PRIVACY_URL),
            InlineKeyboardButton("Телеграм канал", url=CHANNEL_URL),
        ],
        [InlineKeyboardButton("Dev Blog", url=DEV_BLOG_URL)],
    ]
    await update.message.reply_text(
        "Привет! Я пиар-менеджер Lexora Visuals.\n"
        "Чтобы стать медиа партнёром и получать эксклюзивный контент, "
        "выбери ниже кнопку СТАТЬ ПАРТНЁРОМ и заполни форму!",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# --------------------- ПОКАЗ ФОРМЫ ---------------------
FORM_TEXT = (
    "Заполни форму и отправь одним сообщением:\n\n"
    "1. Ваш username в Telegram:\n"
    "2. Как вас зовут:\n"
    "3. Ссылка на канал YouTube/TikTok:\n"
    "4. Размер аудитории (подписчики, просмотры):\n"
    "5. Почему именно мы?:\n"
    "6. Вы согласны с политикой конфиденциальности? (Да/Нет):"
)

async def show_form(chat_id, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Отправляет форму и добавляет пользователя в список ожидания."""
    awaiting_application.add(user_id)
    await context.bot.send_message(chat_id=chat_id, text="Заполни форму ниже!")
    await context.bot.send_message(chat_id=chat_id, text=FORM_TEXT)

# --------------------- КНОПКА "СТАТЬ ПАРТНЁРОМ" ---------------------
async def become_partner_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await show_form(query.message.chat_id, context, query.from_user.id)

# --------------------- КОМАНДА /media ---------------------
async def media_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_form(update.message.chat_id, context, update.message.from_user.id)

# --------------------- ПРИЁМ ЗАПОЛНЕННОЙ ФОРМЫ ---------------------
async def handle_application_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.message.from_user
    user_id = user.id

    # Игнорируем если пользователь не в режиме ожидания
    if user_id not in awaiting_application:
        return

    awaiting_application.discard(user_id)

    # Генерируем уникальный S-ID
    while True:
        s_id = str(random.randint(1000, 9999))
        if s_id not in applications:
            break

    form_text = update.message.text

    applications[s_id] = {
        "user_id":  user_id,
        "username": user.username,
        "text":     form_text,
    }

    # ── Сообщение администраторам с ТЕКСТОМ ФОРМЫ ────────────────────────────
    admin_text = (
        f"📋 Новая заявка!\n"
        f"От: @{user.username or '—'} (ID: <code>{user_id}</code>)\n"
        f"S-ID: <b>{s_id}</b> (копировать: <code>{s_id}</code>)\n\n"
        f"<b>Форма:</b>\n"
        f"{form_text}\n\n"
        f"<i>Если кнопки не работают:\n"
        f"/yes {s_id} — одобрить\n"
        f"/no {s_id} — отклонить</i>"
    )

    keyboard = [[
        InlineKeyboardButton("✅ Одобрить!", callback_data=f"appr_{s_id}"),
        InlineKeyboardButton("❌ Отклонить!", callback_data=f"rej_{s_id}"),
    ]]

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            print(f"Ошибка отправки админу {admin_id}: {e}")

    await update.message.reply_text(
        "✅ Ваша заявка отправлена! Ожидайте ответа.\n"
        "Если возникнут вопросы — напишите /tex ваш_вопрос"
    )

# --------------------- КНОПКИ ОДОБРИТЬ / ОТКЛОНИТЬ ---------------------
async def handle_admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    admin_id = query.from_user.id

    if admin_id not in ADMIN_IDS:
        await query.answer("Нет прав", show_alert=True)
        return

    data   = query.data
    action, s_id = data.split("_", 1)
    app    = applications.pop(s_id, None)

    if not app:
        await query.answer("Заявка уже обработана или не найдена.", show_alert=True)
        return

    user_id = app["user_id"]

    if action == "appr":
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 Твоя заявка на сотрудничество принята! Скоро с тобой свяжется администратор.",
            )
        except Exception as e:
            print(f"Ошибка уведомления {user_id}: {e}")
        await query.edit_message_text(
            query.message.text + "\n\n✅ <b>ОДОБРЕНО</b>",
            parse_mode="HTML",
        )
    else:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "😔 К сожалению, ваша заявка была отклонена.\n"
                    "Попробуйте позже или свяжитесь с поддержкой: /tex ваш_вопрос"
                ),
            )
        except Exception as e:
            print(f"Ошибка уведомления {user_id}: {e}")
        await query.edit_message_text(
            query.message.text + "\n\n❌ <b>ОТКЛОНЕНО</b>",
            parse_mode="HTML",
        )

    await query.answer()

# --------------------- /yes и /no (ручное управление) ---------------------
async def yes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Только для администраторов.")
        return
    if not context.args:
        await update.message.reply_text("❗ Использование: /yes <S-ID>")
        return
    s_id = context.args[0]
    app  = applications.pop(s_id, None)
    if not app:
        await update.message.reply_text("❌ Заявка не найдена.")
        return
    try:
        await context.bot.send_message(
            chat_id=app["user_id"],
            text="🎉 Твоя заявка на сотрудничество принята! Скоро с тобой свяжется администратор.",
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка уведомления: {e}")
        return
    await update.message.reply_text(f"✅ Заявка {s_id} одобрена.")

async def no_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Только для администраторов.")
        return
    if not context.args:
        await update.message.reply_text("❗ Использование: /no <S-ID>")
        return
    s_id = context.args[0]
    app  = applications.pop(s_id, None)
    if not app:
        await update.message.reply_text("❌ Заявка не найдена.")
        return
    try:
        await context.bot.send_message(
            chat_id=app["user_id"],
            text=(
                "😔 К сожалению, ваша заявка была отклонена.\n"
                "Попробуйте позже или свяжитесь с поддержкой: /tex ваш_вопрос"
            ),
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка уведомления: {e}")
        return
    await update.message.reply_text(f"❌ Заявка {s_id} отклонена.")

# --------------------- /tex (техподдержка) ---------------------
async def tex_command_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user         = update.message.from_user
    message_text = update.message.text[4:].strip()
    if not message_text:
        await update.message.reply_text("❗ Напишите вопрос после /tex")
        return
    header = f"📩 Сообщение от @{user.username or '—'} (ID: {user.id}):\n\n"
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=header + message_text)
        except Exception as e:
            print(f"Ошибка /tex админу {admin_id}: {e}")
    await update.message.reply_text("✅ Сообщение отправлено администраторам.")

async def tex_media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.message.from_user
    msg     = update.message
    caption = msg.caption or ""
    body    = caption[4:].strip() if len(caption) > 4 else ""
    header  = f"📩 Медиа от @{user.username or '—'} (ID: {user.id})"
    if body:
        header += f":\n{body}"
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
            print(f"Ошибка медиа /tex админу {admin_id}: {e}")
    await update.message.reply_text("✅ Медиа отправлено администраторам.")

# --------------------- ЗАПУСК ---------------------
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start",  start))
    application.add_handler(CommandHandler("media",  media_command))
    application.add_handler(CommandHandler("yes",    yes_command))
    application.add_handler(CommandHandler("no",     no_command))
    application.add_handler(CommandHandler("tex",    tex_command_text))

    application.add_handler(CallbackQueryHandler(become_partner_callback,  pattern="^become_partner$"))
    application.add_handler(CallbackQueryHandler(handle_admin_decision,    pattern="^(appr_|rej_)"))

    # Приём текста формы — только от пользователей в awaiting_application
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_application_text,
    ))

    # Медиа с подписью /tex
    application.add_handler(MessageHandler(
        filters.CAPTION & filters.Regex(r"^/tex"),
        tex_media_handler,
    ))

    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
