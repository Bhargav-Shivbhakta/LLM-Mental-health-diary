import openai
import streamlit as st
import random

openai.api_key = st.secrets.get("openai_api_key", None)

def analyze_emotion(text):
    if openai.api_key is None:
        st.error("Missing OpenAI API key.")
        return "Unknown", "Missing API key"

    prompt = f"""
    Analyze the emotional tone of the following journal entry and respond in this format:
    Emotion: <One word emotion>

    Entry:
    \"\"\"{text}\"\"\"
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that detects emotions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=100
        )

        content = response['choices'][0]['message']['content']
        lines = content.strip().splitlines()
        emotion = lines[0].split(":")[1].strip()

        # Refined Hindi mood dataset
        mood_data = {
            "Anxious": {
                "songs": ["Zinda – Bhaag Milkha Bhaag", "Besabriyaan – MS Dhoni", "Phir Se Ud Chala – Rockstar"],
                "quotes": [
                    "Worrying doesn’t take away tomorrow’s troubles, it takes away today’s peace.",
                    "Calm mind brings inner strength and self-confidence. — Dalai Lama"
                ],
                "tips": [
                    "Close your eyes and take 5 slow, deep breaths.",
                    "Listen to a calm Hindi track and stretch your body.",
                    "Write down what’s stressing you — then let it go."
                ]
            },
            "Sad": {
                "songs": ["Channa Mereya – Ae Dil Hai Mushkil", "Agar Tum Saath Ho – Tamasha", "Tujhse Naraz Nahi – Masoom"],
                "quotes": [
                    "This too shall pass. — Persian Proverb",
                    "Tears are words that the heart can’t say."
                ],
                "tips": [
                    "Call or message someone you trust.",
                    "Write your feelings in a safe place.",
                    "Let your emotions flow with a meaningful song."
                ]
            },
            "Happy": {
                "songs": ["Ilahi – YJHD", "Gallan Goodiyan – Dil Dhadakne Do", "Ude Dil Befikre"],
                "quotes": [
                    "The more you celebrate your life, the more there is to celebrate. — Oprah",
                    "Happiness is not ready-made. It comes from your actions. — Dalai Lama"
                ],
                "tips": [
                    "Capture this moment in a photo or journal.",
                    "Share a compliment or smile with someone.",
                    "Make a playlist of songs that match your mood!"
                ]
            },
            "Angry": {
                "songs": ["Sultan – Title Track", "Ziddi Dil – Mary Kom", "Khoon Chala – Rang De Basanti"],
                "quotes": [
                    "Anger is one letter short of danger.",
                    "Speak when you are angry and you will make the best speech you will ever regret."
                ],
                "tips": [
                    "Do a quick workout or shadow box to burn off steam.",
                    "Write what made you angry, then tear it up.",
                    "Channel it into music or drawing."
                ]
            },
            "Lonely": {
                "songs": ["Tera Yaar Hoon Main", "Kabira", "Mann Bharryaa"],
                "quotes": [
                    "You are never truly alone. You are always connected in ways you cannot see.",
                    "Loneliness is a sign you are in desperate need of yourself."
                ],
                "tips": [
                    "Join an online group or virtual event.",
                    "Message someone even if you haven’t talked in a while.",
                    "Listen to a soul-touching Hindi song and let yourself feel."
                ]
            }
        }

        # Handle unexpected emotion values
        data = mood_data.get(emotion.capitalize(), mood_data["Happy"])

        song = random.choice(data["songs"])
        quote = random.choice(data["quotes"])
        tip = random.choice(data["tips"])

        # Cleaner formatted suggestion
        suggestion = f"""
        <div style='font-size:16px; line-height:1.6'>
            <b>🎧 Hindi Song:</b> {song}<br>
            <b>💬 Quote:</b> <i>{quote}</i><br>
            <b>✅ Tip:</b> {tip}
        </div>
        """

        return emotion, suggestion

    except Exception as e:
        st.error(f"Error analyzing emotion: {e}")
        return "Unknown", "Please try again later."
