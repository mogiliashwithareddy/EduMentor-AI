import uuid
import chromadb

from sentence_transformers import SentenceTransformer

from config import (
    CHROMA_DIR,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K,
    OLLAMA_MODEL,
)

from modules.document_processor import (
    extract_pdf_pages,
    create_chunks,
)

from modules.llm_utils import ask_ollama


_embedding_model = None


def get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = SentenceTransformer(
            EMBEDDING_MODEL
        )

    return _embedding_model


def get_client():
    return chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )


def get_collection():
    client = get_client()

    return client.get_or_create_collection(
        name="study_materials"
    )


def clear_database():
    client = get_client()

    try:
        client.delete_collection(
            name="study_materials"
        )
    except Exception:
        pass

    return client.get_or_create_collection(
        name="study_materials"
    )


def process_uploaded_files(uploaded_files):
    collection = clear_database()
    embedding_model = get_embedding_model()

    all_chunks = []
    processed_files = []

    for uploaded_file in uploaded_files:
        pages = extract_pdf_pages(uploaded_file)

        if not pages:
            continue

        chunks = create_chunks(
            pages=pages,
            source=uploaded_file.name,
            chunk_size=CHUNK_SIZE,
            overlap=CHUNK_OVERLAP
        )

        all_chunks.extend(chunks)

        processed_files.append({
            "name": uploaded_file.name,
            "pages": len(pages),
            "chunks": len(chunks)
        })

    if not all_chunks:
        return processed_files, 0

    texts = [
        chunk["text"]
        for chunk in all_chunks
    ]

    embeddings = embedding_model.encode(
        texts,
        show_progress_bar=False
    )

    ids = [
        str(uuid.uuid4())
        for _ in all_chunks
    ]

    metadatas = [
        {
            "source": chunk["source"],
            "page": chunk["page"],
            "chunk": chunk["chunk"]
        }
        for chunk in all_chunks
    ]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=metadatas
    )

    return processed_files, len(all_chunks)


def get_document_names():
    collection = get_collection()

    if collection.count() == 0:
        return []

    results = collection.get(
        include=["metadatas"]
    )

    names = set()

    for metadata in results["metadatas"]:
        if metadata:
            names.add(
                metadata.get(
                    "source",
                    "Unknown"
                )
            )

    return sorted(names)


def retrieve_chunks(question, top_k=TOP_K, selected_source=None):
    collection = get_collection()

    count = collection.count()

    if count == 0:
        return []

    embedding_model = get_embedding_model()

    question_embedding = embedding_model.encode(
        question
    )

    query_args = {
        "query_embeddings": [
            question_embedding.tolist()
        ],
        "n_results": min(top_k, count),
        "include": [
            "documents",
            "metadatas",
            "distances"
        ]
    }

    if selected_source and selected_source != "All Documents":
        query_args["where"] = {
            "source": selected_source
        }

    results = collection.query(
        **query_args
    )

    retrieved = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):
        retrieved.append({
            "text": document,
            "source": metadata.get("source", "Unknown"),
            "page": metadata.get("page", "?"),
            "distance": distance
        })

    return retrieved


def answer_question(
    question,
    selected_source=None,
    model=OLLAMA_MODEL,
    chat_history=None
):
    chunks = retrieve_chunks(
        question=question,
        selected_source=selected_source
    )

    if not chunks:
        return (
            "Please upload and process your study material first.",
            []
        )

    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"""
[Source {index}]
File: {chunk['source']}
Page: {chunk['page']}

{chunk['text']}
"""
        )

    context = "\n\n".join(context_parts)

    history_text = ""

    if chat_history:
        recent_history = chat_history[-6:]

        for message in recent_history:
            history_text += (
                f"{message['role']}: "
                f"{message['content']}\n"
            )

    prompt = f"""
You are EduMentor AI, a helpful study assistant.

Answer the student's question using ONLY the
study material provided below.

Rules:
1. Use simple language.
2. Do not invent information.
3. If the answer is not in the material, say:
"I could not find this information in the uploaded study material."
4. Mention relevant source filename and page.
5. Use conversation history only for follow-up context.

Recent conversation:
{history_text}

Study material:
{context}

Student question:
{question}

Answer:
"""

    answer = ask_ollama(
        prompt=prompt,
        model=model
    )

    return answer, chunks


def get_document_content(source=None, max_chars=14000):
    collection = get_collection()

    if collection.count() == 0:
        return ""

    if source and source != "All Documents":
        results = collection.get(
            where={"source": source},
            include=["documents", "metadatas"]
        )
    else:
        results = collection.get(
            include=["documents", "metadatas"]
        )

    items = []

    for document, metadata in zip(
        results["documents"],
        results["metadatas"]
    ):
        items.append(
            (
                metadata.get("source", ""),
                int(metadata.get("page", 0)),
                document
            )
        )

    items.sort(
        key=lambda x: (
            x[0],
            x[1]
        )
    )

    combined = ""

    for source_name, page, text in items:
        section = (
            f"\n\nFile: {source_name}\n"
            f"Page: {page}\n{text}"
        )

        if len(combined) + len(section) > max_chars:
            break

        combined += section

    return combined