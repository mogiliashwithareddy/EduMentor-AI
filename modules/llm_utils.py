import ollama


def ask_ollama(prompt, model="llama3.2", system_prompt=None):
    messages = []

    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    messages.append({
        "role": "user",
        "content": prompt
    })

    response = ollama.chat(
        model=model,
        messages=messages
    )

    return response["message"]["content"]