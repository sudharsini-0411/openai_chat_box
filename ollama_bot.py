import ollama

# Define personalities
personalities = {
    "funny": "Respond in a funny and humorous way.",
    "tutor": "Act like a kind and helpful tutor. Explain clearly.",
    "formal": "Be polite and formal in your responses.",
    "friendly": "Sound cheerful and conversational like a friend."
}

# Let user pick personality
print("Choose a personality: funny, tutor, formal, friendly")
personality = input("Your choice: ").lower()

if personality not in personalities:
    personality = "friendly"

def chat_with_gemma(message):
    response = ollama.chat(
        model='gemma:2b',
        messages=[
            {"role": "system", "content": personalities[personality]},
            {"role": "user", "content": message}
        ]
    )
    return response['message']['content']

# Chat loop
user_input = input("You: ")
while user_input.lower() not in ["exit", "quit"]:
    reply = chat_with_gemma(user_input)
    print("Gemma:", reply)
    user_input = input("You: ")
