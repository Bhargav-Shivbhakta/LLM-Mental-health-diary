import streamlit as st
from datetime import datetime
from utils.analysis import analyze_emotion
from database.db_handler import insert_entry, get_all_entries
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Mental Health Diary", layout="centered")

# Sidebar
st.sidebar.title("Mental Health Diary 🧠")
page = st.sidebar.radio("Go to", ["Write Journal", "Emotion History", "About"])

# Page 1: Journal Entry
if page == "Write Journal":
    st.title("📝 Today's Journal")
    entry = st.text_area("How are you feeling today?", height=200)
    if st.button("Analyze & Save"):
        if entry.strip() == "":
            st.warning("Please write something before submitting.")
        else:
            emotion, suggestion = analyze_emotion(entry)
            st.success(f"Detected Emotion: **{emotion}**")
            st.info(f"Suggestion: _{suggestion}_")
            insert_entry(datetime.now().strftime("%Y-%m-%d"), entry, emotion, suggestion)

# Page 2: History
elif page == "Emotion History":
    st.title("📊 Your Emotion History")
    data = get_all_entries()
    if data:
        df = pd.DataFrame(data, columns=["Date", "Entry", "Emotion", "Suggestion"])
        st.dataframe(df[["Date", "Emotion", "Suggestion"]])

        # Plot emotion frequency
        st.subheader("Emotion Frequency")
        emotion_counts = df["Emotion"].value_counts()
        fig, ax = plt.subplots()
        emotion_counts.plot(kind='bar', ax=ax)
        st.pyplot(fig)
    else:
        st.info("No entries found yet.")

# Page 3: About
else:
    st.title("💡 About")
    st.markdown("""
    This app helps you track your mental health by:
    - Writing daily journal entries
    - Detecting emotional tone using AI
    - Providing motivational suggestions
    - Showing your emotion trends over time

    _Built with ❤️ using Streamlit and OpenAI_
    """)
