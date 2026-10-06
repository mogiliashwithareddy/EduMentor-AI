import hashlib
import uuid

import chromadb
import streamlit as st

from pypdf import PdfReader

from sentence_transformers import (
    SentenceTransformer
)

from config import (
    CHROMA_DIR,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K,
    OLLAMA_MODEL
)

from modules.llm_utils import (
    ask_ollama
)


# =========================================================
# EMBEDDING MODEL
# =========================================================

@st.cache_resource
def get_embedding_model():

    return SentenceTransformer(
        EMBEDDING_MODEL
    )


# =========================================================
# PERSISTENT CHROMADB
# =========================================================

@st.cache_resource
def get_chroma_client():

    return chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )


# =========================================================
# COLLECTION
# =========================================================

def get_collection():

    client = get_chroma_client()

    return client.get_or_create_collection(
        name="edumentor_documents"
    )


# =========================================================
# FILE HASH
# =========================================================

def get_file_hash(uploaded_file):

    file_bytes = uploaded_file.getvalue()

    return hashlib.sha256(
        file_bytes
    ).hexdigest()


# =========================================================
# EXTRACT PDF PAGES
# =========================================================

def extract_pdf_pages(
    uploaded_file
):

    uploaded_file.seek(0)

    reader = PdfReader(
        uploaded_file
    )

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        text = page.extract_text()

        if text and text.strip():

            pages.append(
                {
                    "page": page_number,
                    "text": text.strip()
                }
            )

    return pages


# =========================================================
# CREATE CHUNKS
# =========================================================

def create_chunks(
    pages,
    source,
    file_hash
):

    chunks = []

    step = max(
        CHUNK_SIZE - CHUNK_OVERLAP,
        1
    )

    chunk_number = 0

    for page in pages:

        text = page["text"]

        start = 0

        while start < len(text):

            end = (
                start + CHUNK_SIZE
            )

            chunk_text = text[
                start:end
            ].strip()

            if chunk_text:

                chunks.append(
                    {
                        "text": chunk_text,
                        "source": source,
                        "page": page["page"],
                        "chunk": chunk_number,
                        "file_hash": file_hash
                    }
                )

                chunk_number += 1

            start += step

    return chunks


# =========================================================
# CHECK DUPLICATE
# =========================================================

def document_already_exists(
    file_hash
):

    collection = get_collection()

    result = collection.get(
        where={
            "file_hash": file_hash
        }
    )

    ids = result.get(
        "ids",
        []
    )

    return bool(ids)


# =========================================================
# PROCESS UPLOADED FILES
# =========================================================

def process_uploaded_files(
    uploaded_files
):

    collection = get_collection()

    embedding_model = (
        get_embedding_model()
    )

    processed_files = []

    total_chunks = 0

    for uploaded_file in uploaded_files:

        file_hash = get_file_hash(
            uploaded_file
        )


        # ---------------------------------
        # ALREADY SAVED
        # ---------------------------------

        if document_already_exists(
            file_hash
        ):

            processed_files.append(
                {
                    "name": uploaded_file.name,
                    "pages": 0,
                    "status": "Already processed"
                }
            )

            continue


        # ---------------------------------
        # EXTRACT PDF
        # ---------------------------------

        pages = extract_pdf_pages(
            uploaded_file
        )

        if not pages:

            processed_files.append(
                {
                    "name": uploaded_file.name,
                    "pages": 0,
                    "status": "No readable text"
                }
            )

            continue


        # ---------------------------------
        # CHUNK TEXT
        # ---------------------------------

        chunks = create_chunks(
            pages=pages,
            source=uploaded_file.name,
            file_hash=file_hash
        )

        if not chunks:

            continue


        texts = [
            chunk["text"]
            for chunk in chunks
        ]


        # ---------------------------------
        # EMBEDDINGS
        # ---------------------------------

        embeddings = (
            embedding_model.encode(
                texts,
                show_progress_bar=False
            )
        )


        ids = [
            uuid.uuid4().hex
            for _ in chunks
        ]


        metadatas = []

        for chunk in chunks:

            metadatas.append(
                {
                    "source": (
                        chunk["source"]
                    ),
                    "page": int(
                        chunk["page"]
                    ),
                    "chunk": int(
                        chunk["chunk"]
                    ),
                    "file_hash": (
                        chunk["file_hash"]
                    )
                }
            )


        # ---------------------------------
        # SAVE TO CHROMA
        # ---------------------------------

        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )


        total_chunks += len(
            chunks
        )


        processed_files.append(
            {
                "name": uploaded_file.name,
                "pages": len(pages),
                "status": "Processed"
            }
        )


    return (
        processed_files,
        total_chunks
    )


# =========================================================
# DOCUMENT NAMES
# =========================================================

def get_document_names():

    collection = get_collection()

    result = collection.get(
        include=[
            "metadatas"
        ]
    )

    names = set()

    for metadata in result.get(
        "metadatas",
        []
    ):

        if not metadata:
            continue

        source = metadata.get(
            "source"
        )

        if source:
            names.add(source)

    return sorted(names)


# =========================================================
# GET DOCUMENT CONTEXT
# Used by Summary / Quiz / Flashcards etc.
# =========================================================

def get_context_for_source(
    source,
    max_chars=18000
):

    collection = get_collection()

    if collection.count() == 0:
        return ""


    if source == "No Documents":

        return ""


    if source == "All Documents":

        result = collection.get(
            include=[
                "documents",
                "metadatas"
            ]
        )

    else:

        result = collection.get(
            where={
                "source": source
            },
            include=[
                "documents",
                "metadatas"
            ]
        )


    documents = result.get(
        "documents",
        []
    )

    metadatas = result.get(
        "metadatas",
        []
    )


    if not documents:
        return ""


    # Sort chunks by document / page / chunk

    combined = list(
        zip(
            documents,
            metadatas
        )
    )

    combined.sort(
        key=lambda item: (
            item[1].get(
                "source",
                ""
            ),
            item[1].get(
                "page",
                0
            ),
            item[1].get(
                "chunk",
                0
            )
        )
    )


    context_parts = []

    current_length = 0

    for document, metadata in combined:

        source_name = metadata.get(
            "source",
            "Unknown"
        )

        page = metadata.get(
            "page",
            0
        )

        part = (
            f"\nDocument: {source_name}\n"
            f"Page: {page}\n"
            f"{document}\n"
        )


        if (
            current_length
            + len(part)
            > max_chars
        ):
            break


        context_parts.append(
            part
        )

        current_length += len(
            part
        )


    return "\n".join(
        context_parts
    )


# =========================================================
# RETRIEVE RELEVANT CHUNKS
# =========================================================

def retrieve_chunks(
    question,
    selected_source="All Documents"
):

    collection = get_collection()

    if collection.count() == 0:

        return []


    embedding_model = (
        get_embedding_model()
    )


    query_embedding = (
        embedding_model.encode(
            question
        )
    )


    query_args = {
        "query_embeddings": [
            query_embedding.tolist()
        ],
        "n_results": min(
            TOP_K,
            collection.count()
        ),
        "include": [
            "documents",
            "metadatas",
            "distances"
        ]
    }


    if (
        selected_source
        and
        selected_source
        not in [
            "All Documents",
            "No Documents"
        ]
    ):

        query_args["where"] = {
            "source": selected_source
        }


    result = collection.query(
        **query_args
    )


    if not result.get(
        "documents"
    ):

        return []


    if not result[
        "documents"
    ][0]:

        return []


    chunks = []


    documents = (
        result["documents"][0]
    )

    metadatas = (
        result["metadatas"][0]
    )

    distances = (
        result["distances"][0]
    )


    for (
        document,
        metadata,
        distance
    ) in zip(
        documents,
        metadatas,
        distances
    ):

        chunks.append(
            {
                "text": document,
                "source": metadata.get(
                    "source",
                    "Unknown"
                ),
                "page": int(
                    metadata.get(
                        "page",
                        0
                    )
                ),
                "distance": distance
            }
        )


    return chunks


# =========================================================
# ANSWER QUESTION
# =========================================================

def answer_question(
    question,
    selected_source="All Documents",
    model=OLLAMA_MODEL,
    chat_history=None
):

    chunks = retrieve_chunks(
        question=question,
        selected_source=selected_source
    )


    if not chunks:

        return (
            "I could not find relevant information "
            "in the selected study material.",
            []
        )


    context_parts = []


    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        context_parts.append(
            f"""
SOURCE {index}

Document:
{chunk['source']}

Page:
{chunk['page']}

Content:
{chunk['text']}
"""
        )


    context = "\n\n".join(
        context_parts
    )


    # -------------------------------------
    # RECENT CHAT
    # -------------------------------------

    history_text = ""

    if chat_history:

        for message in (
            chat_history[-6:]
        ):

            history_text += (
                f"{message['role']}: "
                f"{message['content']}\n"
            )


    prompt = f"""
You are EduMentor AI.

Answer the student's question using the
retrieved study material.

RETRIEVED STUDY MATERIAL:

{context}

RECENT CHAT:

{history_text}

STUDENT QUESTION:

{question}

RULES:

1. Use the retrieved material as the
   primary source.
2. Do not invent unsupported facts.
3. Explain clearly in student-friendly
   language.
4. Mention relevant document/page numbers
   when useful.
5. Use chat history only to understand
   follow-up questions.
"""


    answer = ask_ollama(
        prompt=prompt,
        model=model
    )


    return (
        answer,
        chunks
    )