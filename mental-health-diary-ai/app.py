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
import plotly.express as px

elif page == "📊 Emotion History":
    st.subheader("📈 Your Emotion History")
    data = get_all_entries()

    if data:
        df = pd.DataFrame(data, columns=["Date", "Entry", "Emotion", "Suggestion"])
        df["Date"] = pd.to_datetime(df["Date"])

        # Date range filter
        min_date = df["Date"].min().date()
        max_date = df["Date"].max().date()
        start_date, end_date = st.date_input("Select date range", [min_date, max_date])

        filtered_df = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]

        st.dataframe(filtered_df[["Date", "Emotion", "Suggestion"]])

        # 🎯 1. Interactive Line Chart: Mood Over Time
        st.subheader("🕒 Mood Over Time")
        trend_df = filtered_df.groupby("Date")["Emotion"].agg(lambda x: x.mode()[0] if not x.mode().empty else "Unknown").reset_index()
        fig_line = px.line(trend_df, x="Date", y="Emotion", markers=True, title="Your Mood Trend")
        st.plotly_chart(fig_line, use_container_width=True)

        # 🥧 2. Interactive Pie Chart: Emotion Share
        st.subheader("🧠 Emotion Distribution")
        pie_data = filtered_df["Emotion"].value_counts().reset_index()
        pie_data.columns = ["Emotion", "Count"]
        fig_pie = px.pie(pie_data, names="Emotion", values="Count", title="Emotion Breakdown", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

        # 📊 3. Interactive Bar Chart: Emotion Frequency
        st.subheader("📊 Emotion Frequency")
        fig_bar = px.bar(pie_data, x="Emotion", y="Count", color="Emotion", title="Emotion Frequency Chart")
        st.plotly_chart(fig_bar, use_container_width=True)

        # 📥 Optional Download
        csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Emotion Log as CSV", data=csv, file_name="emotion_log.csv", mime="text/csv")

    else:
        st.info("No entries found yet. Start journaling today!")


# ----------------------------
# Page 3: About
# ----------------------------
else:
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
