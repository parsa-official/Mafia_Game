import os
import json
import random
from functools import wraps
from collections import defaultdict
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus
from pathlib import Path

app = Client(
    name="GOD_Mafia",
    api_id=27689690,
    api_hash="893842f3f7e2fe003d8fc73d47045cbf",
    bot_token="7288761682:AAE_XDugs5OKYGV1JA4vFi1qmJdpMAH5I90",
)

commands_list = [
    ("/start", "Start the bot"),
    ("/select_members", "Select members for the game"),
    ("/select_characters", "Select characters for the members"),
    ("/shuffle", "Shuffle characters and show the list to admin"),
    ("/send_characters", "Send the selected characters to members"),
    ("/reset", "Reset the bot (admin only)")
]


# Define the function to display the commands
@app.on_message(filters.command(["start", "commands"]) & filters.group)
def start(client, message):
    help_text = "Available commands:\n\n"
    for command, description in commands_list:
        help_text += f"{command} - {description}\n"
    
    message.reply_text(help_text)

app.run()