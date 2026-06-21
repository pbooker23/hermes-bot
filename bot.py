"""
HERMES - Multi-AI Life Management System
Compatible with python-telegram-bot 20.x
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from agents import AGENTS, get_agent_response
from memory import Memory

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "0"))

memory = Memory()
user_sessions = {}


def build_agent_menu():
    agents_list = list(AGENTS.items())
    keyboard = []
    for i in range(0, len(agents_list), 2):
        row = []
        for key, agent in agents_list[i:i+2]:
            row.append(InlineKeyboardButton(
                f"{agent['emoji']} {agent['name']}",
                callback_data=f"agent:{key}"
            ))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("📋 Status", callback_data="status")])
    return keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        return
    await update.message.reply_text(
        "⚡ *HERMES ONLINE*\n\nYour personal AI command center.\nPick an agent:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(build_agent_menu())
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        return

    data = query.data

    if data.startswith("agent:"):
        agent_key = data.split(":")[1]
        user_sessions[user_id] = agent_key
        agent = AGENTS[agent_key]
        history = memory.get_history(user_id, agent_key, limit=5)
        ctx = f"\n\n📜 {len(history)} messages in memory" if history else ""
        await query.edit_message_text(
            f"{agent['emoji']} *{agent['name']} ACTIVATED*\n\n"
            f"_{agent['description']}_"
            f"{ctx}\n\nWhat do you need?",
            parse_mode="Markdown"
        )

    elif data == "status":
        stats = memory.get_stats(user_id)
        active = user_sessions.get(user_id, "none")
        active_name = AGENTS[active]["name"] if active in AGENTS else "None"
        text = f"📊 *HERMES STATUS*\n\n🤖 Active: {active_name}\n💬 Total: {stats.get('total', 0)}\n\n*Usage:*\n"
        for key, agent in AGENTS.items():
            text += f"  {agent['emoji']} {agent['name']}: {stats.get(key, 0)}\n"
        keyboard = [[InlineKeyboardButton("◀️ Menu", callback_data="menu")]]
        await query.edit_message_text(text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "menu":
        await query.edit_message_text(
            "⚡ *HERMES* — Choose your agent:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(build_agent_menu())
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        return

    text = update.message.text
    agent_key = user_sessions.get(user_id, "general")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    history = memory.get_history(user_id, agent_key, limit=10)
    response = await get_agent_response(agent_key, text, history)

    memory.save_message(user_id, agent_key, "user", text)
    memory.save_message(user_id, agent_key, "assistant", response)

    agent = AGENTS[agent_key]
    keyboard = [[
        InlineKeyboardButton("🔄 Switch", callback_data="menu"),
        InlineKeyboardButton("📋 Status", callback_data="status")
    ]]

    await update.message.reply_text(
        f"{agent['emoji']} *{agent['name']}*\n\n{response}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def switch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        return
    await update.message.reply_text("⚡ Switch Agent:",
        reply_markup=InlineKeyboardMarkup(build_agent_menu()))


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        return
    agent_key = user_sessions.get(user_id, "general")
    memory.clear_history(user_id, agent_key)
    await update.message.reply_text(f"🗑️ Memory cleared for {AGENTS[agent_key]['emoji']} {AGENTS[agent_key]['name']}")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("switch", switch_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("HERMES is online ⚡")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
