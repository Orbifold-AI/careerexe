from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from openai import OpenAI
import os
import pandas as pd
import json

app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Hard-coded knowledge from a txt file
def load_hardcoded_knowledge(file_path):
    """Load knowledge from a specified txt file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error loading hardcoded knowledge: {str(e)}"

# Load knowledge from a txt file
KNOWLEDGE_BASE = load_hardcoded_knowledge('sample_500.csv')

def extract_csv_text(file_path):
    """Extract text from a CSV file."""
    text = ""
    try:
        df = pd.read_csv(file_path)
        text = df.to_string(index=False)  # Convert entire DataFrame to a string format
    except Exception as e:
        text = f"Error extracting CSV text: {str(e)}"
    return text

# Preload the CSV content from 'sample.csv' at startup
CSV_CONTENT = extract_csv_text('sample_10.csv')

@app.route('/verify', methods=['POST'])
def verify_code():
    data = request.get_json()
    if data['code'] == '5124':
        return jsonify({'valid': True})
    else:
        return jsonify({'valid': False})

@app.route('/ask', methods=['POST'])
def ask_question():
    """Endpoint to answer a question based on preloaded CSV content."""
    data = request.get_json()
    user_question = data.get('question', '')

    if not user_question:
        return jsonify({'message': 'Question is missing'}), 400

    try:
        # Send preloaded CSV content and user question to OpenAI's chat completion
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {"role": "system", "content": f"Hard-coded knowledge:\n{KNOWLEDGE_BASE}"},
                {"role": "system", "content": "Refer solely to the provided file when answering questions, avoiding any online resources. Do not mention the source or format of the data. This CSV file includes individuals' names, job histories, and educational backgrounds. For any row missing a name, assign the information to the most recent prior individual with a name. Respond in English if the question is in English, in Chinese if the question is in Chinese, and in Chinese if the question combines English and Chinese."},
                {"role": "system", "content": "Generate possible follow-up questions that users might ask and return to us."},
                {"role": "user", "content": f"CSV Content: {CSV_CONTENT}\n\nUser Question: {user_question}"}
            ]
        )

        response_message = response.choices[0].message.content
        # Add basic HTML formatting for better display
        #formatted_response = response_message.replace('\n', '<br>')
        
        formatted_response = response_message.replace('\n', '<br>')
        return Response(
            response=json.dumps({'message': formatted_response}),
            status=200,
            content_type='application/json; charset=utf-8'
        )
    
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)