import streamlit as st

from config import (
    APP_NAME,
    OLLAMA_MODEL
)

from modules.rag_engine import (
    process_uploaded_files,
    answer_question,
    get_document_names,
    get_collection
)

from modules.chat_store import (
    load_chat_history,
    save_chat_history,
    clear_chat_history
)

from modules.study_tools import (
    generate_summary,
    generate_quiz,
    generate_flashcards,
    generate_important_questions
)


st.set_page_config(
    page_title=APP_NAME,
    page_icon="📚",
    layout="wide"
)


if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()


if "study_output" not in st.session_state:
    st.session_state.study_output = ""


st.sidebar.title("📚 EduMentor AI")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "📂 Study Materials",
        "💬 Chat With Notes",
        "📝 Summary",
        "❓ Quiz",
        "🧠 Flashcards",
        "🎯 Important Questions",
        "ℹ️ About"
    ]
)

st.sidebar.divider()

ollama_model = st.sidebar.text_input(
    "Ollama Model",
    value=OLLAMA_MODEL
)


def available_documents():
    names = get_document_names()

    if not names:
        return ["No Documents"]

    return ["All Documents"] + names


if page == "🏠 Home":

    st.title("📚 EduMentor AI")
    st.subheader(
        "Your Personal AI Study Assistant"
    )

    st.write(
        "Upload your notes and use AI to study them."
    )

    collection = get_collection()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Documents",
        len(get_document_names())
    )

    col2.metric(
        "Study Sections",
        collection.count()
    )

    col3.metric(
        "Chat Messages",
        len(st.session_state.messages)
    )


elif page == "📂 Study Materials":

    st.title("📂 Study Materials")

    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type=["pdf"],
        accept_multiple_files=True
    )

    if st.button(
        "🚀 Process Study Materials",
        type="primary"
    ):

        if not uploaded_files:
            st.warning(
                "Please select at least one PDF."
            )

        else:
            with st.spinner(
                "Processing PDFs..."
            ):
                files, chunk_count = (
                    process_uploaded_files(
                        uploaded_files
                    )
                )

            if chunk_count == 0:
                st.error(
                    "No readable PDF text found."
                )

            else:
                st.success(
                    "Study materials processed."
                )

                st.write(
                    f"{chunk_count} study sections created."
                )

                for item in files:
                    st.write(
                        f"✅ {item['name']} "
                        f"— {item['pages']} pages"
                    )

    st.subheader(
        "Current Knowledge Base"
    )

    for name in get_document_names():
        st.write(
            f"📄 {name}"
        )


elif page == "💬 Chat With Notes":

    st.title("💬 Chat With Notes")

    documents = available_documents()

    selected_source = st.selectbox(
        "Study material",
        documents
    )

    for message in st.session_state.messages:
        with st.chat_message(
            message["role"]
        ):
            st.markdown(
                message["content"]
            )

    question = st.chat_input(
        "Ask something about your notes..."
    )

    if question:

        st.session_state.messages.append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):

            with st.spinner(
                "Searching your notes..."
            ):

                answer, chunks = (
                    answer_question(
                        question=question,
                        selected_source=selected_source,
                        model=ollama_model,
                        chat_history=(
                            st.session_state.messages
                        )
                    )
                )

            st.markdown(answer)

            if chunks:
                with st.expander(
                    "📖 Sources used"
                ):
                    shown = set()

                    for chunk in chunks:
                        key = (
                            chunk["source"],
                            chunk["page"]
                        )

                        if key not in shown:
                            shown.add(key)

                            st.write(
                                f"📄 {chunk['source']} "
                                f"— Page {chunk['page']}"
                            )

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        save_chat_history(
            st.session_state.messages
        )

    if st.button(
        "🗑️ Clear Chat History"
    ):
        st.session_state.messages = []
        clear_chat_history()
        st.rerun()


elif page == "📝 Summary":

    st.title("📝 Summary Generator")

    source = st.selectbox(
        "Select study material",
        available_documents()
    )

    summary_type = st.selectbox(
        "Summary type",
        [
            "Short",
            "Detailed",
            "Exam Revision",
            "Bullet Point"
        ]
    )

    if st.button(
        "Generate Summary",
        type="primary"
    ):

        with st.spinner(
            "Generating summary..."
        ):
            st.session_state.study_output = (
                generate_summary(
                    source,
                    summary_type,
                    ollama_model
                )
            )

    if st.session_state.study_output:
        st.markdown(
            st.session_state.study_output
        )


elif page == "❓ Quiz":

    st.title("❓ Quiz Generator")

    source = st.selectbox(
        "Select study material",
        available_documents()
    )

    number = st.slider(
        "Number of questions",
        3,
        15,
        5
    )

    difficulty = st.selectbox(
        "Difficulty",
        [
            "Easy",
            "Medium",
            "Hard"
        ]
    )

    if st.button(
        "Generate Quiz",
        type="primary"
    ):

        with st.spinner(
            "Generating quiz..."
        ):

            st.session_state.study_output = (
                generate_quiz(
                    source,
                    number,
                    difficulty,
                    ollama_model
                )
            )

    if st.session_state.study_output:
        st.markdown(
            st.session_state.study_output
        )


elif page == "🧠 Flashcards":

    st.title("🧠 Flashcards")

    source = st.selectbox(
        "Select study material",
        available_documents()
    )

    number = st.slider(
        "Number of flashcards",
        5,
        20,
        10
    )

    if st.button(
        "Generate Flashcards",
        type="primary"
    ):

        with st.spinner(
            "Generating flashcards..."
        ):

            st.session_state.study_output = (
                generate_flashcards(
                    source,
                    number,
                    ollama_model
                )
            )

    if st.session_state.study_output:
        st.markdown(
            st.session_state.study_output
        )


elif page == "🎯 Important Questions":

    st.title(
        "🎯 Important Questions"
    )

    source = st.selectbox(
        "Select study material",
        available_documents()
    )

    if st.button(
        "Generate Important Questions",
        type="primary"
    ):

        with st.spinner(
            "Generating questions..."
        ):

            st.session_state.study_output = (
                generate_important_questions(
                    source,
                    ollama_model
                )
            )

    if st.session_state.study_output:
        st.markdown(
            st.session_state.study_output
        )


elif page == "ℹ️ About":

    st.title("ℹ️ About EduMentor AI")

    st.write(
        """
EduMentor AI is a local RAG-based study
assistant.

Students can upload PDFs and:

- Ask questions
- Generate summaries
- Create quizzes
- Generate flashcards
- Generate important exam questions

Technology:
Python, Streamlit, PyPDF,
SentenceTransformers, ChromaDB and Ollama.
"""
    )