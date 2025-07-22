import ollama

# Set up a chat with the smaller model 'mistral'
messages = [
    {
        'role': 'user',
        'content': 'Hello, how can I use you in my app?'
    }
]

response = ollama.chat(model='mistral', messages=messages)

# Print the model's response
print("AI Response:", response['message']['content'])
