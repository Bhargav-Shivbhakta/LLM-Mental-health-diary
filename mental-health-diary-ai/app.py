import os
import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px

from utils.analysis import analyze_emotion, PROMPT_VERSIONS, get_eval_scores
from database.db_handler import (
    init_db, insert_entry, get_all_entries, insert_runlog, get_all_runlogs, ensure_migrations
)

# ---------- APP INIT ----------
init_db()
ensure_migrations()  # adds the runlog table if missing
st.set_page_config(page_title="Mental Health Diary", layout="centered")

# ---------- HEADER ----------
st.markdown("""
    <div style="text-align: center;">
        <h1 style="color: #4CAF50; font-size: 36px;">🧠 Mental Health Diary</h1>
        <p style="font-size: 18px;">Your personal emotional wellness companion 💚</p>
    </div>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
st.sidebar.markdown("## 📌 Navigation")
page = st.sidebar.radio("Go to", ["📝 Write Journal", "📊 Emotion History", "🧪 Evaluate Outputs", "💡 About"])

st.sidebar.markdown("---")
st.sidebar.info("Stay consistent and reflect daily 🌱")

# Assignment knobs (transparent + reproducible)
st.sidebar.markdown("## ⚙️ Experiment Settings")
prompt_choice = st.sidebar.selectbox(
    "Prompt version (for assignment iterations)", list(PROMPT_VERSIONS.keys()), index=0
)
temperature = st.sidebar.slider("Creativity (temperature)", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
max_tokens = st.sidebar.slider("Max tokens", min_value=256, max_value=2048, value=600, step=64)
model_name = st.sidebar.selectbox("Model", ["gpt-3.5-turbo"], index=0)  # pinned to 3.5 per requirement

st.sidebar.markdown("---")
st.sidebar.caption(
    "⚠️ Not a medical device. If you’re in crisis or thinking about self-harm, seek immediate help. "
    "In the U.S., call or text **988** (Suicide & Crisis Lifeline). If outside the U.S., contact local emergency numbers."
)

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
            emotion, suggestion, raw = analyze_emotion(
                entry,
                prompt_version=prompt_choice,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )

            st.success(f"**Detected Emotion:** `{emotion}`")
            st.markdown(suggestion, unsafe_allow_html=True)

            insert_entry(datetime.now().strftime("%Y-%m-%d"), entry, emotion, suggestion)
            insert_runlog(
                timestamp=datetime.now().isoformat(timespec="seconds"),
                prompt_version=prompt_choice,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                user_input=entry,
                raw_request=raw["request"],
                raw_response=raw["response"]
            )
            st.info("Saved entry and logged prompt/response for evaluation ✅")

# ----------------------------
# Page 2: Emotion History
# ----------------------------
elif page == "📊 Emotion History":
    st.subheader("📈 Your Emotion History")
    data = get_all_entries()

    if data:
        df = pd.DataFrame(data, columns=["Date", "Entry", "Emotion", "Suggestion"])
        df["Date"] = pd.to_datetime(df["Date"])
        st.dataframe(df[["Date", "Emotion", "Suggestion"]])

        # 📅 Line Chart: “mood” over time
        st.subheader("🕒 Mood Over Time")
        daily_mood = df.groupby("Date")["Emotion"].agg(lambda x: x.mode()[0] if not x.mode().empty else "Unknown").reset_index()
        fig_line = px.line(daily_mood, x="Date", y="Emotion", title="Most Frequent Mood per Day", markers=True)
        st.plotly_chart(fig_line)

        # 🥧 Distribution
        st.subheader("🧠 Emotion Distribution")
        emotion_counts = df["Emotion"].value_counts()
        fig_pie = px.pie(
            names=emotion_counts.index,
            values=emotion_counts.values,
            title="Overall Emotion Distribution",
            hole=0.4
        )
        st.plotly_chart(fig_pie)

        # 📊 Frequency
        st.subheader("📊 Emotion Frequency")
        fig_bar = px.bar(
            x=emotion_counts.index,
            y=emotion_counts.values,
            labels={'x': 'Emotion', 'y': 'Count'},
            title="Emotion Frequency Bar Chart"
        )
        st.plotly_chart(fig_bar)

        st.download_button(
            "⬇️ Export entries (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="emotion_entries.csv",
            mime="text/csv"
        )
    else:
        st.info("No entries found yet. Start journaling today!")

# ----------------------------
# Page 3: Evaluate Outputs (for rubric’s analytical review)
# ----------------------------
elif page == "🧪 Evaluate Outputs":
    st.subheader("🧪 Evaluation Dashboard")
    logs = get_all_runlogs()
    if logs:
        logs_df = pd.DataFrame(logs, columns=[
            "timestamp","prompt_version","model","temperature","max_tokens",
            "user_input","raw_request","raw_response"
        ])
        st.dataframe(logs_df[["timestamp","prompt_version","model","temperature","user_input"]])

        # Auto-scoring (heuristics + LLM-lite rubric)
        st.markdown("##### Auto-Scores (0–5) for: Empathy, Specificity, Actionability, Safety")
        scored = get_eval_scores(logs_df)
        st.dataframe(scored[["timestamp","prompt_version","Empathy","Specificity","Actionability","Safety","Notes"]])

        # Aggregate view
        agg = scored.groupby("prompt_version")[["Empathy","Specificity","Actionability","Safety"]].mean().round(2).reset_index()
        st.markdown("##### Average by Prompt Version")
        st.dataframe(agg)

        st.download_button(
            "⬇️ Export evaluation (CSV)",
            data=scored.to_csv(index=False).encode("utf-8"),
            file_name="evaluation_scores.csv",
            mime="text/csv"
        )
        st.info("Use these tables/CSV excerpts in your Canvas write-up for the analytical review section.")
    else:
        st.info("No run logs yet. Analyze & Save a few journal entries first to populate this page.")

# ----------------------------
# Page 4: About
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

    **Ethics & Safety**  
    - This is not a medical device and does not provide clinical advice.  
    - If you are in immediate danger or thinking about self-harm, seek help right away. In the U.S., call or text **988**.

    _Built using **Streamlit** + **OpenAI GPT-3.5**_
    """, unsafe_allow_html=True)
