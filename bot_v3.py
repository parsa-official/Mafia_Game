import os
import json
import random
from pathlib import Path
from functools import wraps
from collections import defaultdict
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors.exceptions import MessageNotModified
from pyrogram.enums import ChatMemberStatus

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = Path(script_dir) / "config.json"

# Load the configuration from the config file
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

workdir = Path(script_dir) / config["workdir"]
workdir.mkdir(parents=True, exist_ok=True)

app = Client(
    name="GOD_Mafia",
    api_id=config["api_id"],
    api_hash=config["api_hash"],
    bot_token=config["bot_token"],
    workdir=workdir  # Specify the work directory
)

# Construct the absolute path to the JSON file
json_file_path = os.path.join(script_dir, "db/characters.json")

# Load characters from JSON file
with open(json_file_path, "r", encoding="utf-8") as file:
    data = json.load(file)
    characters = data["mafia"] + data["city"] + data["unknown"]

selected_members = defaultdict(dict)
user_characters = defaultdict(dict)
user_character_selections = defaultdict(dict)
shuffled_characters = defaultdict(dict)


def is_admin(client, chat_id, user_id):
    member = client.get_chat_member(chat_id, user_id)
    return member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]

def admin_only(func):
    @wraps(func)
    def wrapper(client, update, *args, **kwargs):
        chat_id = update.chat.id if hasattr(update, 'chat') else update.message.chat.id
        user_id = update.from_user.id

        if not is_admin(client, chat_id, user_id):
            if isinstance(update, CallbackQuery):
                update.answer("Only admins can use this command.", show_alert=True)
            else:
                update.reply_text("You must be an admin to use this command.")
            return
        return func(client, update, *args, **kwargs)
    return wrapper
commands_list = [
    ("/start", "Start the bot \n"),
    ("/select_members", "Select members for the game \n"),
    ("/select_characters", "Select characters for the members \n"),
    ("/shuffle", "Shuffle characters and show the list to admin \n"),
    ("/send_characters", "Send the selected characters to members \n\n"),
    ("/reset", "Reset the bot (admin only)")
]


# Define the function to display the commands
@app.on_message(filters.command(["start", "commands"]) & filters.group)
@admin_only
def start(client, message):
    help_text = "Available commands:\n\n"
    for command, description in commands_list:
        help_text += f"{command} - {description}\n"
    
    message.reply_text(help_text)


def reset():
    global selected_members, user_characters, user_character_selections
    selected_members = defaultdict(dict)
    user_characters = defaultdict(dict)
    user_character_selections = defaultdict(dict)
    # Any other reset logic can go here

# Command handler for /reset
@app.on_message(filters.command("reset") & filters.group)
@admin_only
def reset_command(client, message):
    reset()
    message.reply_text("Bot data has been reset.")
#####################################################################################

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
                f"{'✅ ' if m.user.id in selected_members.get(chat_id, {}).get(user_id, []) else ''}"
                f"{m.user.first_name} {m.user.last_name or ''} ({m.user.username or 'N/A'})",
                callback_data=f"select_member_{m.user.id}"
            )
        ]
        for m in sorted_members
    ]

    # Add '----done----' button to the end
    done_button = InlineKeyboardButton("----☑️ done ☑️----", callback_data="done_selecting_members")
    buttons.append([done_button])

    reply_markup = InlineKeyboardMarkup(buttons)
    message.reply_text("Select members:", reply_markup=reply_markup)

@app.on_callback_query(filters.regex(r"^select_member_"))
@admin_only
def on_select_member(client, callback_query):
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

@app.on_callback_query(filters.regex(r"^done_selecting_members"))
@admin_only
def done_selecting_members(client, callback_query):
    callback_query.message.delete()

    # Send a new message with the count of selected members
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    selected_count = len(selected_members.get(chat_id, {}).get(user_id, []))

    client.send_message(
        chat_id=chat_id,
        text=f"👥 Selected --members-- >>> **{selected_count}** \n\n Edit --Members--: /select_members \n Choose --Characters--: /select_characters",
    )
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

    # Add '----done----' button to the end
    done_button = InlineKeyboardButton("----☑️ done ☑️----", callback_data="done_selecting_members")
    buttons.append([done_button])

    selected_count = len(selected_members.get(chat_id, {}).get(user_id, []))
    reply_markup = InlineKeyboardMarkup(buttons)
    
    # Edit the original message with updated selection status
    try:
        message.edit_text(f"Select members >> \n👥 selected: {selected_count}", reply_markup=reply_markup)
    except MessageNotModified:
        pass 

def save_selected_members(client, selected_members, chat_id, user_id):
    user_info_data = []

    for user_id in selected_members[chat_id][user_id]:
        user = client.get_users(user_id)
        user_info = f"{user.first_name} {user.last_name or ''} ({user.username or 'N/A'})"
        user_info_data.append(user_info)

    with open('user_info.json', 'w') as f:
        json.dump(user_info_data, f)


####################################################################################################
characters_mafia = data["mafia"]
characters_city = data["city"]
characters_unknown = data["unknown"]


@app.on_message(filters.command("select_characters") & filters.group)
@admin_only
def select_characters(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if user_id in selected_members[chat_id] and selected_members[chat_id][user_id]:
        selected_members_count = len(selected_members[chat_id][user_id])
        selected_characters_count = len(user_character_selections[chat_id].get(user_id, []))

        buttons = [
            [InlineKeyboardButton("Mafia", callback_data="select_group_mafia")],
            [InlineKeyboardButton("City", callback_data="select_group_city")],
            [InlineKeyboardButton("Unknown", callback_data="select_group_unknown")],
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        message.reply_text(
            f"Select character group >> \n👥 selected --members--: **{selected_members_count}** \n🃏 selected --characters--: **{selected_characters_count}**",
            reply_markup=reply_markup
        )
    else:
        message.reply_text("You haven't selected any members yet.")

@app.on_callback_query(filters.regex(r"^select_group_"))
@admin_only
def on_select_group(client, callback_query: CallbackQuery):
    group = callback_query.data.split("_")[2]
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if group == "mafia":
        character_list = characters_mafia
    elif group == "city":
        character_list = characters_city
    else:
        character_list = characters_unknown

    buttons = [
        [
            InlineKeyboardButton(
                f"{'✅ ' if c['character_name'] in [uc['character_name'] for uc in user_character_selections[chat_id].get(user_id, [])] else ''}"
                f"{c['character_name']}",
                callback_data=f"select_character_{group}_{i}"
            )
        ]
        for i, c in enumerate(character_list)
    ]

    # Add 'back' button to return to select_characters
    back_button = InlineKeyboardButton("Back 🔙", callback_data="back_to_select_characters")
    buttons.append([back_button])

    reply_markup = InlineKeyboardMarkup(buttons)
    callback_query.message.edit_text(
        f"Select characters from {group} >>",
        reply_markup=reply_markup
    )

@app.on_callback_query(filters.regex(r"^select_character_"))
@admin_only
def on_select_character(client, callback_query: CallbackQuery):
    data = callback_query.data.split("_")
    group = data[2]
    selected_char_index = int(data[3])

    if group == "mafia":
        character = characters_mafia[selected_char_index]
    elif group == "city":
        character = characters_city[selected_char_index]
    else:
        character = characters_unknown[selected_char_index]

    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

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
    update_character_selection_message(client, callback_query.message, user_id, chat_id, group)

def update_character_selection_message(client, message, user_id, chat_id, group):
    if group == "mafia":
        character_list = characters_mafia
    elif group == "city":
        character_list = characters_city
    else:
        character_list = characters_unknown

    selected_members_count = len(selected_members[chat_id].get(user_id, []))
    selected_characters_count = len(user_character_selections[chat_id].get(user_id, []))

    buttons = [
        [
            InlineKeyboardButton(
                f"{'✅ ' if c in user_character_selections[chat_id].get(user_id, []) else ''}"
                f"{c['character_name']}",
                callback_data=f"select_character_{group}_{i}"
            )
        ]
        for i, c in enumerate(character_list)
    ]

    # Add 'back' button to return to select_characters
    back_button = InlineKeyboardButton("Back 🔙", callback_data="back_to_select_characters")
    buttons.append([back_button])

    reply_markup = InlineKeyboardMarkup(buttons)
    message.edit_text(
        f"Select characters from {group} >> \n👥 selected --members--: **{selected_members_count}** \n🃏 selected --characters--: **{selected_characters_count}**",
        reply_markup=reply_markup
    )

@app.on_callback_query(filters.regex(r"^back_to_select_characters"))
@admin_only
def back_to_select_characters(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if user_id in selected_members[chat_id] and selected_members[chat_id][user_id]:
        selected_members_count = len(selected_members[chat_id][user_id])
        selected_characters_count = len(user_character_selections[chat_id].get(user_id, []))

        buttons = [
            [InlineKeyboardButton("Mafia", callback_data="select_group_mafia")],
            [InlineKeyboardButton("City", callback_data="select_group_city")],
            [InlineKeyboardButton("Unknown", callback_data="select_group_unknown")],
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        callback_query.message.edit_text(
            f"Select character group >> \n👥 selected --members--: **{selected_members_count}** \n🃏 selected --characters--: **{selected_characters_count}**",
            reply_markup=reply_markup
        )
    else:
        callback_query.message.edit_text("You haven't selected any members yet.")


###########################################################################
@app.on_message(filters.command("shuffle") & filters.group)
@admin_only
def show_characters(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if user_id in selected_members[chat_id] and isinstance(selected_members[chat_id][user_id], list):
        if len(selected_members[chat_id][user_id]) != len(user_character_selections[chat_id][user_id]):
            message.reply_text("You need to select exactly the same number of characters as the number of selected members.")
            return

        # Shuffle the user_character_selections before using them
        shuffled_character_selections = user_character_selections[chat_id][user_id][:]
        random.shuffle(shuffled_character_selections)

        # Store the shuffled characters
        shuffled_characters[chat_id][user_id] = shuffled_character_selections

        mafia_players = []
        city_players = []
        unknown_players = []

        user_character_pairs = []

        for i, user in enumerate(selected_members[chat_id][user_id]):
            if isinstance(user, int):
                user = client.get_users(user)  # Fetch the user object if it's an integer
            character = shuffled_character_selections[i]
            character_id = character['id']
            character_name = character['character_name']
            character_side = character.get('side', 'unknown')

            # Truncate the username if it exceeds 10 characters
            truncated_username = user.username[:10] + '...' if user.username and len(user.username) > 8 else (user.username or 'N/A')

            user_info = f"{user.first_name} {user.last_name or ''} ({truncated_username}) - --**{character_name}**--"
            user_character_pairs.append((character_id, character_side, user_info))

        # Sort the user_character_pairs by character_id
        user_character_pairs.sort(key=lambda x: x[0])

        for character_id, character_side, user_info in user_character_pairs:
            if character_side.lower() == 'mafia':
                mafia_players.append(f"🔻 {user_info}")
            elif character_side.lower() == 'city':
                city_players.append(f"🔷 {user_info}")
            else:
                unknown_players.append(f"🔶 {user_info}")

        # Select a random player to start the game
        starting_player = random.choice(selected_members[chat_id][user_id])
        if isinstance(starting_player, int):
            starting_player = client.get_users(starting_player)

        starting_player_info = f" --**{starting_player.first_name} {starting_player.last_name or ''}**-- ({starting_player.username or 'N/A'})"

        message_text = "🔴 Mafia Players:\n" + "||" + "\n".join(mafia_players) + "||" + "\n\n" + \
                       "🔵 City Players:\n" + "||" + "\n".join(city_players) + "||" + "\n\n" + \
                       "🟡 Unknown Players:\n" + "||" + "\n".join(unknown_players) + "||" + "\n\n" + \
                       f"🗣 Starting Player: {starting_player_info}"

        client.send_message(chat_id=user_id, text=f"Selected members and their characters:\n\n {message_text}")
        message.reply_text("The list of selected characters has been sent to you in a private message.")
    else:
        message.reply_text("You haven't selected any members yet.")



###########################################################################
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

    if chat_id not in shuffled_characters or user_id not in shuffled_characters[chat_id]:
        message.reply_text("You need to shuffle the characters first using /shuffle.")
        return

    shuffled_character_selections = shuffled_characters[chat_id][user_id]

    user_info_data = []  # List to store user information for display

    failed_users = []
    for i, user in enumerate(selected_members[chat_id][user_id]):
        if isinstance(user, int):
            user = client.get_users(user)  # Fetch the user object if it's an integer
        character = shuffled_character_selections[i]
        char_name = character['character_name']
        char_side = character.get('side', 'unknown')
        char_emoji = character.get('emoji', '')

        # Construct user_info with first_name, last_name, and username
        user_info = f"{user.first_name} {user.last_name or ''} ({user.username or 'N/A'})"
        user_info_data.append(user_info)

        try:
            # Mapping char_side to Persian equivalent
            if char_side.lower() == 'city':
                char_side_persian = "شهروند"
            elif char_side.lower() == 'mafia':
                char_side_persian = "مافیا"
            else:
                char_side_persian = "مستقل"

            # Sending the message to the user
            client.send_message(
                chat_id=user.id, 
                text=f"لطفاً از نشان دادن نقش خود به دیگران و باز کردن پیام در دید بقیه بازیکن‌ها خودداری کنید.\n\nنقش شما در این بازی:\n\n|| **{char_name} {char_emoji}** ||\n\nساید شما در این بازی:\n\n|| **{char_side_persian}** || \n"
            )

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