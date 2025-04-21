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

        # Enhanced suggestion system
        mood_data = {
            "Anxious": {
                "songs": ["Weightless - Marconi Union", "Let It Be - The Beatles", "Breathe Me - Sia"],
                "quotes": [
                    "You don’t have to control your thoughts. You just have to stop letting them control you. — Dan Millman",
                    "Feelings are much like waves, we can’t stop them from coming but we can choose which one to surf."
                ],
                "tips": [
                    "Try deep breathing like athletes before a match.",
                    "Listen to calming instrumental music.",
                    "Stretch or go for a light jog to reset your mind."
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
                    "Draw, journal, or express how you feel through music.",
                    "Reach out to someone. You're not alone."
                ]
            },
            "Happy": {
                "songs": ["Happy - Pharrell Williams", "Can't Stop the Feeling - Justin Timberlake", "Good as Hell - Lizzo"],
                "quotes": [
                    "Happiness is not something ready-made. It comes from your own actions. — Dalai Lama",
                    "The more you praise and celebrate your life, the more there is in life to celebrate."
                ],
                "tips": [
                    "Celebrate a small win with music or movement.",
                    "Smile at someone or send a positive message.",
                    "Play a favorite song and dance!"
                ]
            },
            "Angry": {
                "songs": ["Numb - Linkin Park", "Lose Yourself - Eminem", "Believer - Imagine Dragons"],
                "quotes": [
                    "Speak when you are angry – and you’ll make the best speech you’ll ever regret.",
                    "Anger doesn’t solve anything. It builds nothing, but it can destroy everything."
                ],
                "tips": [
                    "Do 10 jumping jacks to release tension.",
                    "Write it out, don’t act it out.",
                    "Use art or sports to channel frustration."
                ]
            },
            "Lonely": {
                "songs": ["Talking to the Moon - Bruno Mars", "All by Myself - Celine Dion", "Lovely - Billie Eilish"],
                "quotes": [
                    "The best way to cheer yourself is to try to cheer someone else up.",
                    "You are never alone. You are eternally connected with everyone. — Amit Ray"
                ],
                "tips": [
                    "Send a meme or voice note to a friend.",
                    "Watch a virtual concert or event.",
                    "Start a creative hobby today."
                ]
            }
        }

        data = mood_data.get(emotion.capitalize(), mood_data["Happy"])
        song = random.choice(data["songs"])
        quote = random.choice(data["quotes"])
        tip = random.choice(data["tips"])

        suggestion = f"🎧 **Song Suggestion:** {song}\\n💬 **Quote:** _{quote}_\\n✅ **Tip:** {tip}"
        return emotion, suggestion

    except Exception as e:
        st.error(f"Error analyzing emotion: {e}")
        return "Unknown", "Please try again later."
