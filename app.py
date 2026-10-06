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


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📚",
    layout="wide"
)


# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()


if "summary_output" not in st.session_state:
    st.session_state.summary_output = ""


if "flashcard_output" not in st.session_state:
    st.session_state.flashcard_output = ""


if "important_questions_output" not in st.session_state:
    st.session_state.important_questions_output = ""


# Quiz state

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = []


if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False


if "quiz_user_answers" not in st.session_state:
    st.session_state.quiz_user_answers = {}


# Used to detect page changes

if "previous_page" not in st.session_state:
    st.session_state.previous_page = None


# =========================================================
# HELPER: CLEAR QUIZ ONLY
# =========================================================

def clear_quiz_state():

    st.session_state.quiz_data = []

    st.session_state.quiz_submitted = False

    st.session_state.quiz_user_answers = {}


    quiz_answer_keys = [
        key
        for key in list(
            st.session_state.keys()
        )
        if key.startswith(
            "quiz_answer_"
        )
    ]


    for key in quiz_answer_keys:

        del st.session_state[
            key
        ]


# =========================================================
# DOCUMENT SELECTOR HELPER
# =========================================================

def available_documents():

    names = get_document_names()


    if not names:

        return [
            "No Documents"
        ]


    return [
        "All Documents"
    ] + names


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "📚 EduMentor AI"
)


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


# =========================================================
# RESET QUIZ WHEN LEAVING QUIZ PAGE
# =========================================================

if (
    st.session_state.previous_page == "❓ Quiz"
    and
    page != "❓ Quiz"
):

    clear_quiz_state()


st.session_state.previous_page = page


# =========================================================
# HOME PAGE
# =========================================================

if page == "🏠 Home":

    st.title(
        "📚 EduMentor AI"
    )


    st.subheader(
        "Your Personal AI Study Assistant"
    )


    st.write(
        """
        Upload your PDF notes once and reuse them
        for chat, summaries, quizzes, flashcards
        and exam preparation.
        """
    )


    collection = get_collection()


    col1, col2, col3 = st.columns(
        3
    )


    col1.metric(
        "Documents",
        len(
            get_document_names()
        )
    )


    col2.metric(
        "Study Sections",
        collection.count()
    )


    col3.metric(
        "Chat Messages",
        len(
            st.session_state.messages
        )
    )


# =========================================================
# STUDY MATERIALS
# =========================================================

elif page == "📂 Study Materials":

    st.title(
        "📂 Study Materials"
    )


    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type=[
            "pdf"
        ],
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

                try:

                    files, chunk_count = (
                        process_uploaded_files(
                            uploaded_files
                        )
                    )

                except Exception as error:

                    files = []

                    chunk_count = 0

                    st.error(
                        f"Processing error: {error}"
                    )


            if files:

                processed = [
                    item
                    for item in files
                    if item.get(
                        "status"
                    ) == "Processed"
                ]


                existing = [
                    item
                    for item in files
                    if item.get(
                        "status"
                    ) == "Already processed"
                ]


                unreadable = [
                    item
                    for item in files
                    if item.get(
                        "status"
                    ) == "No readable text"
                ]


                if processed:

                    st.success(
                        "Study materials processed."
                    )


                    st.write(
                        f"{chunk_count} new study "
                        "sections created."
                    )


                if existing:

                    st.info(
                        "Previously processed "
                        "documents were detected."
                    )


                for item in processed:

                    st.write(
                        f"✅ {item['name']} "
                        f"— {item['pages']} pages"
                    )


                for item in existing:

                    st.write(
                        f"♻️ {item['name']} "
                        "— already available"
                    )


                for item in unreadable:

                    st.write(
                        f"⚠️ {item['name']} "
                        "— no readable text"
                    )


    st.divider()


    st.subheader(
        "Current Knowledge Base"
    )


    documents = get_document_names()


    if documents:

        for name in documents:

            st.write(
                f"📄 {name}"
            )

    else:

        st.caption(
            "No study materials available."
        )


# =========================================================
# CHAT WITH NOTES
# =========================================================

elif page == "💬 Chat With Notes":

    st.title(
        "💬 Chat With Notes"
    )


    selected_source = st.selectbox(
        "Study material",
        available_documents(),
        key="chat_source"
    )


    # Show previous messages

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

        if selected_source == "No Documents":

            st.warning(
                "Please process a PDF first."
            )

        else:

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": question
                }
            )


            with st.chat_message(
                "user"
            ):

                st.markdown(
                    question
                )


            with st.chat_message(
                "assistant"
            ):

                with st.spinner(
                    "Searching your notes..."
                ):

                    try:

                        answer, chunks = (
                            answer_question(
                                question=question,
                                selected_source=(
                                    selected_source
                                ),
                                model=OLLAMA_MODEL,
                                chat_history=(
                                    st.session_state.messages
                                )
                            )
                        )

                    except Exception as error:

                        answer = (
                            "Sorry, I could not "
                            "process the question."
                        )

                        chunks = []

                        st.error(
                            f"Chat error: {error}"
                        )


                st.markdown(
                    answer
                )


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


                            if key in shown:

                                continue


                            shown.add(
                                key
                            )


                            st.write(
                                f"📄 {chunk['source']} "
                                f"— Page "
                                f"{chunk['page']}"
                            )


            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )


            save_chat_history(
                st.session_state.messages
            )


    if st.session_state.messages:

        if st.button(
            "🗑️ Clear Chat History"
        ):

            st.session_state.messages = []

            clear_chat_history()

            st.rerun()


# =========================================================
# SUMMARY
# =========================================================

elif page == "📝 Summary":

    st.title(
        "📝 Summary Generator"
    )


    source = st.selectbox(
        "Select study material",
        available_documents(),
        key="summary_source"
    )


    summary_type = st.selectbox(
        "Summary type",
        [
            "Short",
            "Detailed",
            "Exam Revision",
            "Bullet Point"
        ],
        key="summary_type"
    )


    if st.button(
        "Generate Summary",
        type="primary"
    ):

        if source == "No Documents":

            st.warning(
                "Please process a PDF first."
            )

        else:

            with st.spinner(
                "Generating summary..."
            ):

                try:

                    st.session_state.summary_output = (
                        generate_summary(
                            source,
                            summary_type,
                            OLLAMA_MODEL
                        )
                    )

                except Exception as error:

                    st.error(
                        f"Summary error: {error}"
                    )


    if st.session_state.summary_output:

        st.divider()


        st.subheader(
            "Generated Summary"
        )


        st.markdown(
            st.session_state.summary_output
        )


# =========================================================
# QUIZ
# =========================================================

elif page == "❓ Quiz":

    st.title(
        "❓ Interactive Quiz"
    )


    source = st.selectbox(
        "Select study material",
        available_documents(),
        key="quiz_source"
    )


    number = st.slider(
        "Number of questions",
        min_value=3,
        max_value=15,
        value=5,
        key="quiz_number"
    )


    difficulty = st.selectbox(
        "Difficulty",
        [
            "Easy",
            "Medium",
            "Hard"
        ],
        key="quiz_difficulty"
    )


    # -----------------------------------------------------
    # GENERATE QUIZ
    # -----------------------------------------------------

    if st.button(
        "Generate Quiz",
        type="primary"
    ):

        if source == "No Documents":

            st.warning(
                "Please process a PDF first."
            )

        else:

            with st.spinner(
                "Generating quiz..."
            ):

                try:

                    quiz = generate_quiz(
                        source,
                        number,
                        difficulty,
                        OLLAMA_MODEL
                    )


                    # Clear old answer widgets

                    old_keys = [
                        key
                        for key in list(
                            st.session_state.keys()
                        )
                        if key.startswith(
                            "quiz_answer_"
                        )
                    ]


                    for key in old_keys:

                        del st.session_state[
                            key
                        ]


                    st.session_state.quiz_data = (
                        quiz
                    )


                    st.session_state.quiz_submitted = (
                        False
                    )


                    st.session_state.quiz_user_answers = (
                        {}
                    )


                    st.rerun()


                except Exception as error:

                    st.error(
                        f"Quiz error: {error}"
                    )


    # -----------------------------------------------------
    # QUIZ EXISTS
    # -----------------------------------------------------

    if st.session_state.quiz_data:

        st.divider()


        # =================================================
        # BEFORE SUBMISSION
        # =================================================

        if not st.session_state.quiz_submitted:

            st.subheader(
                "Answer the questions"
            )


            st.caption(
                "Choose one answer for every "
                "question and then submit."
            )


            for index, item in enumerate(
                st.session_state.quiz_data
            ):

                st.markdown(
                    f"### {index + 1}. "
                    f"{item['question']}"
                )


                st.radio(
                    "Choose an answer",
                    item["options"],
                    index=None,
                    key=(
                        f"quiz_answer_{index}"
                    )
                )


                st.divider()


            # ---------------------------------------------
            # SUBMIT
            # ---------------------------------------------

            if st.button(
                "Submit Quiz",
                type="primary",
                use_container_width=True
            ):

                unanswered = []

                answers = {}


                for index in range(
                    len(
                        st.session_state.quiz_data
                    )
                ):

                    key = (
                        f"quiz_answer_{index}"
                    )


                    selected = (
                        st.session_state.get(
                            key
                        )
                    )


                    if selected is None:

                        unanswered.append(
                            index + 1
                        )

                    else:

                        answers[
                            index
                        ] = selected


                if unanswered:

                    st.warning(
                        "Please answer all questions. "
                        "Unanswered: "
                        + ", ".join(
                            map(
                                str,
                                unanswered
                            )
                        )
                    )

                else:

                    st.session_state.quiz_user_answers = (
                        answers
                    )


                    st.session_state.quiz_submitted = (
                        True
                    )


                    st.rerun()


        # =================================================
        # AFTER SUBMISSION
        # =================================================

        else:

            score = 0


            total = len(
                st.session_state.quiz_data
            )


            for index, item in enumerate(
                st.session_state.quiz_data
            ):

                st.markdown(
                    f"### {index + 1}. "
                    f"{item['question']}"
                )


                selected = (
                    st.session_state
                    .quiz_user_answers
                    .get(index)
                )


                correct_index = (
                    item["answer"]
                )


                correct_answer = (
                    item["options"][
                        correct_index
                    ]
                )


                st.write(
                    f"**Your answer:** "
                    f"{selected}"
                )


                st.write(
                    f"**Correct answer:** "
                    f"{correct_answer}"
                )


                if selected == correct_answer:

                    score += 1

                    st.success(
                        "Correct"
                    )

                else:

                    st.error(
                        "Incorrect"
                    )


                explanation = item.get(
                    "explanation",
                    ""
                )


                if explanation:

                    st.info(
                        f"Explanation: "
                        f"{explanation}"
                    )


                st.divider()


            percentage = (
                score / total * 100
                if total
                else 0
            )


            st.subheader(
                "Quiz Result"
            )


            col1, col2 = st.columns(
                2
            )


            col1.metric(
                "Score",
                f"{score} / {total}"
            )


            col2.metric(
                "Percentage",
                f"{percentage:.0f}%"
            )


            if percentage >= 80:

                st.success(
                    "Excellent work!"
                )

            elif percentage >= 60:

                st.info(
                    "Good work. Review the "
                    "incorrect questions."
                )

            else:

                st.warning(
                    "Review the material "
                    "and try again."
                )


            # ---------------------------------------------
            # NEW QUIZ
            # ---------------------------------------------

            if st.button(
                "🔄 Start New Quiz"
            ):

                clear_quiz_state()

                st.rerun()


# =========================================================
# FLASHCARDS
# =========================================================

elif page == "🧠 Flashcards":

    st.title(
        "🧠 Flashcards"
    )


    source = st.selectbox(
        "Select study material",
        available_documents(),
        key="flashcard_source"
    )


    number = st.slider(
        "Number of flashcards",
        min_value=5,
        max_value=20,
        value=10,
        key="flashcard_number"
    )


    if st.button(
        "Generate Flashcards",
        type="primary"
    ):

        if source == "No Documents":

            st.warning(
                "Please process a PDF first."
            )

        else:

            with st.spinner(
                "Generating flashcards..."
            ):

                try:

                    st.session_state.flashcard_output = (
                        generate_flashcards(
                            source,
                            number,
                            OLLAMA_MODEL
                        )
                    )

                except Exception as error:

                    st.error(
                        f"Flashcard error: {error}"
                    )


    if st.session_state.flashcard_output:

        st.divider()


        st.subheader(
            "Generated Flashcards"
        )


        st.markdown(
            st.session_state.flashcard_output
        )


# =========================================================
# IMPORTANT QUESTIONS
# =========================================================

elif page == "🎯 Important Questions":

    st.title(
        "🎯 Important Questions"
    )


    source = st.selectbox(
        "Select study material",
        available_documents(),
        key="important_questions_source"
    )


    if st.button(
        "Generate Important Questions",
        type="primary"
    ):

        if source == "No Documents":

            st.warning(
                "Please process a PDF first."
            )

        else:

            with st.spinner(
                "Generating questions..."
            ):

                try:

                    st.session_state.important_questions_output = (
                        generate_important_questions(
                            source,
                            OLLAMA_MODEL
                        )
                    )

                except Exception as error:

                    st.error(
                        "Important questions error: "
                        f"{error}"
                    )


    if st.session_state.important_questions_output:

        st.divider()


        st.subheader(
            "Important Questions"
        )


        st.markdown(
            st.session_state.important_questions_output
        )


# =========================================================
# ABOUT
# =========================================================

elif page == "ℹ️ About":

    st.title(
        "ℹ️ About EduMentor AI"
    )


    st.markdown(
        """
EduMentor AI is a local RAG-based study
assistant.

### Features

- Persistent PDF study materials
- Chat with notes
- Source and page references
- Summary generation
- Interactive quizzes
- Flashcards
- Important exam questions
- Persistent chat history

### Technologies

- Python
- Streamlit
- Ollama
- PyPDF
- Sentence Transformers
- ChromaDB
- Retrieval-Augmented Generation
"""
    )