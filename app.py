
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import ollama
import os
from werkzeug.utils import secure_filename
import PyPDF2
from PIL import Image, ImageDraw, ImageFont
import requests
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

AI_NAME = "Jingly"
UPLOAD_FOLDER = 'uploads'
GENERATED_IMAGES_FOLDER = 'static/generated_images'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_IMAGES_FOLDER, exist_ok=True)
os.makedirs('static', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def clean_text_for_json(text):
    """Clean text to prevent JSON parsing issues"""
    if not text:
        return ""
    # Remove non-printable characters
    cleaned = ''.join(char for char in text if ord(char) >= 32 and ord(char) < 127)
    # Remove problematic characters
    cleaned = cleaned.replace('<', '').replace('>', '').replace('"', "'")
    cleaned = cleaned.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
    # Remove multiple spaces
    cleaned = ' '.join(cleaned.split())
    return cleaned

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/generated_images/<filename>')
def generated_images(filename):
    return send_from_directory(GENERATED_IMAGES_FOLDER, filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file selected"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            try:
                file_info = {
                    "filename": filename,
                    "size": os.path.getsize(file_path),
                    "path": file_path,
                    "type": filename.split('.')[-1].lower()
                }
                
                if filename.lower().endswith('.pdf'):
                    content = extract_text_from_pdf(file_path)
                    content = clean_text_for_json(content)
                    if len(content) > 1000:
                        content = content[:1000] + "... (truncated)"
                    file_info["content"] = content
                    file_info["pages"] = len(PyPDF2.PdfReader(open(file_path, 'rb')).pages)
                else:
                    file_info["content"] = f"Image {filename} uploaded successfully!"
                
                # Don't remove the file - keep it in uploads folder
                return jsonify({
                    "success": True,
                    "file_info": file_info
                }), 200
                
            except Exception as e:
                if os.path.exists(file_path):
                    os.remove(file_path)
                return jsonify({"error": f"Error processing file: {str(e)}"}), 500
        
        return jsonify({"error": "Invalid file type. Please upload PDF, PNG, JPG, JPEG, or GIF files."}), 400
    
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route('/generate-image', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400
            
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
        
        # Create a colorful placeholder image
        colors = [(255, 182, 193), (173, 216, 230), (144, 238, 144), (255, 218, 185), (221, 160, 221)]
        color = colors[len(prompt) % len(colors)]
        
        img = Image.new('RGB', (400, 300), color=color)
        draw = ImageDraw.Draw(img)
        
        # Add border
        draw.rectangle([10, 10, 390, 290], outline=(255, 255, 255), width=2)
        
        # Add text safely
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        # Clean and wrap text - remove all problematic characters
        clean_prompt = ''.join(char for char in prompt if ord(char) < 128)
        clean_prompt = clean_prompt.replace('<', '').replace('>', '').replace('"', "'")
        
        words = clean_prompt.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > 30:
                lines.append(' '.join(current_line[:-1]))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        y_offset = 30
        for line in lines[:6]:
            draw.text((20, y_offset), line, fill=(255, 255, 255), font=font)
            y_offset += 25
        
        draw.text((20, 250), "AI Generated Image", fill=(255, 255, 255), font=font)
        
        # Generate unique filename
        import time
        filename = f"generated_{int(time.time())}.png"
        filepath = os.path.join(GENERATED_IMAGES_FOLDER, filename)
        img.save(filepath)
        
        return jsonify({
            "success": True,
            "image_url": f"/static/generated_images/{filename}",
            "prompt": clean_prompt
        })
        
    except Exception as e:
        return jsonify({"error": f"Image generation failed: {str(e)}"})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    personality = data.get('personality', 'Friendly')
    
    try:
        response = ollama.chat(
            model='gemma:2b',
            messages=[
                {"role": "system", "content": f"You are {AI_NAME}, a helpful AI assistant. Be {personality.lower()}."},
                {"role": "user", "content": message}
            ]
        )
        return jsonify({"response": response['message']['content']})
    except Exception as e:
        return jsonify({"response": f"Sorry, I'm having trouble connecting. Error: {str(e)}"})

@app.route('/files', methods=['GET'])
def list_files():
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                files.append({
                    "filename": filename,
                    "size": os.path.getsize(file_path),
                    "modified": os.path.getmtime(file_path)
                })
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
