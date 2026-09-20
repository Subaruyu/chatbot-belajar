import os
import streamlit as st
from google import genai
from google.genai import types

NAMA_APP = "KIRANA"
LOGO = "logo.jpg"
MODEL = "gemini-flash-latest"

ada_logo = os.path.exists(LOGO)
st.set_page_config(page_title=NAMA_APP, page_icon=LOGO if ada_logo else EMOJI)
if ada_logo:
    st.logo(LOGO)

st.markdown("""
<style>
[data-testid="stChatMessage"] {
    background: #111B2E; border: 1px solid #1F3358;
    border-radius: 16px; padding: 12px 16px;
    box-shadow: 0 0 12px rgba(59,130,246,0.15); margin-bottom: 8px;
}
.stButton > button {
    background: #111B2E; color: #E6EEF9;
    border: 1px solid #1F3358; border-radius: 12px;
    width: 100%; text-align: left;
}
.stButton > button:hover { border-color: #3B82F6; color: #3B82F6; }
h1 { color: #60A5FA; }
[data-testid="stAppDeployButton"], .stAppDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    api_key = st.sidebar.text_input("Gemini API Key", type="password")
    if not api_key:
        st.info("Masukkan API key di sidebar untuk mulai.")
        st.stop()


def buat_judul(client, pertanyaan, jawaban):
    try:
        r = client.models.generate_content(
            model=MODEL,
            contents=(
                "Buat judul singkat (maksimal 4 kata, tanpa tanda kutip, "
                "tanpa titik) untuk percakapan ini.\n"
                f"Pertanyaan: {pertanyaan}\nJawaban: {jawaban[:300]}\n"
                "Balas hanya dengan judulnya."
            ),
        )
        judul = (r.text or "").strip().strip('"').strip("*").strip()
        return judul[:30] if judul else pertanyaan[:28]
    except Exception:
        return pertanyaan[:28]


if "chats" not in st.session_state:
    st.session_state.chats = [{"title": "Chat baru", "messages": []}]
    st.session_state.active = 0


def hapus_chat(i):
    aktif = st.session_state.active
    st.session_state.chats.pop(i)
    if not st.session_state.chats:
        st.session_state.chats = [{"title": "Chat baru", "messages": []}]
        aktif = 0
    elif i < aktif:
        aktif -= 1
    st.session_state.active = min(aktif, len(st.session_state.chats) - 1)


with st.sidebar:
    if st.button("➕ Chat baru"):
        st.session_state.chats.append({"title": "Chat baru", "messages": []})
        st.session_state.active = len(st.session_state.chats) - 1
        st.rerun()

    cari = st.text_input("🔍 Cari riwayat", placeholder="Cari judul atau isi chat...")
    st.markdown("**Riwayat**")

    kata = cari.strip().lower()
    ada_hasil = False
    for i, c in enumerate(st.session_state.chats):
        if kata:
            isi = " ".join(m["content"] for m in c["messages"]).lower()
            if kata not in c["title"].lower() and kata not in isi:
                continue
        ada_hasil = True
        tanda = "🔵 " if i == st.session_state.active else ""
        kiri, kanan = st.columns([5, 1])
        if kiri.button(tanda + c["title"], key=f"chat{i}"):
            st.session_state.active = i
            st.rerun()
        if kanan.button("🗑️", key=f"hapus{i}"):
            hapus_chat(i)
            st.rerun()
    if kata and not ada_hasil:
        st.caption("Tidak ada chat yang cocok.")

    if st.button("🧹 Hapus semua riwayat"):
        st.session_state.chats = [{"title": "Chat baru", "messages": []}]
        st.session_state.active = 0
        st.rerun()

chat = st.session_state.chats[st.session_state.active]

judul_kol, ulang_kol, hapus_kol = st.columns([8, 1, 1])
with judul_kol:
    if ada_logo:
        st.image(LOGO, width=90)
    st.title(NAMA_APP)
with ulang_kol:
    if st.button("🔄", key="ulang", help="Muat ulang halaman"):
        st.rerun()
with hapus_kol:
    if st.button("🗑️", key="hapus_aktif", help="Hapus chat ini"):
        hapus_chat(st.session_state.active)
        st.rerun()

st.caption("Tanya apa saja soal pelajaran, aku jelaskan dengan bahasa sederhana.")

for m in chat["messages"]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Tulis pertanyaanmu di sini..."):
    pertama = len(chat["messages"]) == 0
    chat["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = genai.Client(api_key=api_key)
    history = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part(text=m["content"])],
        )
        for m in chat["messages"]
    ]
    try:
        with st.spinner("Sedang berpikir..."):
            response = client.models.generate_content(
                model=MODEL,
                contents=history,
                config=types.GenerateContentConfig(
                    system_instruction="Kamu adalah KIRANA, asisten belajar yang ramah untuk pelajar. Jawab dalam bahasa Indonesia yang sederhana, beri contoh, dan singkat."
                ),
            )
        with st.chat_message("assistant"):
            st.markdown(response.text)
        chat["messages"].append({"role": "assistant", "content": response.text})
        if pertama:
            chat["title"] = buat_judul(client, prompt, response.text)
            st.rerun()
    except Exception:
        chat["messages"].pop()
        st.warning("Server AI sedang sibuk, coba kirim ulang sebentar lagi ya 🙏")