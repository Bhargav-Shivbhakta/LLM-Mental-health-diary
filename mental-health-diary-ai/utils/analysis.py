import openai
import streamlit as st

def analyze_emotion(text):
    try:
        api_key = st.secrets["openai_api_key"]
    except KeyError:
        st.error("API key not found. Please add `openai_api_key` to your Streamlit secrets.")
        return "Unknown", "OpenAI key missing. Add it to Streamlit secrets."

    client = openai.OpenAI(api_key=api_key)

    prompt = f"""
    Analyze the emotional tone of the following journal entry and respond in this format:
    Emotion: <One word emotion>
    Suggestion: <Short motivational advice>

    Entry:
    \"\"\"{text}\"\"\"
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that detects emotions and gives supportive advice."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=100
        )

        content = response.choices[0].message.content
        lines = content.splitlines()
        emotion = lines[0].split(":")[1].strip()
        suggestion = lines[1].split(":")[1].strip()
        return emotion, suggestion

    except Exception as e:
        st.error(f"Error analyzing emotion: {e}")
        return "Unknown", "Please try again later."
