"""
HERMES - Multi-AI Life Management + Automation System
Persistent memory across sessions via disk storage
9 specialized agents including AutoBot
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

    facts = memory.get_facts(user_id)
    greeting = "Welcome back, Pierre." if facts else "HERMES ONLINE."

    await update.message.reply_text(
        f"⚡ *{greeting}*\n\n"
        f"Personal assistant. Automation architect. 9 agents ready.\n"
        f"Memory: {'🟢 Active (' + str(len(facts)) + ' facts stored)' if facts else '🔴 No facts yet — I learn as we talk'}\n\n"
        f"Pick an agent:",
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
        facts = memory.get_facts(user_id)
        mem_text = f"\n\n📜 {len(history)} messages | 🧠 {len(facts)} facts remembered"
        await query.edit_message_text(
            f"{agent['emoji']} *{agent['name']} ACTIVATED*\n\n"
            f"_{agent['description']}_"
            f"{mem_text}\n\nWhat do you need?",
            parse_mode="Markdown"
        )

    elif data == "status":
        stats = memory.get_stats(user_id)
        facts = memory.get_facts(user_id)
        active = user_sessions.get(user_id, "none")
        active_name = AGENTS[active]["name"] if active in AGENTS else "None"
        text = (
            f"📊 *HERMES STATUS*\n\n"
            f"🤖 Active: {active_name}\n"
            f"💬 Total Messages: {stats.get('total', 0)}\n"
            f"🧠 Facts Remembered: {len(facts)}\n\n"
            f"*Agent Usage:*\n"
        )
        for key, agent in AGENTS.items():
            text += f"  {agent['emoji']} {agent['name']}: {stats.get(key, 0)}\n"
        if facts:
            text += f"\n*Long-term Memory:*\n"
            for key, data in list(facts.items())[:5]:
                text += f"  • {key}: {data['value'][:50]}\n"
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

    text = update.message.text or ""
    agent_key = user_sessions.get(user_id, "general")

    # Check for remember command
    if text.lower().startswith("remember:"):
        parts = text[9:].strip().split("=", 1)
        if len(parts) == 2:
            memory.save_fact(user_id, parts[0].strip(), parts[1].strip())
            await update.message.reply_text(f"🧠 Saved: *{parts[0].strip()}* = {parts[1].strip()}", parse_mode="Markdown")
        else:
            await update.message.reply_text("Format: `remember: key = value`\nExample: `remember: business partner = Sharmeka Parrish`", parse_mode="Markdown")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    history = memory.get_history(user_id, agent_key, limit=10)
    facts_context = memory.get_facts_as_text(user_id)

    response = await get_agent_response(agent_key, text, history, facts_context=facts_context)

    memory.save_message(user_id, agent_key, "user", text)
    memory.save_message(user_id, agent_key, "assistant", response)

    # Auto-extract facts from conversation
    await auto_remember(user_id, text, response)

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


async def auto_remember(user_id: int, user_text: str, response: str):
    """Auto-save key facts mentioned by the user"""
    text_lower = user_text.lower()
    # Save explicit preferences and facts
    triggers = [
        ("my name is", "name"),
        ("i live in", "location"),
        ("i work on", "current_project"),
        ("my goal is", "goal"),
        ("i'm working on", "current_project"),
        ("my partner", "partner"),
        ("my company", "company"),
    ]
    for trigger, key in triggers:
        if trigger in text_lower:
            idx = text_lower.find(trigger) + len(trigger)
            value = user_text[idx:idx+100].strip().split(".")[0].strip()
            if value and len(value) > 2:
                memory.save_fact(user_id, key, value)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        return

    agent_key = user_sessions.get(user_id, "general")
    caption = update.message.caption or ""

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()

    history = memory.get_history(user_id, agent_key, limit=6)
    facts_context = memory.get_facts_as_text(user_id)

    response = await get_agent_response(
        agent_key, caption, history,
        image_data=bytes(image_bytes),
        image_mime="image/jpeg",
        facts_context=facts_context
    )

    memory.save_message(user_id, agent_key, "user", f"[IMAGE] {caption}")
    memory.save_message(user_id, agent_key, "assistant", response)

    keyboard = [[
        InlineKeyboardButton("🔄 Switch", callback_data="menu"),
        InlineKeyboardButton("📋 Status", callback_data="status")
    ]]

    await update.message.reply_text(
        f"{AGENTS[agent_key]['emoji']} *{AGENTS[agent_key]['name']}*\n\n{response}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all remembered facts"""
    user_id = update.effective_user.id
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        return
    facts = memory.get_facts(user_id)
    if not facts:
        await update.message.reply_text("🧠 No facts stored yet. I learn as we talk, or use:\n`remember: key = value`", parse_mode="Markdown")
        return
    text = "🧠 *Everything I Remember About You:*\n\n"
    for key, data in facts.items():
        text += f"• *{key}*: {data['value']}\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def forget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all long-term facts"""
    user_id = update.effective_user.id
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        return
    memory.clear_facts(user_id)
    await update.message.reply_text("🗑️ Long-term memory cleared.")


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
    await update.message.reply_text(
        f"🗑️ Conversation cleared for {AGENTS[agent_key]['emoji']} {AGENTS[agent_key]['name']}\n"
        f"_(Long-term memory still intact)_",
        parse_mode="Markdown"
    )


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("switch", switch_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("memory", memory_command))
    app.add_handler(CommandHandler("forget", forget_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("HERMES is online ⚡ [Persistent Memory + Automation Expert]")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
