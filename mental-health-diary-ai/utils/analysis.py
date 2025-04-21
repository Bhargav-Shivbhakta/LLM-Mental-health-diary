import openai
import streamlit as st

openai.api_key = st.secrets.get("openai_api_key", None)

def analyze_emotion(text):
    if openai.api_key is None:
        st.error("Missing OpenAI API key.")
        return "Unknown", "Missing API key"

    prompt = f"""
    Analyze the emotional tone of the following journal entry and respond in this format:
    Emotion: <One word emotion>
    Suggestion: <Short motivational advice>

    Entry:
    \"\"\"{text}\"\"\"
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that detects emotions and gives supportive advice."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=100
        )

        content = response['choices'][0]['message']['content']
        lines = content.strip().splitlines()
        emotion = lines[0].split(":")[1].strip()
        suggestion = lines[1].split(":")[1].strip()
        return emotion, suggestion

    except Exception as e:
        st.error(f"Error analyzing emotion: {e}")
        return "Unknown", "Please try again later."

import random

# Mood-based song, quote, and tip generator
mood_data = {
    "Anxious": {
        "songs": ["Weightless - Marconi Union", "Someone Like You - Adele", "Let It Be - The Beatles"],
        "quotes": [
            "You don’t have to control your thoughts. You just have to stop letting them control you. — Dan Millman",
            "Slow breathing is like an anchor in the midst of an emotional storm."
        ],
        "tips": [
            "Try deep breathing for 2 minutes.",
            "Play calming instrumental music.",
            "Go for a short walk or stretch like an athlete before a game."
        ]
    },
    "Sad": {
        "songs": ["Fix You - Coldplay", "Jealous - Labrinth", "River Flows in You - Yiruma"],
        "quotes": [
            "Stars can’t shine without darkness.",
            "This too shall pass. — Persian Proverb"
        ],
        "tips": [
            "Write down 3 things you're grateful for.",
            "Talk to a friend or listen to comforting music.",
            "Watch a feel-good movie or game highlights."
        ]
    },
    "Happy": {
        "songs": ["Happy - Pharrell Williams", "Can't Stop the Feeling - Justin Timberlake", "Good as Hell - Lizzo"],
        "quotes": [
            "Happiness is not something ready-made. It comes from your own actions. — Dalai Lama",
            "The more you praise and celebrate your life, the more there is in life to celebrate."
        ],
        "tips": [
            "Share your smile with someone else today.",
            "Create a playlist for your happy days.",
            "Celebrate small wins like athletes do."
        ]
    },
    "Angry": {
        "songs": ["Numb - Linkin Park", "Lose Yourself - Eminem", "Believer - Imagine Dragons"],
        "quotes": [
            "Speak when you are angry – and you’ll make the best speech you’ll ever regret.",
            "Anger doesn’t solve anything. It builds nothing, but it can destroy everything."
        ],
        "tips": [
            "Punch a pillow or do 10 push-ups to release energy.",
            "Channel it into writing, drumming, or drawing.",
            "Play fast-paced music and dance it out."
        ]
    },
    "Lonely": {
        "songs": ["Talking to the Moon - Bruno Mars", "All by Myself - Celine Dion", "Lovely - Billie Eilish"],
        "quotes": [
            "The best way to cheer yourself is to try to cheer someone else up.",
            "You are never alone. You are eternally connected with everyone. — Amit Ray"
        ],
        "tips": [
            "Call or text someone you miss.",
            "Watch a concert or sports event livestream.",
            "Start a creative hobby — journaling, art, music."
        ]
    }
}

# Safely select from mood data
data = mood_data.get(emotion.capitalize(), mood_data["Happy"])  # Fallback to Happy

song = random.choice(data["songs"])
quote = random.choice(data["quotes"])
tip = random.choice(data["tips"])

# Build improved suggestion
suggestion = f"🎧 **Song Suggestion:** {song}\n💬 **Quote:** _{quote}_\n✅ **Tip:** {tip}"

