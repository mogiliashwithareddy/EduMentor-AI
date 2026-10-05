from config import OLLAMA_MODEL

from modules.llm_utils import ask_ollama

from modules.rag_engine import (
    get_document_content
)


def get_study_content(source):
    content = get_document_content(
        source=source
    )

    if not content:
        return None

    return content


def generate_summary(
    source,
    summary_type="Exam Revision",
    model=OLLAMA_MODEL
):
    content = get_study_content(source)

    if not content:
        return "No study material found."

    prompt = f"""
Create a {summary_type} summary using ONLY
the following study material.

Use simple language, headings and bullet points.

Study material:

{content}

Summary:
"""

    return ask_ollama(
        prompt,
        model
    )


def generate_quiz(
    source,
    number_of_questions=5,
    difficulty="Medium",
    model=OLLAMA_MODEL
):
    content = get_study_content(source)

    if not content:
        return "No study material found."

    prompt = f"""
Create a {difficulty} level multiple-choice quiz
using ONLY the study material.

Number of questions:
{number_of_questions}

Each question should have:
A.
B.
C.
D.

After all questions give an ANSWER KEY.

Study material:

{content}
"""

    return ask_ollama(
        prompt,
        model
    )


def generate_flashcards(
    source,
    number_of_cards=10,
    model=OLLAMA_MODEL
):
    content = get_study_content(source)

    if not content:
        return "No study material found."

    prompt = f"""
Create {number_of_cards} flashcards using ONLY
the following study material.

Format:

Flashcard 1

Question:
...

Answer:
...

Study material:

{content}
"""

    return ask_ollama(
        prompt,
        model
    )


def generate_important_questions(
    source,
    model=OLLAMA_MODEL
):
    content = get_study_content(source)

    if not content:
        return "No study material found."

    prompt = f"""
Using ONLY the study material below, generate:

2-Mark Questions
5-Mark Questions
10-Mark Questions

Create:
8 two-mark questions
6 five-mark questions
4 ten-mark questions

Study material:

{content}
"""

    return ask_ollama(
        prompt,
        model
    )