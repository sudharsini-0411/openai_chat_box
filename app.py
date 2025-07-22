from flask import Flask, request, jsonify, render_template
import ollama

app = Flask(__name__)

AI_NAME = "Jingly"  # Custom AI name

# Define personality prompts
personalities = {
    "Formal": f"{AI_NAME} responds in a very formal and professional tone.",
    "Funny": f"{AI_NAME} responds with humor and jokes. Be lighthearted.",
    "Friendly": f"{AI_NAME} responds in a warm, helpful, and casual tone.",
    "Tutor": f"{AI_NAME} explains concepts like a teacher. Be clear and educational."
}

OLLAMA_MODEL = "gemma:2b"

@app.route('/')
def index():
    return render_template('index.html', ai_name=AI_NAME)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get("message", "")
    personality = data.get("personality", "Formal")

    # Compose prompt with Jingly's personality
    prompt = f"{personalities.get(personality, '')}\nUser: {message}\n{AI_NAME}:"

    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=[
            {"role": "user", "content": prompt}
        ])
        reply = response['message']['content']
    except Exception as e:
        reply = f"Oops! {AI_NAME} had an error: {str(e)}"

    return jsonify({"response": reply})

if __name__ == '__main__':
    app.run(debug=True)
