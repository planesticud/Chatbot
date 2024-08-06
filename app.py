import os
import warnings
from dotenv import load_dotenv
from QAHandler import QAHandler
from flask import Flask, request, jsonify

warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv()

# Obtener API Keys
cohere_api_key = os.getenv('COHERE_API_KEY')
docs_path = os.getenv('DOCS_PATH')

qa_handler = QAHandler(cohere_api_key, docs_path)

app = Flask(__name__)

@app.route('/ask', methods=['GET', 'POST'])
def ask():
    if request.method == 'POST':
        data = request.get_json()
        question = data.get('question')
    else:
        question = request.args.get('question')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400

    answer = qa_handler.get_answer(question)
    return jsonify({'answer': answer})

@app.route('/update', methods=['POST'])
def update():
    qa_handler.update_documents()
    return jsonify({'status': 'Documents updated successfully'})

@app.route('/')
def home():
    return "API is running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)