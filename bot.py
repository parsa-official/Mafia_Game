import os
import json
import random
from functools import wraps
from collections import defaultdict
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus

app = Client(name="GOD_Mafia",
             api_id=27689690,
             api_hash="893842f3f7e2fe003d8fc73d47045cbf",
             bot_token="7288761682:AAE_XDugs5OKYGV1JA4vFi1qmJdpMAH5I90")

script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to the JSON file
json_file_path = os.path.join(script_dir, "db/characters2.json")

# Load characters from JSON file
with open(json_file_path, "r", encoding="utf-8") as file:
    data = json.load(file)
    characters = data["mafia"] + data["city"] + data["unknown"]

selected_members = defaultdict(dict)
user_characters = defaultdict(dict)
user_character_selections = defaultdict(dict)

def is_admin(client, chat_id, user_id):
    member = client.get_chat_member(chat_id, user_id)
    return member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]

def admin_only(func):
    @wraps(func)
    def wrapper(client, message, *args, **kwargs):
        chat_id = message.chat.id
        user_id = message.from_user.id
        if is_admin(client, chat_id, user_id):
            return func(client, message, *args, **kwargs)
        else:
            message.reply_text("You must be an admin to use this command.")
    return wrapper

commands_list = [
    ("/start", "Start the bot"),
    ("/select_members", "Select members for the game"),
    ("/select_characters", "Select characters for the members"),
    ("/shuffle", "Shuffle characters adn Show the list to admin"),
    ("/send_characters", "Send the selected characters to members"),
    # Add more commands as needed
]

# Define the function to display the commands
@app.on_message(filters.command(["start", "commands"]) & filters.group)
@admin_only
def start(client, message):
    help_text = "Available commands:\n\n"
    for command, description in commands_list:
        help_text += f"{command} - {description}\n"
    
    message.reply_text(help_text)


# @app.on_message(filters.command("start"))
# def start(client, message):
#     message.reply_text("Hello! Add me to a group and use /select to select members.")

@app.on_message(filters.command("select_members") & filters.group)
@admin_only
def select_members(client, message):
    chat_id = message.chat.id
    members = client.get_chat_members(chat_id)
    user_id = message.from_user.id

    # Sort members alphabetically by full name (first name + last name)
    sorted_members = sorted(
        [m for m in members if not m.user.is_bot],
        key=lambda m: (f"{m.user.first_name} {m.user.last_name or ''}").lower()
    )
    buttons = [
        [
            InlineKeyboardButton(
                f"{'✅ ' if m.user.id in selected_members.get(user_id, []) else ''}{m.user.first_name} {m.user.last_name or ''} ({m.user.username or 'N/A'})",
                callback_data=f"select_member_{m.user.id}"
            )
        ]
        for m in sorted_members
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    message.reply_text("Select members:", reply_markup=reply_markup)

    
@app.on_callback_query(filters.regex(r"^select_member_"))
def on_select_member(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    selected_user_id = int(callback_query.data.split("_")[2])
    user = client.get_users(selected_user_id)

    # Initialize the selected_members dictionary if it doesn't exist for this chat
    if chat_id not in selected_members:
        selected_members[chat_id] = {}

    # Initialize the user's selected members list if it doesn't exist for this chat
    if user_id not in selected_members[chat_id]:
        selected_members[chat_id][user_id] = []

    # Toggle selection: add if not selected, remove if already selected
    if selected_user_id in selected_members[chat_id][user_id]:
        selected_members[chat_id][user_id].remove(selected_user_id)
        callback_query.answer(f"Deselected: {user.first_name} {user.last_name or ''} ({user.username or 'N/A'})")
    else:
        selected_members[chat_id][user_id].append(selected_user_id)
        callback_query.answer(f"Selected: {user.first_name} {user.last_name or ''} ({user.username or 'N/A'})")

    # Update the message with the current selection status
    update_member_selection_message(client, callback_query.message, user_id, chat_id)

    save_selected_members(client, selected_members, chat_id, user_id)

def update_member_selection_message(client, message, user_id, chat_id):
    chat_id = message.chat.id
    members = client.get_chat_members(chat_id)

    # Sort members alphabetically by full name (first name + last name)
    sorted_members = sorted(
        [m for m in members if not m.user.is_bot],
        key=lambda m: (f"{m.user.first_name} {m.user.last_name or ''}").lower()
    )

    buttons = [
        [
            InlineKeyboardButton(
                f"{'✅ ' if m.user.id in selected_members.get(chat_id, {}).get(user_id, []) else ''}"
                f"{m.user.first_name} {m.user.last_name or ''} ({m.user.username or 'N/A'})",
                callback_data=f"select_member_{m.user.id}"
            )
        ]
        for m in sorted_members
    ]

    selected_count = len(selected_members.get(chat_id, {}).get(user_id, []))
    reply_markup = InlineKeyboardMarkup(buttons)
    
    # Edit the original message with updated selection status
    message.edit_text(f"Select members >> \n👥 selected: {selected_count}", reply_markup=reply_markup)

def save_selected_members(client, selected_members, chat_id, user_id):
    user_info_data = []

    for user_id in selected_members[chat_id][user_id]:
        user = client.get_users(user_id)
        user_info = f"{user.first_name} {user.last_name or ''} ({user.username or 'N/A'})"
        user_info_data.append(user_info)

    with open('user_info.json', 'w') as f:
        json.dump(user_info_data, f)


####################################################################################################
@app.on_message(filters.command("select_characters") & filters.group)
@admin_only
def select_characters(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if user_id in selected_members[chat_id] and selected_members[chat_id][user_id]:
        selected_members_count = len(selected_members[chat_id][user_id])
        selected_characters_count = len(user_character_selections[chat_id].get(user_id, []))

        buttons = [
            [
                InlineKeyboardButton(
                    f"{'✅ ' if c['character_name'] in [uc['character_name'] for uc in user_character_selections[chat_id].get(user_id, [])] else ''}"
                    f"{c['character_name']}",
                    callback_data=f"select_character_{i}"
                )
            ]
            for i, c in enumerate(characters)
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        message.reply_text(
            f"Select characters >> \n👥 selected --members--: **{selected_members_count}** \n🃏 selected --characters--: **{selected_characters_count}**",
            reply_markup=reply_markup
        )
    else:
        message.reply_text("You haven't selected any members yet.")

@app.on_callback_query(filters.regex(r"^select_character_"))
def on_select_character(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    selected_char_index = int(callback_query.data.split("_")[2])
    character = characters[selected_char_index]

    # Initialize the user's selected characters list if it doesn't exist for this chat
    if user_id not in user_character_selections[chat_id]:
        user_character_selections[chat_id][user_id] = []

    # Toggle selection: add if not selected, remove if already selected
    if character in user_character_selections[chat_id][user_id]:
        user_character_selections[chat_id][user_id].remove(character)
        callback_query.answer(f"Deselected: {character['character_name']}")
    else:
        user_character_selections[chat_id][user_id].append(character)
        callback_query.answer(f"Selected: {character['character_name']}")

    # Update the character selection message
    update_character_selection_message(client, callback_query.message, user_id, chat_id)

def update_character_selection_message(client, message, user_id, chat_id):
    selected_members_count = len(selected_members[chat_id].get(user_id, []))
    selected_characters_count = len(user_character_selections[chat_id].get(user_id, []))

    buttons = [
        [
            InlineKeyboardButton(
                f"{'✅ ' if c in user_character_selections[chat_id].get(user_id, []) else ''}"
                f"{c['character_name']}",
                callback_data=f"select_character_{i}"
            )
        ]
        for i, c in enumerate(characters)
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    message.edit_text(
        f"Select characters >> \n👥 selected --members--: **{selected_members_count}** \n🃏 selected --characters--: **{selected_characters_count}**",
        reply_markup=reply_markup
    )
    
@app.on_message(filters.command("shuffle") & filters.group)
@admin_only
def show_characters(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if user_id in selected_members[chat_id] and isinstance(selected_members[chat_id][user_id], list):
        if len(selected_members[chat_id][user_id]) != len(user_character_selections[chat_id][user_id]):
            message.reply_text("You need to select exactly the same number of characters as the number of selected members.")
            return

        mafia_players = []
        city_players = []
        unknown_players = []

        random.shuffle(user_character_selections[chat_id][user_id])  # Shuffle the selected characters

        for i, user in enumerate(selected_members[chat_id][user_id]):
            if isinstance(user, int):
                user = client.get_users(user)  # Fetch the user object if it's an integer
            character = user_character_selections[chat_id][user_id][i]
            character_name = character['character_name']
            character_side = character.get('side', 'unknown')

            user_info = f"{user.first_name} {user.last_name or ''} ({user.username or 'N/A'}) - {character_name}"
            if character_side.lower() == 'mafia':
                mafia_players.append(f"🔻 {user_info}")
            elif character_side.lower() == 'city':
                city_players.append(f"🔷 {user_info}")
            else:
                unknown_players.append(f"🔶 {user_info}")

        message_text = "🔴 Mafia Players:\n" + "\n".join(mafia_players) + "\n\n" + \
                       "🔵 City Players:\n" + "\n".join(city_players) + "\n\n" + \
                       "🟡 Unknown Players:\n" + "\n".join(unknown_players)
        
        # message_text = "🔴 Mafia Players:\n" + "||" + "\n".join(mafia_players) + "||" + "\n\n" + \
        #                "🔵 City Players:\n" + "||" + "\n".join(city_players) + "||" + "\n\n" + \
        #                "🟡 Unknown Players:\n" + "||" + "\n".join(unknown_players) + "||" 


        client.send_message(chat_id=user_id, text=f"Selected members and their characters:\n {message_text}")
        message.reply_text("The list of selected characters has been sent to you in a private message.")
    else:
        message.reply_text("You haven't selected any members yet.")

import json

@app.on_message(filters.command("send_characters") & filters.group)
@admin_only
def send_characters_to_selected(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if user_id not in selected_members[chat_id] or not selected_members[chat_id][user_id]:
        message.reply_text("You haven't selected any members yet.")
        return

    if len(selected_members[chat_id][user_id]) != len(user_character_selections[chat_id][user_id]):
        message.reply_text("You need to select exactly the same number of characters as the number of selected members.")
        return

    user_info_data = []  # List to store user information for display

    failed_users = []
    for i, user in enumerate(selected_members[chat_id][user_id]):
        if isinstance(user, int):
            user = client.get_users(user)  # Fetch the user object if it's an integer
        character = user_character_selections[chat_id][user_id][i]
        char_name = character['character_name']
        char_side = character.get('side', 'unknown')

        # Construct user_info with first_name, last_name, and username
        user_info = f"{user.first_name} {user.last_name or ''} ({user.username or 'N/A'})"
        user_info_data.append(user_info)

        try:
            client.send_message(chat_id=user.id, text=f"|| Your character is: {char_name}\nSide: {char_side.capitalize()} ||")
        except Exception as e:
            failed_users.append(user.username or f"{user.first_name} {user.last_name or ''}")
            print(f"Failed to send message to {user.id}: {str(e)}")

    # Write user_info_data to a file
    with open('user_info.json', 'w') as f:
        json.dump(user_info_data, f)

    if failed_users:
        failed_list = ", ".join(failed_users)
        message.reply_text(f"Message sent to all selected members except: {failed_list}")
    else:
        message.reply_text("Message sent to all selected members.")

app.run()