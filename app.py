from flask import Flask, request, render_template_string, jsonify, send_file
import openai
from pathlib import Path
import os
import io
import PyPDF2
from fpdf import FPDF
import re
import tempfile
import requests


app = Flask(__name__)


# Initialize the OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')


# Pinata API credentials
PINATA_API_KEY = os.getenv('PINATA_API_KEY')
PINATA_SECRET_API_KEY = os.getenv('PINATA_SECRET_API_KEY')


# HTML template for the upload page
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
   <title>Test Generator</title>
   <style>
       body { max-width: 800px; margin: 0 auto; padding: 20px; background-color: green; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; font-family: Arial, sans-serif; }
       .container { margin-top: 20px; }
       #result { white-space: pre-wrap; }
       .error { color: red; }
       .center-text { text-align: center; font-size: 24px; color: white; font-weight: bold; }
       .welcome-text { text-align: center; font-size: 36px; color: white; font-weight: bold; margin-top: 20vh; }
       .bottom-left { position: absolute; bottom: 20px; left: 20px; }
   </style>
</head>
<body>
   <div class="welcome-text">Welcome to the future of educational resources</div>
   <h1 class="center-text">Test Case Generator</h1>
   <div class="center-text">This is the future of education</div>
   <form id="uploadForm" enctype="multipart/form-data" method="post" action="/generate" class="bottom-left">
       <input type="file" name="file" accept=".pdf" required>
       <button type="submit">Generate Similar Tests</button>
   </form>
   <div class="container">
       <h2>Generated Tests:</h2>
       <div id="result"></div>
   </div>
</body>
</html>
'''


def read_pdf_content(file_path):
   """Read content from a PDF file."""
   try:
       with open(file_path, 'rb') as file:
           reader = PyPDF2.PdfReader(file)
           content = ""
           for page_num in range(len(reader.pages)):
               page = reader.pages[page_num]
               text = page.extract_text()
               if text:
                   content += text
               else:
                   print(f"Warning: No text extracted from page {page_num}")
       return content
   except Exception as e:
       print(f"Error reading PDF content: {str(e)}")
       return None


def generate_similar_tests(original_content):
   """Generate similar tests using OpenAI API."""
   try:
       response = openai.Completion.create(
           model="text-davinci-003",
           prompt=f"Here is the original test:\n\n{original_content}\n\nPlease generate 3 similar but different test cases following the same pattern and structure.",
           max_tokens=1500,
           n=1,
           stop=None,
           temperature=0.7
       )
       return response.choices[0].text.strip()
   except Exception as e:
       return f"Error generating tests: {str(e)}"


def create_pdf(content, output_path):
   """Create a PDF from text content using FPDF."""
   pdf = FPDF()
   pdf.add_page()
   pdf.set_auto_page_break(auto=True, margin=15)
   pdf.set_font("Arial", size=12)
   pdf.multi_cell(0, 10, content)
   pdf.output(output_path)


def upload_to_pinata(file_path):
   """Upload a file to Pinata and return the CID."""
   url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
   headers = {
       "pinata_api_key": PINATA_API_KEY,
       "pinata_secret_api_key": PINATA_SECRET_API_KEY
   }
   with open(file_path, 'rb') as file:
       files = {
           'file': (os.path.basename(file_path), file)
       }
       response = requests.post(url, headers=headers, files=files)
       if response.status_code == 200:
           return response.json()['IpfsHash']
       else:
           raise RuntimeError(f"Error uploading to Pinata: {response.content.decode()}")


@app.route('/')
def index():
   """Render the upload page."""
   return render_template_string(HTML_TEMPLATE)


@app.route('/generate', methods=['POST'])
def generate():
   """Handle file upload and test generation."""
   if 'file' not in request.files:
       return jsonify({'error': 'No file uploaded'}), 400
  
   file = request.files['file']
   if file.filename == '':
       return jsonify({'error': 'No file selected'}), 400


   try:
       # Save the uploaded file
       original_file_path = os.path.join(tempfile.gettempdir(), file.filename)
       file.save(original_file_path)


       # Read the content of the uploaded PDF
       content = read_pdf_content(original_file_path)
       if not content:
           return jsonify({'error': 'Failed to extract content from the uploaded PDF'}), 400


       generated_tests = generate_similar_tests(content)
      
       # Create a PDF with the generated tests
       generated_file_path = os.path.join(tempfile.gettempdir(), "generated_tests.pdf")
       create_pdf(generated_tests, generated_file_path)
      
       # Upload the original PDF to Pinata
       original_cid = upload_to_pinata(original_file_path)
      
       # Upload the generated PDF to Pinata
       generated_cid = upload_to_pinata(generated_file_path)
      
       return jsonify({
           'message': 'PDFs generated and uploaded to Pinata',
           'original_cid': original_cid,
           'generated_cid': generated_cid
       })
   except Exception as e:
       return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
   if not openai.api_key:
       print("Warning: OpenAI API key not set. Please set it before running the application.")
   app.run(debug=True, port=5001)