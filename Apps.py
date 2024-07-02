import streamlit as st
import os
import subprocess

def main():
    st.title("Telegram Bot Controller")
    st.write("This application allows you to start and stop your Telegram bot.")

    # Define the path to your Telegram bot script
    script_path = os.path.join(os.path.dirname(__file__), 'telegram_bot.py')

    if st.button("Start Bot"):
        st.write("Starting the bot...")
        subprocess.Popen(["python3", script_path])
        st.success("Bot started successfully.")

    if st.button("Stop Bot"):
        st.write("Stopping the bot...")
        subprocess.run(["pkill", "-f", script_path])
        st.success("Bot stopped successfully.")

if __name__ == "__main__":
    main()
