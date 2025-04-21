import streamlit as st
from datetime import datetime
from utils.analysis import analyze_emotion
from database.db_handler import insert_entry, get_all_entries
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

# Initialize DB
from database.db_handler import init_db
init_db()

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
# Page 2: Emotion History (Interactive)
# ----------------------------
elif page == "📊 Emotion History":
    st.subheader("📈 Your Emotion History")
    data = get_all_entries()

    if data:
        df = pd.DataFrame(data, columns=["Date", "Entry", "Emotion", "Suggestion"])
        df["Date"] = pd.to_datetime(df["Date"])

        st.dataframe(df[["Date", "Emotion", "Suggestion"]])

        # 📅 Line Chart: Mood over Time
        st.subheader("🕒 Mood Over Time")
        daily_mood = df.groupby("Date")["Emotion"].agg(lambda x: x.mode()[0] if not x.mode().empty else "Unknown").reset_index()
        fig_line = px.line(daily_mood, x="Date", y="Emotion", title="Most Frequent Mood per Day", markers=True)
        st.plotly_chart(fig_line)

        # 🥧 Pie Chart: Emotion Distribution
        st.subheader("🧠 Emotion Distribution")
        emotion_counts = df["Emotion"].value_counts()
        fig_pie = px.pie(
            names=emotion_counts.index,
            values=emotion_counts.values,
            title="Overall Emotion Distribution",
            hole=0.4
        )
        st.plotly_chart(fig_pie)

        # 📊 Bar Chart: Frequency
        st.subheader("📊 Emotion Frequency")
        fig_bar = px.bar(
            x=emotion_counts.index,
            y=emotion_counts.values,
            labels={'x': 'Emotion', 'y': 'Count'},
            title="Emotion Frequency Bar Chart"
        )
        st.plotly_chart(fig_bar)

    else:
        st.info("No entries found yet. Start journaling today!")

# ----------------------------
# Page 3: About
# ----------------------------
elif page == "💡 About":
    st.subheader("💡 About This App")
    st.markdown("""
    Welcome to the **Mental Health Diary & Emotion Tracker** — your personal wellness companion.

    This app helps you:
    - 📝 Reflect by writing daily journal entries  
    - 🧠 Understand your emotions with AI-powered mood analysis  
    - 📊 Track your emotional trends over time  
    - 🎧 Receive mood-specific **Hindi song suggestions**, **motivational quotes**, and **tips**  
    - 📅 Visualize your emotional journey in interactive charts  

    Whether you're feeling joyful, anxious, sad, or lonely — this diary is your safe space to feel, grow, and heal 💚

    _Built using **Streamlit** + **OpenAI GPT** with love by passionate minds 💡_
    """, unsafe_allow_html=True)
