import streamlit as st
import json
import subprocess
import os
import signal
import time
from glob import glob

st.title("Telegram Bot Control")

# Function to start the Telegram bot
def start_bot():
    if "bot_process" not in st.session_state or st.session_state.bot_process.poll() is not None:
        bot_process = subprocess.Popen(["python", "bot_v2.py"])
        st.session_state.bot_process = bot_process
        st.session_state.bot_started = True
        st.write("Telegram bot started.")
    else:
        st.write("Telegram bot is already running.")

# Function to stop the Telegram bot
def stop_bot():
    if "bot_process" in st.session_state and st.session_state.bot_process.poll() is None:
        try:
            bot_process = st.session_state.bot_process
            bot_pid = bot_process.pid

            # Send SIGTERM to the bot process
            os.kill(bot_pid, signal.SIGTERM)
            st.write("Stopping Telegram bot...")

            # Wait for the process to terminate gracefully (up to 5 seconds)
            timeout = 5  # seconds
            start_time = time.time()
            while time.time() - start_time <= timeout:
                if bot_process.poll() is not None:
                    break
                time.sleep(0.1)
            else:
                st.write("Forcefully terminating bot process...")
                os.kill(bot_pid, signal.SIGKILL)

            # Remove session files
            session_files = glob(f"/session_files/{bot_pid}*.session")
            for file in session_files:
                os.remove(file)
                st.write(f"Deleted session file: {file}")

            st.session_state.bot_process = None
            st.session_state.bot_started = False
            st.write("Telegram bot stopped.")
            
            # Delete the JSON file if it exists
            if os.path.exists('user_info.json'):
                os.remove('user_info.json')
                st.write("user_info.json file deleted.")
                
        except Exception as e:
            st.write(f"Error stopping bot: {e}")
    else:
        st.write("Telegram bot is not running.")

# Toggle button to start/stop the bot
bot_status = st.button("Turn Telegram Bot On/Off")

# Handle bot status toggle
if bot_status:
    if "bot_started" in st.session_state and st.session_state.bot_started:
        stop_bot()
    else:
        start_bot()

# Display current bot status
if "bot_started" in st.session_state and st.session_state.bot_started:
    st.success("Telegram bot is currently running.")
else:
    st.info("Telegram bot is currently stopped.")

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
