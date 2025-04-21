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
