import streamlit as st
import json
import subprocess
import os
import signal


def start_bot():
    if "bot_process" not in st.session_state:
        st.session_state.bot_process = subprocess.Popen(["python", "telegram_bot.py"])
        st.session_state.bot_started = True
        st.write("Telegram bot started.")

def stop_bot():
    if "bot_process" in st.session_state:
        os.kill(st.session_state.bot_process.pid, signal.SIGTERM)
        st.session_state.bot_process = None
        st.session_state.bot_started = False
        st.write("Telegram bot stopped.")
        if os.path.exists('user_info.json'):
            os.remove('user_info.json')
            st.write("user_info.json file deleted.")

def display_members_info():
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

def run():
    st.set_page_config(
        page_title="Telegram Bot Control",
        page_icon="🤖",
    )

    st.title("Telegram Bot Control")

    if st.button("Start Telegram Bot"):
        start_bot()
        st.rerun()

    if st.button("Stop Telegram Bot"):
        stop_bot()
        st.rerun()

    if "bot_started" in st.session_state:
        if st.session_state.bot_started:
            st.success("Telegram bot is currently running.")
        else:
            st.success("Telegram bot is currently stopped.")

    st.title("Display Members Info")
    display_members_info()

if __name__ == "__main__":
    run()
