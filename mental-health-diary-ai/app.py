import streamlit as st
from datetime import datetime
from utils.analysis import analyze_emotion
from database.db_handler import insert_entry, get_all_entries
import pandas as pd
import matplotlib.pyplot as plt

# Initialize DB
from database.db_handler import init_db
init_db()

# Set up page
st.set_page_config(page_title="Mental Health Diary", layout="centered")

# Header
st.markdown("""
    <div style="text-align: center;">
        <h1 style="color: #4CAF50; font-size: 36px;">🧠 Mental Health Diary</h1>
        <p style="font-size: 18px;">Your personal emotional wellness companion 💚</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.markdown("## 📌 Navigation")
page = st.sidebar.radio("Go to", ["📝 Write Journal", "📊 Emotion History", "💡 About"])
st.sidebar.markdown("---")
st.sidebar.info("Stay consistent and reflect daily 🌱")

# ----------------------------
# Page 1: Journal Entry
# ----------------------------
if page == "📝 Write Journal":
    st.markdown("#### ✍️ How are you feeling today?")
    entry = st.text_area("Write your journal entry below", height=250, placeholder="Lately I've been feeling...")

    if st.button("🧠 Analyze & Save"):
        if entry.strip() == "":
            st.warning("Please write something before submitting.")
        else:
            emotion, suggestion = analyze_emotion(entry)
            st.success(f"**Detected Emotion:** `{emotion}`")
            st.markdown(suggestion, unsafe_allow_html=True)
            insert_entry(datetime.now().strftime("%Y-%m-%d"), entry, emotion, suggestion)

# ----------------------------
# Page 2: History
# ----------------------------
elif page == "📊 Emotion History":
    st.subheader("📈 Your Emotion History")
    data = get_all_entries()
    if data:
        df = pd.DataFrame(data, columns=["Date", "Entry", "Emotion", "Suggestion"])
        st.dataframe(df[["Date", "Emotion", "Suggestion"]])

        # Emotion frequency bar chart
        st.subheader("Emotion Frequency")
        emotion_counts = df["Emotion"].value_counts()
        fig, ax = plt.subplots()
        emotion_counts.plot(kind='bar', ax=ax, color="#4CAF50")
        ax.set_title("Emotion Frequency", fontsize=16)
        ax.set_ylabel("Count")
        st.pyplot(fig)
    else:
        st.info("No entries found yet. Start journaling today!")

# ----------------------------
# Page 3: About
# ----------------------------
else:
    st.subheader("💡 About This App")
    st.markdown("""
    This app is your personal space to reflect, feel, and grow emotionally.

    - 📝 Write daily journal entries  
    - 🧠 Get emotional analysis powered by AI  
    - 📊 Visualize your emotional trends  
    - 🎧 Receive mood-specific Hindi songs, quotes & tips

    _Crafted with ❤️ using Streamlit & OpenAI_
    """)
