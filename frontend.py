import streamlit as st
import requests

# Page configuration
st.set_page_config(
    page_title="TaazaKhabar",
    page_icon="🥷",
    layout="wide"
)

# Backend URL
BACKEND_URL = "http://localhost:1234"

# Custom CSS for better styling
st.markdown("""
    <style>
        .main-title {
            font-size: 2.2rem !important;
            font-weight: 700;
            color: #222;
            text-align: center;
        }
        .topic-chip {
            display: inline-block;
            background-color: #f0f2f6;
            padding: 6px 12px;
            border-radius: 20px;
            margin: 4px;
            font-size: 0.9rem;
        }
        .stButton>button {
            border-radius: 12px !important;
            font-weight: 600 !important;
        }
        .audio-card {
            background: #f9fafc;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
            margin-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown("<h1 class='main-title'>📰 TaazaKhabar</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>AI-powered news & Reddit audio summaries</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Initialize session state
    if 'topics' not in st.session_state:
        st.session_state.topics = []
    if 'input_counter' not in st.session_state:
        st.session_state.input_counter = 0

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        source_type = st.selectbox(
            "Source:",
            ["both", "news", "reddit"],
            format_func=lambda x: {
                "both": "⚡ News + Reddit", 
                "news": "📜 News only", 
                "reddit": "👥 Reddit only"
            }[x]
        )
        
        st.info("💡 Try: 'AI', 'Climate Change', 'Space News'")

        with st.expander("ℹ️ About"):
            st.write("TaazaKhabar scrapes trending topics, analyzes discussions, and generates audio news summaries using AI.")

    # Add topics section

    st.subheader("➕ Add Topics")

    # Use columns to align input + button properly
    col1, col2 = st.columns([4, 1])

    with col1:
        new_topic = st.text_input("Enter a topic:", placeholder="E.g. Artificial Intelligence...", label_visibility="collapsed")

    with col2:
        add_clicked = st.button("Add", use_container_width=True)

    if add_clicked and new_topic.strip():
        if "topics" not in st.session_state:
            st.session_state.topics = []
        st.session_state.topics.append(new_topic.strip())
        st.rerun()

    # Progress bar for topic count
    st.progress(len(st.session_state.topics) / 3)

    # Show current topics
    # Show current topics
    if st.session_state.topics:
        st.subheader("📌 Your Topics")

        for i, topic in enumerate(st.session_state.topics):
            col1, col2 = st.columns([8, 1])
            with col1:
                st.markdown(
                    f"<div style='background:#e6f0ff;padding:6px 14px;border-radius:20px;"
                    f"display:inline-block;font-size:0.95rem;font-weight:500;color:#1a1a1a;'>"
                    f"{topic}</div>",
                    unsafe_allow_html=True
                )
            with col2:
                if st.button("✖", key=f"remove_{i}", help="Remove this topic"):
                    st.session_state.topics.pop(i)
                    st.rerun()


    st.markdown("---")

    # Generate button
    st.subheader("🚀 Generate Summary")

    if not st.session_state.topics:
        st.info("⚠️ Add at least one topic to continue")
        generate_disabled = True
    else:
        generate_disabled = False

    if st.button("🎧 Generate Audio Summary", disabled=generate_disabled, type="primary", use_container_width=True):
        with st.spinner("🥷 Mixing ninja news... please wait"):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/generate-news-audio",
                    json={
                        "topics": st.session_state.topics,
                        "source_type": source_type
                    }
                )

                if response.status_code == 200:
                    st.markdown("### ✅ Your Summary is Ready!")
                    with st.container():
                        st.markdown("<div class='audio-card'>", unsafe_allow_html=True)
                        st.audio(response.content, format="audio/mpeg")
                        st.download_button(
                            "⬇️ Download Audio",
                            data=response.content,
                            file_name="summary.mp3",
                            mime="audio/mpeg",
                            use_container_width=True
                        )
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.error(f"Error: {response.status_code}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Can't connect to server. Is it running on localhost:1234?")
            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")

if __name__ == "__main__":
    main()