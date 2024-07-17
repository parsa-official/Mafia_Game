import streamlit as st
import json
import subprocess
import os
import signal
import time
from glob import glob

st.title("Telegram Bot Control")

# Function to start the Telegram bot
def start_bot(bot_version):
    other_bot_version = "bot_v3" if bot_version == "bot_v4" else "bot_v4"
    bot_key = f"{bot_version}_process"
    other_bot_key = f"{other_bot_version}_process"

    # Check if the other bot is running and stop it
    if other_bot_key in st.session_state and st.session_state[other_bot_key] is not None and st.session_state[other_bot_key].poll() is None:
        stop_bot(other_bot_version)
        time.sleep(5)  # Wait for 5 seconds before starting the new bot

    if bot_key not in st.session_state or st.session_state[bot_key] is None or st.session_state[bot_key].poll() is not None:
        bot_process = subprocess.Popen(["python", f"{bot_version}.py"])
        st.session_state[bot_key] = bot_process
        st.session_state[f"{bot_version}_started"] = True
        st.write(f"Telegram bot {bot_version} started.")
    else:
        st.write(f"Telegram bot {bot_version} is already running.")

# Function to stop the Telegram bot
def stop_bot(bot_version):
    bot_key = f"{bot_version}_process"
    if bot_key in st.session_state and st.session_state[bot_key] is not None and st.session_state[bot_key].poll() is None:
        try:
            bot_process = st.session_state[bot_key]
            bot_pid = bot_process.pid

            # Send SIGTERM to the bot process
            os.kill(bot_pid, signal.SIGTERM)
            st.write(f"Stopping Telegram bot {bot_version}...")

            # Wait for the process to terminate gracefully (up to 5 seconds)
            timeout = 5  # seconds
            start_time = time.time()
            while time.time() - start_time <= timeout:
                if bot_process.poll() is not None:
                    break
                time.sleep(0.1)
            else:
                st.write(f"Forcefully terminating bot {bot_version} process...")
                os.kill(bot_pid, signal.SIGKILL)

            # Remove session files
            session_files = glob(f"/session_files/{bot_pid}*.session")
            for file in session_files:
                os.remove(file)
                st.write(f"Deleted session file: {file}")

            st.session_state[bot_key] = None
            st.session_state[f"{bot_version}_started"] = False
            st.write(f"Telegram bot {bot_version} stopped.")
            
            # Delete the JSON file if it exists
            if os.path.exists('user_info.json'):
                os.remove('user_info.json')
                st.write("user_info.json file deleted.")
                
        except Exception as e:
            st.write(f"Error stopping bot {bot_version}: {e}")
    else:
        st.write(f"Telegram bot {bot_version} is not running.")

# Toggle button to start/stop bot_v3
if "bot_v3_started" not in st.session_state:
    st.session_state.bot_v3_started = False

bot_v3_status = st.button("Mafia-Classic", disabled=st.session_state.get("bot_v4_started", False))
if bot_v3_status:
    if st.session_state.bot_v3_started:
        stop_bot("bot_v3")
    else:
        start_bot("bot_v3")

# Toggle button to start/stop bot_v4
if "bot_v4_started" not in st.session_state:
    st.session_state.bot_v4_started = False

bot_v4_status = st.button("Mafia-Night", disabled=st.session_state.get("bot_v3_started", False))
if bot_v4_status:
    if st.session_state.bot_v4_started:
        stop_bot("bot_v4")
    else:
        start_bot("bot_v4")

# Display current bot status
if st.session_state.bot_v3_started:
    st.success("Telegram bot (Mafia-Classic) is currently running.")
else:
    st.info("Telegram bot (Mafia-Classic) is currently stopped.")

if st.session_state.bot_v4_started:
    st.success("Telegram bot (Mafia-Night) is currently running.")
else:
    st.info("Telegram bot (Mafia-Night) is currently stopped.")

st.title("Display Members Info")

try:
    with open('user_info.json', 'r') as f:
        user_info_data = json.load(f)
except FileNotFoundError:
    user_info_data = []

if user_info_data:
    for info in user_info_data:
        st.write(info)
else:
    st.write("No user information available yet.")
