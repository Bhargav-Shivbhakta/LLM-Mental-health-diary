import os
import re
import random
from dataclasses import dataclass
from typing import Dict, Tuple

import openai
import streamlit as st
import pandas as pd

# --- API KEY from Streamlit secrets ---
openai.api_key = st.secrets.get("openai_api_key", None)


# ================= PROMPT VERSIONS =================
PROMPT_VERSIONS: Dict[str, str] = {
    "v1 - basic empathetic reply": """
You are a supportive diary assistant. Given a user's journal entry, do:
1) Detect the primary emotion as ONE word from: [joy, sadness, anger, anxiety, fear, loneliness, stress, neutrality]
2) Provide a short, empathetic reflection (2-3 sentences).
3) Offer exactly one practical, low-effort tip.
Return JSON with keys: emotion, suggestion.
""".strip(),

    "v2 - add specificity + follow-up": """
You are a supportive diary assistant. For the journal entry:
1) Detect primary emotion from: [joy, sadness, anger, anxiety, fear, loneliness, stress, neutrality]
2) Provide a 2-3 sentence empathetic reflection that references 1–2 specific phrases from the user's text.
3) Offer one practical tip AND one micro-action the user can do in <5 minutes.
4) End with one gentle follow-up question.
Return JSON with keys: emotion, suggestion (HTML allowed), followup.
""".strip(),

    "v3 - safety-aware + culture-aware (English music option)": """
You are a supportive diary assistant with safety awareness. For the journal entry:
1) Detect primary emotion from: [joy, sadness, anger, anxiety, fear, loneliness, stress, neutrality]
2) Provide a 2-3 sentence empathetic reflection referencing 1–2 user phrases.
3) Offer one specific, practical tip AND one <5-min micro-action.
4) If mood is negative (not joy/neutrality), optionally suggest one English song (title – artist) relevant to mood.
5) If the entry indicates crisis (self-harm intent, plans, or immediate danger), add a short, compassionate crisis message:
   - Encourage seeking immediate professional help and contacting local emergency services.
   - In the U.S., mention 988 Suicide & Crisis Lifeline.
6) End with one gentle follow-up question.
Return JSON with keys: emotion, suggestion (HTML allowed), followup, crisis (boolean).
""".strip(),
}


# ================= English mood library =================
MUSIC_LIBRARY = {
    "anxiety": {
        "songs": ["Shake It Out – Florence + The Machine", "Breathe Me – Sia", "Fix You – Coldplay"],
        "quotes": [
            "You don’t have to control your thoughts. You just have to stop letting them control you. — Dan Millman",
            "Worrying doesn’t take away tomorrow’s troubles, it takes away today’s peace."
        ],
        "tips": [
            "Take 5 slow, deep breaths and count backwards from 10.",
            "Write down your anxious thoughts and challenge one of them.",
            "Listen to a calm song and stretch your body."
        ],
    },
    "sadness": {
        "songs": ["Let It Be – The Beatles", "Someone Like You – Adele", "Fix You – Coldplay"],
        "quotes": [
            "Tears are words that need to be written. — Paulo Coelho",
            "This too shall pass. — Persian Proverb"
        ],
        "tips": [
            "Reach out to someone you trust for a quick chat.",
            "Allow yourself to cry — it’s healing.",
            "Write down three small things you’re grateful for."
        ],
    },
    "joy": {
        "songs": ["Happy – Pharrell Williams", "Best Day of My Life – American Authors", "Good as Hell – Lizzo"],
        "quotes": [
            "Happiness is not something ready-made. It comes from your actions. — Dalai Lama",
            "The more you celebrate your life, the more there is to celebrate. — Oprah"
        ],
        "tips": [
            "Share your joy with someone else.",
            "Capture this moment in your journal or take a photo.",
            "Create a playlist of upbeat songs."
        ],
    },
    "anger": {
        "songs": ["Lose Yourself – Eminem", "Numb – Linkin Park", "Stronger – Kanye West"],
        "quotes": [
            "For every minute you are angry, you lose sixty seconds of happiness. — Emerson",
            "Speak when you are angry and you will make the best speech you will ever regret."
        ],
        "tips": [
            "Go for a walk or do a quick workout to release tension.",
            "Write down what made you angry, then rip the page.",
            "Take a deep breath before reacting."
        ],
    },
    "loneliness": {
        "songs": ["Fix You – Coldplay", "Lean On Me – Bill Withers", "See You Again – Wiz Khalifa ft. Charlie Puth"],
        "quotes": [
            "The eternal quest of the human being is to shatter his loneliness. — Norman Cousins",
            "You are never truly alone — you are always connected in ways you cannot see."
        ],
        "tips": [
            "Send a message to someone you miss.",
            "Join an online community or hobby group.",
            "Watch or listen to something that makes you smile."
        ],
    },
    "fear": {
        "songs": ["Brave – Sara Bareilles", "Fight Song – Rachel Platten", "Don’t Stop Believin’ – Journey"],
        "quotes": [
            "Do the thing you fear and the death of fear is certain. — Emerson",
            "Everything you want is on the other side of fear. — Jack Canfield"
        ],
        "tips": [
            "Write down what you’re afraid of and one tiny action you can take.",
            "Remind yourself of a time you overcame something tough.",
            "Take one deep breath and move forward."
        ],
    },
    "stress": {
        "songs": ["Weightless – Marconi Union", "Budapest – George Ezra", "Let It Go – James Bay"],
        "quotes": [
            "Almost everything will work again if you unplug it for a few minutes, including you. — Anne Lamott",
            "Slow down and everything you are chasing will come around and catch you. — Thich Nhat Hanh"
        ],
        "tips": [
            "Take a 5-minute break and stretch.",
            "Drink some water and breathe deeply.",
            "Focus on just one task — small wins reduce stress."
        ],
    },
    "neutrality": {
        "songs": ["Viva La Vida – Coldplay", "Riptide – Vance Joy", "Home – Edward Sharpe & The Magnetic Zeros"],
        "quotes": [
            "Contentment is not the fulfillment of what you want, but the realization of how much you already have.",
            "Small steps every day lead to big changes."
        ],
        "tips": [
            "Write one thing you appreciate today.",
            "Take a short walk and notice your surroundings.",
            "Try something new, even small — novelty lifts energy."
        ],
    },
}


# ================= Helper dataclass =================
@dataclass
class LLMRaw:
    request: str
    response: str


def _call_chat_completion(prompt: str, model: str, temperature: float, max_tokens: int) -> str:
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system",
             "content": "You are a concise, supportive mental-health diary assistant. Avoid clinical diagnosis."},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp["choices"][0]["message"]["content"]


def _extract_json(text: str) -> Dict:
    import json
    match = re.search(r"\{.*\}", text, re.DOTALL)
    blob = match.group(0) if match else "{}"
    try:
        return json.loads(blob)
    except Exception:
        return {"emotion": "neutrality", "suggestion": "", "followup": None, "crisis": False}


# ================= Main function =================
def analyze_emotion(
    text: str,
    prompt_version: str = "v1 - basic empathetic reply",
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.3,
    max_tokens: int = 600,
) -> Tuple[str, str, Dict]:
    if openai.api_key is None:
        st.error("Missing OpenAI API key.")
        return "Unknown", "Missing API key", {"request": "", "response": ""}

    template = PROMPT_VERSIONS.get(prompt_version, PROMPT_VERSIONS["v1 - basic empathetic reply"])
    user_prompt = f"{template}\n\nUser journal entry:\n\"\"\"\n{text}\n\"\"\""

    try:
        raw_text = _call_chat_completion(user_prompt, model, temperature, max_tokens)
        data = _extract_json(raw_text)

        emotion = (data.get("emotion") or "neutrality").strip().lower()
        suggestion_html = data.get("suggestion") or ""

        # Add follow-up if present
        followup = data.get("followup")
        if followup:
            suggestion_html += f"<br><br><i>{followup}</i>"

        # Crisis guardrail
        crisis = bool(data.get("crisis", False))
        if crisis:
            banner = (
                "<div style='border-left: 4px solid #e11; padding: 10px; margin: 10px 0;'>"
                "<b>If you are in immediate danger or considering self-harm:</b> "
                "Please reach out to local emergency services or call <b>988</b> (U.S. Suicide & Crisis Lifeline). "
                "This app is not a medical device.</div>"
            )
            suggestion_html = banner + suggestion_html

        # Fallback using English music library
        if not suggestion_html.strip():
            lib = MUSIC_LIBRARY.get(emotion, MUSIC_LIBRARY["neutrality"])
            song = random.choice(lib["songs"])
            quote = random.choice(lib["quotes"])
            tip = random.choice(lib["tips"])
            suggestion_html = f"""
            <div style='font-size:16px; line-height:1.6'>
                <b>🎧 Song:</b> {song}<br>
                <b>💬 Quote:</b> <i>{quote}</i><br>
                <b>✅ Tip:</b> {tip}
            </div>
            """

        raw = LLMRaw(request=user_prompt, response=raw_text).__dict__
        return emotion, suggestion_html, raw

    except Exception as e:
        st.error(f"Error analyzing emotion: {e}")
        return "Unknown", "Please try again later.", {"request": user_prompt, "response": str(e)}


# ================= Evaluation metrics =================
def _score_empathy(text: str) -> int:
    cues = ["I hear", "it sounds", "I understand", "valid", "makes sense", "I'm sorry", "glad"]
    return min(5, sum(1 for c in cues if c.lower() in text.lower()))

def _score_specificity(text: str, ref: str) -> int:
    hits = 0
    seen = set()
    for token in ref.lower().split():
        token = re.sub(r"[^a-z0-9]", "", token)
        if len(token) > 5 and token not in seen:
            seen.add(token)
            if token in text.lower():
                hits += 1
            if hits >= 5:
                break
    return min(5, 1 + hits)

def _score_actionability(text: str) -> int:
    cues = ["try ", "you can ", "set a timer", "write down", "breathe", "walk", "drink water", "journal", "call "]
    return min(5, 1 + sum(1 for c in cues if c in text.lower()))

def _score_safety(text: str) -> int:
    cues = ["not a medical device", "988", "seek immediate", "emergency", "crisis"]
    return min(5, 1 + sum(1 for c in cues if c in text.lower()))

def get_eval_scores(logs_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in logs_df.iterrows():
        resp = str(row.get("raw_response") or "")
        ref = str(row.get("user_input") or "")
        rows.append({
            "timestamp": row.get("timestamp"),
            "prompt_version": row.get("prompt_version"),
            "Empathy": _score_empathy(resp),
            "Specificity": _score_specificity(resp, ref),
            "Actionability": _score_actionability(resp),
            "Safety": _score_safety(resp),
            "Notes": "Auto-scored (heuristic)."
        })
    return pd.DataFrame(rows)
