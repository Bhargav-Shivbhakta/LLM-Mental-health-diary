# app.py — Mental Health Diary (Therapist-style)
# ----------------------------------------------
# Streamlit app for mixed-emotion daily journaling with supportive, therapist-like AI reflections.
# - Uses GPT-3.5 (legacy ChatCompletion) via st.secrets["openai_api_key"]
# - Stores entries in SQLite (entries table), logs raw prompts/responses (runlog table)
# - If database.db_handler is unavailable, uses internal SQLite helpers

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px

# ======================= OpenAI (legacy client) =======================
try:
    import openai
except Exception as e:
    openai = None

# ======================= DB Imports (robust) ==========================
# Try to import your existing db helpers; if not present, define fallbacks.
def _safe_import_db():
    try:
        from database.db_handler import (
            init_db, ensure_migrations, insert_entry, get_all_entries,
            insert_runlog, get_all_runlogs
        )
        return {
            "init_db": init_db,
            "ensure_migrations": ensure_migrations,
            "insert_entry": insert_entry,
            "get_all_entries": get_all_entries,
            "insert_runlog": insert_runlog,
            "get_all_runlogs": get_all_runlogs,
            "_uses_internal": False
        }
    except Exception:
        # Fallback: lightweight internal SQLite implementation
        DB_PATH = os.getenv("DB_PATH", "diary.db")

        def _conn():
            return sqlite3.connect(DB_PATH, check_same_thread=False)

        def init_db():
            with _conn() as con:
                cur = con.cursor()
                cur.execute("""
                CREATE TABLE IF NOT EXISTS entries(
                    date TEXT,
                    entry TEXT,
                    emotion TEXT,
                    suggestion TEXT
                )""")
                con.commit()

        def ensure_migrations():
            with _conn() as con:
                cur = con.cursor()
                cur.execute("""
                CREATE TABLE IF NOT EXISTS runlog(
                    timestamp TEXT,
                    prompt_version TEXT,
                    model TEXT,
                    temperature REAL,
                    max_tokens INTEGER,
                    user_input TEXT,
                    raw_request TEXT,
                    raw_response TEXT
                )""")
                con.commit()

        def insert_entry(date, entry, emotion, suggestion):
            with _conn() as con:
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO entries(date, entry, emotion, suggestion) VALUES(?,?,?,?)",
                    (date, entry, emotion, suggestion)
                )
                con.commit()

        def get_all_entries():
            with _conn() as con:
                cur = con.cursor()
                cur.execute("SELECT date, entry, emotion, suggestion FROM entries ORDER BY date ASC")
                return cur.fetchall()

        def insert_runlog(timestamp, prompt_version, model, temperature, max_tokens, user_input, raw_request, raw_response):
            with _conn() as con:
                cur = con.cursor()
                cur.execute("""
                    INSERT INTO runlog(timestamp, prompt_version, model, temperature, max_tokens, user_input, raw_request, raw_response)
                    VALUES(?,?,?,?,?,?,?,?)
                """, (timestamp, prompt_version, model, temperature, max_tokens, user_input, raw_request, raw_response))
                con.commit()

        def get_all_runlogs():
            with _conn() as con:
                cur = con.cursor()
                cur.execute("""
                    SELECT timestamp, prompt_version, model, temperature, max_tokens, user_input, raw_request, raw_response
                    FROM runlog ORDER BY timestamp DESC
                """)
                return cur.fetchall()

        return {
            "init_db": init_db,
            "ensure_migrations": ensure_migrations,
            "insert_entry": insert_entry,
            "get_all_entries": get_all_entries,
            "insert_runlog": insert_runlog,
            "get_all_runlogs": get_all_runlogs,
            "_uses_internal": True
        }

DB = _safe_import_db()

# ======================= App Config =======================
st.set_page_config(page_title="Mental Health Diary (Therapist)", layout="centered")

# Header
st.markdown("""
    <div style="text-align: center;">
        <h1 style="color: #4CAF50; font-size: 36px;">🧠 Mental Health Diary</h1>
        <p style="font-size: 18px;">A reflective space with a supportive, therapist-style companion</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar: Navigation + Settings
st.sidebar.markdown("## 📌 Navigation")
page = st.sidebar.radio("Go to", ["📝 Write Journal", "📜 History", "🧪 Evaluate Outputs", "ℹ️ About"])
st.sidebar.markdown("---")

st.sidebar.markdown("## ⚙️ AI Settings")
PROMPT_VERSIONS = {
    "v1 — concise therapist": """
You are an empathetic mental health companion.
Given a user's daily journal entry (mixed emotions welcome), do the following:
1) Summary: In 2–3 sentences, summarize the emotional landscape of the day (acknowledge both positives and struggles).
2) Reflection: In 2–3 sentences, validate their feelings, notice any patterns, and highlight signs of resilience.
3) Advice: Offer one realistic, compassionate suggestion for tomorrow (no quotes, no music, no diagnosis).
Tone: warm, human, non-clinical, non-judgmental.
Return JSON with keys: summary, reflection, advice.
""".strip(),
    "v2 — therapist + pattern spotting": """
You are a supportive, therapist-style companion.
For the user's mixed-emotion daily journal entry:
1) Summary (2–3 sentences): capture highs and lows with specificity (echo 1–2 exact phrases).
2) Reflection (2–3 sentences): name a helpful pattern or theme, and validate the user’s experience.
3) Advice (1–2 sentences): one small, practical next step for tomorrow, aligned to their context.
No quotes or music. No diagnosis. Return JSON: summary, reflection, advice.
""".strip(),
    "v3 — therapist + resilience focus": """
You are a compassionate, motivational counselor.
For the user's daily journal entry:
1) Summary (2–3 sentences): acknowledge competing emotions and moments that mattered.
2) Reflection (2–3 sentences): highlight resilience and agency; gently reframe any harsh self-talk.
3) Advice (1–2 sentences): one micro-action (<10 minutes) for tomorrow to build momentum.
Avoid clinical terms, quotes, or songs. Return JSON with keys: summary, reflection, advice.
""".strip(),
}
prompt_choice = st.sidebar.selectbox("Prompt version", list(PROMPT_VERSIONS.keys()), index=0)
temperature = st.sidebar.slider("Creativity (temperature)", 0.0, 1.0, 0.3, 0.1)
max_tokens = st.sidebar.slider("Max tokens", 256, 2048, 600, 64)
model_name = st.sidebar.selectbox("Model", ["gpt-3.5-turbo"], index=0)

st.sidebar.markdown("---")
st.sidebar.info("This app is a supportive companion, not a medical device. If you’re in crisis, call or text 988 (U.S.) or local emergency services.")

# ======================= Initialize DB =======================
DB["init_db"]()
DB["ensure_migrations"]()

# ======================= OpenAI Setup =======================
api_key = st.secrets.get("openai_api_key", None)
if openai is None:
    st.error("OpenAI library not found. Add 'openai==0.28.1' to requirements.txt.")
if api_key and openai:
    openai.api_key = api_key

def _chat_complete(prompt: str) -> str:
    if not api_key or not openai:
        raise RuntimeError("Missing OpenAI API key or library.")
    resp = openai.ChatCompletion.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a warm, concise therapist-style companion. Avoid diagnosis."},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp["choices"][0]["message"]["content"]

def _extract_json(text: str) -> dict:
    import re, json
    m = re.search(r"\{.*\}", text, re.DOTALL)
    blob = m.group(0) if m else "{}"
    try:
        return json.loads(blob)
    except Exception:
        return {"summary": "", "reflection": "", "advice": ""}

# ======================= Scoring (Evaluate page) =======================
def score_empathy(text: str) -> int:
    cues = ["I hear", "it sounds", "I understand", "valid", "makes sense", "it's okay", "you showed"]
    return min(5, sum(1 for c in cues if c.lower() in text.lower()))

def score_specificity(text: str, ref: str) -> int:
    # award points if it echoes user's phrases (naive)
    import re
    hits, seen = 0, set()
    for tok in ref.lower().split():
        tok = re.sub(r"[^a-z0-9]", "", tok)
        if len(tok) > 5 and tok not in seen:
            seen.add(tok)
            if tok in text.lower():
                hits += 1
            if hits >= 5:
                break
    return min(5, 1 + hits)

def score_actionability(text: str) -> int:
    cues = ["tomorrow", "try ", "you can ", "set a timer", "write down", "breathe", "walk", "5-minute", "micro"]
    return min(5, 1 + sum(1 for c in cues if c in text.lower()))

def score_safety(text: str) -> int:
    cues = ["not a medical device", "988", "seek immediate", "emergency", "crisis"]
    return min(5, 1 + sum(1 for c in cues if c in text.lower()))

# ======================= PAGE: Write Journal =======================
if page == "📝 Write Journal":
    st.markdown("#### ✍️ Write about your day (mixed emotions welcome)")
    entry = st.text_area(
        "Describe your day in detail: what happened, what you felt (ups and downs), and anything that stuck with you.",
        height=280,
        placeholder="Example: I submitted my project but stumbled during the Q&A. Later a friend cheered me up..."
    )

    if st.button("🧠 Reflect & Save"):
        if not entry.strip():
            st.warning("Please write something before submitting.")
        else:
            template = PROMPT_VERSIONS[prompt_choice]
            user_prompt = f"{template}\n\nUser journal entry:\n\"\"\"\n{entry}\n\"\"\""
            try:
                raw = _chat_complete(user_prompt)
                data = _extract_json(raw)
                summary = (data.get("summary") or "").strip()
                reflection = (data.get("reflection") or "").strip()
                advice = (data.get("advice") or "").strip()

                # Render nicely
                st.markdown("### 🧾 Summary")
                st.write(summary or "_(Model did not return a summary.)_")
                st.markdown("### 💬 Reflection")
                st.write(reflection or "_(Model did not return a reflection.)_")
                st.markdown("### ✅ Advice for Tomorrow")
                st.write(advice or "_(Model did not return advice.)_")

                # Combine for storage in existing 'suggestion' column
                combined_html = f"""
                <div style='font-size:16px; line-height:1.6'>
                    <b>Summary:</b> {summary}<br><br>
                    <b>Reflection:</b> {reflection}<br><br>
                    <b>Advice:</b> {advice}
                </div>
                """

                # Save to DB (reuse entries schema; emotion set to 'mixed')
                DB["insert_entry"](datetime.now().strftime("%Y-%m-%d"), entry, "mixed", combined_html)

                # Log raw prompt/response
                DB["insert_runlog"](
                    timestamp=datetime.now().isoformat(timespec="seconds"),
                    prompt_version=prompt_choice,
                    model=model_name,
                    temperature=float(temperature),
                    max_tokens=int(max_tokens),
                    user_input=entry,
                    raw_request=user_prompt,
                    raw_response=raw
                )
                st.success("Saved entry and logged the session ✅")

            except Exception as e:
                st.error(f"Error generating reflection: {e}")
                if not api_key:
                    st.info("Add your OpenAI API key to Streamlit secrets as 'openai_api_key'.")

# ======================= PAGE: History =======================
elif page == "📜 History":
    st.subheader("📚 Your Journal History")
    rows = DB["get_all_entries"]()
    if not rows:
        st.info("No entries yet. Write your first entry on the “Write Journal” page.")
    else:
        df = pd.DataFrame(rows, columns=["Date", "Entry", "Emotion", "TherapistResponse"])
        df["Date"] = pd.to_datetime(df["Date"])
        df["WordCount"] = df["Entry"].apply(lambda x: len(str(x).split()))
        st.dataframe(df[["Date", "WordCount", "Emotion"]])

        # Trend: word count over time (proxy for engagement)
        st.subheader("🕒 Engagement Over Time (Word Count)")
        wc = df.groupby("Date")["WordCount"].mean().reset_index()
        fig = px.line(wc, x="Date", y="WordCount", markers=True, title="Average Word Count per Day")
        st.plotly_chart(fig)

        # Expand to view therapist responses
        st.subheader("🧠 View Saved Reflections")
        idx = st.selectbox("Pick an entry to view", list(range(len(df)))[::-1], format_func=lambda i: df.iloc[i]["Date"].strftime("%Y-%m-%d"))
        st.markdown(df.iloc[idx]["TherapistResponse"], unsafe_allow_html=True)

        # Export
        st.download_button(
            "⬇️ Export entries (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="journal_history.csv",
            mime="text/csv"
        )

# ======================= PAGE: Evaluate Outputs =======================
elif page == "🧪 Evaluate Outputs":
    st.subheader("🧪 Evaluation Dashboard")
    logs = DB["get_all_runlogs"]()
    if not logs:
        st.info("No logs yet. Generate a few entries on the Write Journal page.")
    else:
        logs_df = pd.DataFrame(logs, columns=[
            "timestamp","prompt_version","model","temperature","max_tokens",
            "user_input","raw_request","raw_response"
        ])
        st.dataframe(logs_df[["timestamp","prompt_version","model","temperature","user_input"]])

        # Auto-scores
        st.markdown("#### Auto-Scores (0–5): Empathy, Specificity, Actionability, Safety")
        rows = []
        for _, r in logs_df.iterrows():
            resp = str(r["raw_response"])
            ref = str(r["user_input"])
            rows.append({
                "timestamp": r["timestamp"],
                "prompt_version": r["prompt_version"],
                "Empathy": score_empathy(resp),
                "Specificity": score_specificity(resp, ref),
                "Actionability": score_actionability(resp),
                "Safety": score_safety(resp),
                "Notes": "Heuristic only."
            })
        scored = pd.DataFrame(rows)
        st.dataframe(scored)

        agg = scored.groupby("prompt_version")[["Empathy","Specificity","Actionability","Safety"]].mean().round(2).reset_index()
        st.markdown("#### Averages by Prompt Version")
        st.dataframe(agg)

        st.download_button(
            "⬇️ Export evaluation (CSV)",
            data=scored.to_csv(index=False).encode("utf-8"),
            file_name="evaluation_scores.csv",
            mime="text/csv"
        )
        st.info("Use these tables in your write-up to discuss output quality and prompt refinement.")

# ======================= PAGE: About =======================
elif page == "ℹ️ About":
    st.subheader("ℹ️ About This App")
    st.markdown("""
**Mental Health Diary (Therapist-style)** helps you:
- Write detailed, realistic daily entries (mixed emotions welcome)
- Receive a warm, therapist-like summary, reflection, and practical advice
- Track engagement over time and evaluate output quality for your class project

**Ethics & Safety**
- This app is **not** a medical device and does **not** provide clinical diagnosis.
- If you are in immediate danger or considering self-harm, contact local emergency services.
- In the U.S., call or text **988** (Suicide & Crisis Lifeline).

_Built with Streamlit + GPT-3.5._
""")
