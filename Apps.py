import streamlit as st
from streamlit.logger import get_logger

LOGGER = get_logger(__name__)

def run():
    st.set_page_config(
        page_title="English with Parsa",
        page_icon="📚",
    )

    st.title("Welcome to English with Parsa! 👋")

    st.sidebar.success("Select a app from the sidebar.")

    st.write(
        """
        Whether you're looking to improve your grammar or enhance your vocabulary,
        you've come to the right place! Choose from the options in the sidebar to
        explore the exciting learning opportunities.

        ## 📕 Grammar Checker 📝
        Enhance your writing skills with our Grammar Checker app. It helps you
        identify and correct grammatical errors, making your writing more polished.

        ## 📘 Vocabulary Quiz 🤓
        Challenge yourself with our Vocabulary Quiz app. Test your knowledge of
        words and expand your English vocabulary in an engaging and interactive way.

        ## 📗 Soon ...

        ### Why Choose English with Parsa?
        - Tailored learning experiences
        - User-friendly apps
        - Improve language skills at your own pace

        ### Get Started
        Select a app from the sidebar to begin your English learning journey!
        
        ### Resources
        - Check out our [documentation](https://docs.englishwithparsa.com)
        - Find the source code on [GitHub](https://github.com/parsa-official/grammar-checker-by-parsa)
          (Grammar Checker by Parsa)

        ### AI Technology
        We utilize Google Gemini AI to power our language learning applications.
        Experience the cutting-edge advancements in AI-driven education.


        ### Stay Connected
        Follow me on:
        - [Instagram](https://www.instagram.com/pkhoshvaghti)
        - [GitHub](https://github.com/parsa-official)
        - [Telegram](https://t.me/official_parsa)
        - [LinkedIn](https://www.linkedin.com/in/pkhoshvaghti/)
        """
    )

if __name__ == "__main__":
    run()