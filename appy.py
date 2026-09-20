import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Asisten Belajar", page_icon="📚")
st.title("📚 Asisten Belajar")
st.caption("Tanya apa saja soal pelajaran, aku jelaskan dengan bahasa sederhana.")

api_key = st.sidebar.text_input("Gemini API Key", type="password")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Tulis pertanyaanmu di sini..."):
    if not api_key:
        st.warning("Masukkan API key di sidebar dulu ya.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = genai.Client(api_key=api_key)
    history = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part(text=m["content"])],
        )
        for m in st.session_state.messages
    ]
    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=history,
        config=types.GenerateContentConfig(
            system_instruction="Kamu asisten belajar yang ramah untuk pelajar. Jawab dalam bahasa Indonesia yang sederhana, beri contoh, dan singkat."
        ),
    )

    with st.chat_message("assistant"):
        st.markdown(response.text)
    st.session_state.messages.append({"role": "assistant", "content": response.text})