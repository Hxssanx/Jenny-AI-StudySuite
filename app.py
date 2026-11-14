import os
import json
import re
import urllib.request
import urllib.parse
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from duckduckgo_search import DDGS
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()
client = Groq()

st.set_page_config(page_title="Jenny AI - Advanced Study Suite", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"], .stMarkdown, .stButton, input, textarea {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(14px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    .skeo-card {
        background: linear-gradient(145deg, #131b2e, #0f1626);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        margin-bottom: 20px;
        animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(145deg, #4f46e5, #4338ca);
        color: #ffffff;
        border-radius: 12px;
        border: none;
        padding: 0.65rem 1.2rem;
        font-weight: 600;
        letter-spacing: -0.01em;
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2);
        transition: all 0.25s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 28px rgba(79, 70, 229, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.3);
        background: linear-gradient(145deg, #6366f1, #4f46e5);
    }
    .stButton>button:active {
        transform: translateY(1px);
        box-shadow: 0 2px 10px rgba(79, 70, 229, 0.3), inset 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    section[data-testid="stSidebar"] {
        background-color: #0d1322 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stChatMessage"] {
        background: linear-gradient(145deg, #131b2e, #101728) !important;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.04);
        animation: slideUp 0.35s ease-out;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    [data-testid="stChatMessage"]:hover {
        border-color: rgba(99, 102, 241, 0.3);
        transform: translateX(4px);
    }
    div[role="radiogroup"] label {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        margin-bottom: 6px;
        transition: all 0.2s ease !important;
    }
    div[role="radiogroup"] label:hover {
        background: rgba(99, 102, 241, 0.08) !important;
        border-color: rgba(99, 102, 241, 0.4) !important;
        transform: translateX(4px);
    }
    .flashcard-box {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 16px;
        padding: 28px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        margin: 15px 0;
    }
    .app-title {
        font-size: 2.6rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #ffffff 30%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .app-subtitle {
        color: #64748b;
        font-size: 1rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

SYSTEM_PROMPT = (
    "Your name is Jenny. You are a fast, high-performance AI study assistant with live web search capabilities. "
    "STRICT RULE: Do NOT use any emojis anywhere in your output under any circumstances. "
    "Keep responses clean, clear, well-structured, and strictly professional."
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "flashcards_data" not in st.session_state:
    st.session_state.flashcards_data = None
if "card_index" not in st.session_state:
    st.session_state.card_index = 0
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

def search_web(query):
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            if results:
                context = "Live Web Search Results:\n"
                for r in results:
                    context += f"- Title: {r.get('title')}\n  Snippet: {r.get('body')}\n  URL: {r.get('href')}\n"
                return context
    except Exception as e:
        print(f"Search error: {e}")
    return ""

def extract_youtube_video_id(url):
    pattern = r'(?:v=|\/|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_youtube_study_material(video_id, url):
    transcript_text = None
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        for t in transcript_list:
            if t.language_code.startswith('en'):
                transcript_text = " ".join([x['text'] for x in t.fetch()])
                break
        if not transcript_text:
            for t in transcript_list:
                transcript_text = " ".join([x['text'] for x in t.fetch()])
                break
    except Exception as e:
        print(f"Transcript API skipped: {e}")
    if not transcript_text:
        try:
            oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url)}&format=json"
            req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                return f"YouTube Video Title: {data.get('title')}\nChannel: {data.get('author_name')}\nURL: {url}"
        except Exception as oembed_err:
            print(f"oembed fallback error: {oembed_err}")
    return transcript_text

def generate_interactive_quiz(topic, num_questions):
    prompt = (
        f"Create a {num_questions}-question multiple-choice quiz about: {topic}.\n"
        "Do NOT include any emojis anywhere in the response.\n"
        "Return ONLY a raw JSON array of objects with NO markdown formatting, NO backticks, and NO code blocks.\n"
        "Each object must have these exact keys:\n"
        "- \"question\": string\n"
        "- \"options\": list of 4 strings\n"
        "- \"answer\": string (must match one of the options exactly)\n"
        "- \"explanation\": string"
    )
    try:
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content.rsplit("\n", 1)[0]
        return json.loads(content.strip())
    except Exception as e:
        st.error(f"Failed to parse quiz data: {e}")
        return None

def generate_flashcards(topic, num_cards=5):
    prompt = (
        f"Create a deck of {num_cards} study flashcards about: {topic}.\n"
        "Do NOT include any emojis anywhere in the response.\n"
        "Return ONLY a raw JSON array of objects with NO markdown formatting, NO backticks, and NO code blocks.\n"
        "Each object must have these exact keys:\n"
        "- \"front\": string (Question or Concept)\n"
        "- \"back\": string (Detailed Explanation or Answer)"
    )
    try:
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content.rsplit("\n", 1)[0]
        return json.loads(content.strip())
    except Exception as e:
        st.error(f"Failed to parse flashcard data: {e}")
        return None

with st.sidebar:
    st.markdown("<h2 style='margin-bottom:0; color: #f3f4f6;'>Jenny AI</h2>", unsafe_allow_html=True)
    st.caption("Advanced Study Engine")
    st.markdown("---")
    st.subheader("Interactive Quiz Generator")
    quiz_topic = st.text_input("Quiz Topic:", placeholder="e.g. Quantum Computing")
    num_q = st.select_slider("Questions:", options=[3, 5, 10], value=5)
    if st.button("Build Interactive Quiz"):
        if quiz_topic.strip():
            with st.spinner("Generating quiz..."):
                quiz_json = generate_interactive_quiz(quiz_topic, num_q)
                if quiz_json:
                    st.session_state.quiz_data = quiz_json
                    st.success("Quiz loaded successfully.")
        else:
            st.warning("Please enter a topic first.")
    st.markdown("---")
    st.subheader("Interactive Flashcards")
    fc_topic = st.text_input("Flashcard Topic:", placeholder="e.g. Cell Biology")
    if st.button("Build Flashcard Deck"):
        if fc_topic.strip():
            with st.spinner("Building flashcards..."):
                fc_json = generate_flashcards(fc_topic)
                if fc_json:
                    st.session_state.flashcards_data = fc_json
                    st.session_state.card_index = 0
                    st.session_state.show_answer = False
                    st.success("Flashcards ready.")
        else:
            st.warning("Please enter a topic first.")
    st.markdown("---")
    if st.button("Clear Workspace"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.quiz_data = None
        st.session_state.flashcards_data = None
        st.rerun()

st.markdown("<div class='app-title'>Jenny AI Suite</div>", unsafe_allow_html=True)
st.markdown("<div class='app-subtitle'>High-speed study companion with live web search, document digestion, YouTube notes, and interactive test suites.</div>", unsafe_allow_html=True)

with st.expander("Upload Notes or Process YouTube Link for Enhanced Study Notes"):
    tab1, tab2 = st.tabs(["Upload Document / Raw Notes", "YouTube Video Link"])
    with tab1:
        uploaded_file = st.file_uploader("Upload text or markdown notes:", type=["txt", "md"])
        raw_text_notes = st.text_area("Or paste raw study notes directly:", height=100)
        if st.button("Generate Enhanced Notes from Document"):
            text_content = ""
            if uploaded_file:
                text_content = uploaded_file.read().decode("utf-8")
            elif raw_text_notes.strip():
                text_content = raw_text_notes.strip()
            if text_content:
                prompt = f"Analyze the following study notes and transform them into structured, comprehensive, high-yield study material with key takeaways and definitions:\n\n{text_content}"
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.rerun()
            else:
                st.warning("Please upload or paste notes first.")
    with tab2:
        yt_url = st.text_input("Paste YouTube Video URL:")
        if st.button("Process YouTube Video"):
            if yt_url.strip():
                v_id = extract_youtube_video_id(yt_url)
                if v_id:
                    with st.spinner("Processing video content and generating study notes..."):
                        material = get_youtube_study_material(v_id, yt_url)
                        if material:
                            trimmed_material = material[:12000]
                            prompt = f"Here is the data extracted from a study video link. Analyze it, break down the core concepts, provide detailed explanations, and create clean, high-yield study notes:\n\n{trimmed_material}"
                            st.session_state.messages.append({"role": "user", "content": prompt})
                            st.rerun()
                        else:
                            st.error("Could not fetch information for this video. Try a different video link.")
                else:
                    st.error("Invalid YouTube URL format.")

if st.session_state.flashcards_data:
    st.markdown("<div class='skeo-card'>", unsafe_allow_html=True)
    st.markdown("### Interactive Flashcards Deck")
    total_cards = len(st.session_state.flashcards_data)
    current_idx = st.session_state.card_index
    card = st.session_state.flashcards_data[current_idx]
    st.caption(f"Card {current_idx + 1} of {total_cards}")
    if not st.session_state.show_answer:
        st.markdown(f"<div class='flashcard-box'><h4 style='color:#94a3b8;'>QUESTION</h4><h3>{card['front']}</h3></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='flashcard-box'><h4 style='color:#818cf8;'>ANSWER</h4><h3>{card['back']}</h3></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Previous Card") and current_idx > 0:
            st.session_state.card_index -= 1
            st.session_state.show_answer = False
            st.rerun()
    with col2:
        if st.button("Flip Card"):
            st.session_state.show_answer = not st.session_state.show_answer
            st.rerun()
    with col3:
        if st.button("Next Card") and current_idx < total_cards - 1:
            st.session_state.card_index += 1
            st.session_state.show_answer = False
            st.rerun()
    if st.button("Close Flashcards"):
        st.session_state.flashcards_data = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.quiz_data:
    st.markdown("<div class='skeo-card'>", unsafe_allow_html=True)
    st.markdown("### Interactive Knowledge Check")
    with st.form("interactive_quiz_form"):
        user_answers = {}
        for idx, q in enumerate(st.session_state.quiz_data):
            st.markdown(f"**Q{idx+1}: {q['question']}**")
            user_answers[idx] = st.radio(
                f"Select answer for Question {idx+1}:", 
                q["options"], 
                key=f"q_{idx}",
                label_visibility="collapsed"
            )
            st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Submit and Grade Answers")        
        if submitted:
            score = 0
            total = len(st.session_state.quiz_data)
            for idx, q in enumerate(st.session_state.quiz_data):
                selected = user_answers[idx]
                correct = q["answer"]  
                if selected == correct:
                    score += 1
                    st.success(f"Q{idx+1}: Correct. ({selected})")
                else:
                    st.error(f"Q{idx+1}: Incorrect. Your pick: {selected} | Correct: {correct}")
                st.info(f"Explanation: {q['explanation']}")          
            st.markdown(f"### Final Score: {score} / {total}")
    if st.button("Close Quiz Window"):
        st.session_state.quiz_data = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("### Live Assistant Chat")
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask Jenny anything or request study help..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        try:
            search_context = search_web(prompt)
            api_messages = list(st.session_state.messages)
            if search_context:
                api_messages.insert(-1, {"role": "system", "content": search_context})
            completion = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=api_messages,
                max_tokens=800,
                stream=True
            )
            for chunk in completion:
                content = chunk.choices[0].delta.content or ""
                full_response += content
                response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"Error: {e}")
