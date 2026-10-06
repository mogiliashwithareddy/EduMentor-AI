import json
import re

from modules.llm_utils import (
    ask_ollama
)

from modules.rag_engine import (
    get_context_for_source
)


# =========================================================
# SUMMARY
# =========================================================

def generate_summary(
    source,
    summary_type,
    model
):

    context = get_context_for_source(
        source
    )


    if not context:

        return (
            "No study material was found "
            "for the selected document."
        )


    prompt = f"""
You are EduMentor AI.

Create a {summary_type} summary using ONLY
the following study material.

STUDY MATERIAL:

{context}

RULES:

- Use only the provided material.
- Do not invent outside facts.
- Keep important concepts.
- Use clear student-friendly language.
- Organize the response clearly.

Summary type:
{summary_type}
"""


    return ask_ollama(
        prompt=prompt,
        model=model
    )


# =========================================================
# CLEAN QUIZ JSON
# =========================================================

def clean_quiz_json(
    response_text
):

    if not response_text:

        raise ValueError(
            "Ollama returned an empty response."
        )


    text = response_text.strip()


    # Remove opening code fence

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )


    # Remove closing code fence

    text = re.sub(
        r"\s*```$",
        "",
        text
    )


    text = text.strip()


    # Extract the JSON array even if Ollama
    # added accidental text around it

    start = text.find("[")

    end = text.rfind("]")


    if (
        start == -1
        or
        end == -1
        or
        end <= start
    ):

        raise ValueError(
            "Ollama did not return a valid "
            "JSON quiz array."
        )


    return text[
        start:end + 1
    ]


# =========================================================
# VALIDATE QUIZ
# =========================================================

def validate_quiz_data(
    quiz_data,
    expected_count
):

    if not isinstance(
        quiz_data,
        list
    ):

        raise ValueError(
            "Quiz output must be a list."
        )


    if not quiz_data:

        raise ValueError(
            "Quiz contains no questions."
        )


    validated = []


    for index, item in enumerate(
        quiz_data,
        start=1
    ):


        if not isinstance(
            item,
            dict
        ):

            raise ValueError(
                f"Question {index} is invalid."
            )


        # ---------------------------------
        # QUESTION
        # ---------------------------------

        question = item.get(
            "question"
        )


        if (
            not isinstance(
                question,
                str
            )
            or
            not question.strip()
        ):

            raise ValueError(
                f"Question {index} has "
                f"invalid text."
            )


        # ---------------------------------
        # OPTIONS
        # ---------------------------------

        options = item.get(
            "options"
        )


        if (
            not isinstance(
                options,
                list
            )
            or
            len(options) != 4
        ):

            raise ValueError(
                f"Question {index} must "
                f"contain exactly 4 options."
            )


        clean_options = []


        for option in options:

            if (
                not isinstance(
                    option,
                    str
                )
                or
                not option.strip()
            ):

                raise ValueError(
                    f"Question {index} "
                    f"contains an invalid option."
                )


            clean_options.append(
                option.strip()
            )


        # Ensure options are distinct

        if len(
            set(clean_options)
        ) != 4:

            raise ValueError(
                f"Question {index} contains "
                f"duplicate options."
            )


        # ---------------------------------
        # ANSWER
        # ---------------------------------

        answer = item.get(
            "answer"
        )


        if isinstance(
            answer,
            str
        ):

            try:

                answer = int(
                    answer.strip()
                )

            except ValueError:

                raise ValueError(
                    f"Question {index} answer "
                    f"must be 0, 1, 2 or 3."
                )


        if (
            not isinstance(
                answer,
                int
            )
            or
            answer not in [
                0,
                1,
                2,
                3
            ]
        ):

            raise ValueError(
                f"Question {index} has an "
                f"invalid answer index."
            )


        # ---------------------------------
        # EXPLANATION
        # ---------------------------------

        explanation = item.get(
            "explanation",
            ""
        )


        if explanation is None:

            explanation = ""


        if not isinstance(
            explanation,
            str
        ):

            explanation = str(
                explanation
            )


        validated.append(
            {
                "question": question.strip(),
                "options": clean_options,
                "answer": answer,
                "explanation": explanation.strip()
            }
        )


    # Allow Ollama returning fewer/more to produce
    # clear error rather than silently accepting it

    if (
        expected_count
        and
        len(validated)
        != expected_count
    ):

        raise ValueError(
            f"Ollama generated "
            f"{len(validated)} questions, "
            f"but {expected_count} were requested."
        )


    return validated


# =========================================================
# QUIZ
# =========================================================

def generate_quiz(
    source,
    number,
    difficulty,
    model
):

    context = get_context_for_source(
        source
    )


    if not context:

        raise ValueError(
            "No study material was found "
            "for the selected document."
        )


    prompt = f"""
You are EduMentor AI.

Generate exactly {number} multiple-choice
quiz questions using ONLY the supplied
study material.

Difficulty:
{difficulty}

STUDY MATERIAL:

{context}

IMPORTANT:

The student will answer these questions in
an interactive Streamlit quiz.

Do NOT reveal the correct answer in the
question or options.

Return ONLY a valid JSON array.

Do NOT return:
- markdown
- ```json
- code fences
- headings
- introductory text
- closing text

Use exactly this JSON structure:

[
  {{
    "question": "Question text",
    "options": [
      "Option 1",
      "Option 2",
      "Option 3",
      "Option 4"
    ],
    "answer": 0,
    "explanation": "Why the answer is correct"
  }}
]

STRICT RULES:

1. Create exactly {number} questions.
2. Every question must have exactly four options.
3. Exactly one option must be correct.
4. All four options must be different.
5. "answer" must be an integer:
   0 = first option
   1 = second option
   2 = third option
   3 = fourth option
6. Do not write the answer in the question.
7. Do not write "correct answer" inside an option.
8. Use only information from the supplied study material.
9. Keep explanations short and clear.
10. Return JSON only.
"""


    response = ask_ollama(
        prompt=prompt,
        model=model
    )


    cleaned = clean_quiz_json(
        response
    )


    try:

        quiz_data = json.loads(
            cleaned
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            "Ollama returned invalid quiz JSON. "
            f"Details: {error}"
        )


    return validate_quiz_data(
        quiz_data=quiz_data,
        expected_count=number
    )


# =========================================================
# FLASHCARDS
# =========================================================

def generate_flashcards(
    source,
    number,
    model
):

    context = get_context_for_source(
        source
    )


    if not context:

        return (
            "No study material was found "
            "for the selected document."
        )


    prompt = f"""
You are EduMentor AI.

Create exactly {number} study flashcards
using ONLY the study material below.

STUDY MATERIAL:

{context}

FORMAT:

### Flashcard 1

**Front:** Question or key term

**Back:** Short answer or explanation

---

### Flashcard 2

**Front:** Question or key term

**Back:** Short answer or explanation

RULES:

- Generate flashcards only.
- Do not generate quiz questions.
- Do not create multiple-choice options.
- Keep each flashcard concise.
- Use only the supplied material.
"""


    return ask_ollama(
        prompt=prompt,
        model=model
    )


# =========================================================
# IMPORTANT QUESTIONS
# =========================================================

def generate_important_questions(
    source,
    model
):

    context = get_context_for_source(
        source
    )


    if not context:

        return (
            "No study material was found "
            "for the selected document."
        )


    prompt = f"""
You are EduMentor AI.

Generate important exam-style questions
using ONLY the study material below.

STUDY MATERIAL:

{context}

RULES:

- Output questions only.
- Do NOT provide answers.
- Do NOT generate flashcards.
- Do NOT generate a quiz with options.
- Include important conceptual questions.
- Include short-answer and descriptive
  questions when appropriate.
- Use only information contained in the
  supplied material.

FORMAT:

### Important Questions

1. Question
2. Question
3. Question
...
"""


    return ask_ollama(
        prompt=prompt,
        model=model
    )