from pyrogram import Client, filters

class MyTelegramBot:
    def __init__(self):
        self.app = Client(
            "GOD_Mafia",
            api_id=27689690,
            api_hash="893842f3f7e2fe003d8fc73d47045cbf",
            bot_token="7288761682:AAE_XDugs5OKYGV1JA4vFi1qmJdpMAH5I90"
        )

        # Define the function to display the commands
        @self.app.on_message(filters.command(["start"]) & filters.group)
        def start(client, message):
            help_text = "Hello, it's okay."
            message.reply_text(help_text)

    def run(self):
        self.app.run()

# Example usage if run directly
if __name__ == "__main__":
    bot = MyTelegramBot()
    bot.run()
