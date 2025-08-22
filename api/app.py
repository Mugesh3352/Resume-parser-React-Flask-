# Import necessary libraries
import os
import zipfile
import io
import re
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import pdfplumber
from docx import Document
import spacy # For NLP tasks
from flask import Flask
from flask_cors import CORS
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd

# Initialize Flask app
app = Flask(__name__)

CORS(app)  

# Configure upload folder (resumes will be extracted here temporarily)
UPLOAD_FOLDER = 'temp_resumes'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load English NLP model from spaCy
# You might need to download it first: python -m spacy download en_core_web_sm
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy 'en_core_web_sm' model...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# --- Helper Functions for Resume Parsing ---

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file using pdfplumber.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)
            return "\n".join(full_text)
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
        return None

def extract_text_from_docx(docx_path):
    """
    Extracts text from a DOCX file using python-docx.
    """
    try:
        doc = Document(docx_path)
        full_text = []
        for para in doc.paragraphs:
            if para.text:
                full_text.append(para.text)
        return "\n".join(full_text)
    except Exception as e:
        print(f"Error extracting text from DOCX {docx_path}: {e}")
        return None

def get_candidate_name_from_text(text):
    """
    Attempts to extract a candidate name from the beginning of the resume text.
    This is a simple heuristic and might not be accurate for all resumes.
    It looks for the first few capitalized words.
    """
    if not text:
        return "Unknown Candidate"
    # Take the first line or a short segment and try to find capitalized words
    first_lines = text.split('\n')[:3]
    name_candidates = []
    for line in first_lines:
        # Find sequences of two or more capitalized words
        matches = re.findall(r'\b[A-Z][a-z]+\s(?:[A-Z][a-z]*\s?)+\b', line)
        if matches:
            # Pick the longest match or the first one as a potential name
            longest_match = max(matches, key=len, default="")
            if longest_match:
                name_candidates.append(longest_match.strip())
    
    if name_candidates:
        return name_candidates[0] # Return the first good candidate
    
    # Fallback to just the first few words if no good match
    words = text.split()
    if len(words) >= 2:
        return f"{words[0].capitalize()} {words[1].capitalize()}"
    elif len(words) == 1:
        return words[0].capitalize()
    return "Unknown Candidate"


# --- NLP Processing and Matching Functions ---

def preprocess_text(text):
    """
    Tokenizes text, removes stopwords and punctuation, and converts to lowercase.
    Returns a list of significant tokens.
    """
    if not text:
        return []
    doc = nlp(text.lower())
    # Filter out stopwords, punctuation, and non-alphabetic tokens
    tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct and token.is_alpha]
    return tokens

def calculate_match_score(resume_tokens, jd_tokens):
    """
    Calculates a simple match percentage based on shared keywords.
    Also identifies top skills (shared) and missing skills (JD skills not in resume).
    """
    # Convert to sets for efficient intersection and difference operations
    resume_skills_set = set(resume_tokens)
    jd_skills_set = set(jd_tokens)

    # Find common skills
    common_skills = resume_skills_set.intersection(jd_skills_set)

    # Calculate match percentage
    if not jd_skills_set: # Avoid division by zero if JD is empty
        return 0, [], []
    match_percentage = (len(common_skills) / len(jd_skills_set)) * 100

    # Identify top skills (can be enhanced with TF-IDF later)
    # For now, top skills are just the common skills
    top_skills = list(common_skills)

    # Identify missing skills (JD skills not found in resume)
    missing_skills = list(jd_skills_set.difference(resume_skills_set))

    return match_percentage, top_skills, missing_skills

# --- Flask Routes ---

# @app.route('/api/match_resumes', methods=['POST'])
# def match_resumes():
#     """
#     API endpoint to receive a ZIP file of resumes and a job description.
#     Parses resumes, compares them to the JD, and returns a match report.
#     """
#     # Check if a file was uploaded
#     if 'resume_zip' not in request.files:
#         return jsonify({'error': 'No resume ZIP file provided'}), 400

#     resume_zip = request.files['resume_zip']
#     job_description = request.form.get('job_description', '')

#     if resume_zip.filename == '':
#         return jsonify({'error': 'No selected file for resumes'}), 400

#     if not job_description:
#         return jsonify({'error': 'No job description provided'}), 400

#     # Secure filename for the ZIP file
#     zip_filename = secure_filename(resume_zip.filename)
#     zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)

#     # Save the uploaded ZIP file
#     try:
#         resume_zip.save(zip_path)
#     except Exception as e:
#         return jsonify({'error': f'Failed to save ZIP file: {e}'}), 500

#     results = []
#     temp_extract_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_resumes')
#     if not os.path.exists(temp_extract_dir):
#         os.makedirs(temp_extract_dir)

#     try:
#         # Extract resumes from the ZIP file
#         with zipfile.ZipFile(zip_path, 'r') as zf:
#             zf.extractall(temp_extract_dir)

#         # Preprocess the job description once
#         jd_tokens = preprocess_text(job_description)

#         # Process each extracted resume
#         for root, _, files in os.walk(temp_extract_dir):
#             for filename in files:
#                 file_path = os.path.join(root, filename)
#                 candidate_name = os.path.splitext(filename)[0] # Default to filename without extension

#                 resume_text = None
#                 if filename.lower().endswith('.pdf'):
#                     resume_text = extract_text_from_pdf(file_path)
#                 elif filename.lower().endswith(('.doc', '.docx')): # Basic check for doc/docx
#                     # If it's a .doc, it might require extra libraries or conversion.
#                     # For simplicity, we'll only handle .docx directly with python-docx.
#                     # A more robust solution might involve libreoffice for .doc conversion.
#                     if filename.lower().endswith('.docx'):
#                         resume_text = extract_text_from_docx(file_path)
#                     else:
#                         print(f"Skipping unsupported file type: {filename}")
#                         continue
#                 else:
#                     print(f"Skipping unsupported file type: {filename}")
#                     continue

#                 if resume_text:
#                     # Attempt to get a better candidate name from the resume content
#                     extracted_name = get_candidate_name_from_text(resume_text)
#                     if extracted_name != "Unknown Candidate":
#                         candidate_name = extracted_name

#                     resume_tokens = preprocess_text(resume_text)
#                     match_percentage, top_skills, missing_skills = calculate_match_score(resume_tokens, jd_tokens)

#                     results.append({
#                         'candidate_name': candidate_name,
#                         'match_percentage': match_percentage,
#                         'top_skills': top_skills,
#                         'missing_skills': missing_skills
#                     })

#     except zipfile.BadZipFile:
#         return jsonify({'error': 'Uploaded file is not a valid ZIP file.'}), 400
#     except Exception as e:
#         return jsonify({'error': f'An error occurred during resume processing: {e}'}), 500
#     finally:
#         # Clean up uploaded ZIP and extracted files
#         if os.path.exists(zip_path):
#             os.remove(zip_path)
#         if os.path.exists(temp_extract_dir):
#             import shutil
#             shutil.rmtree(temp_extract_dir)

#     # Sort results by match percentage in descending order
#     results.sort(key=lambda x: x['match_percentage'], reverse=True)

#     return jsonify({'message': 'Resumes processed successfully', 'results': results})


# --- Flask Routes ---

@app.route('/api/match_resumes', methods=['POST'])
def match_resumes():
    """
    API endpoint to receive a ZIP file of resumes and a job description.
    Parses resumes, compares them to the JD, and returns a match report
    with only Email, Name, Match %, and File Name.
    """
    if 'resume_zip' not in request.files:
        return jsonify({'error': 'No resume ZIP file provided'}), 400

    resume_zip = request.files['resume_zip']
    job_description = request.form.get('job_description', '')

    if resume_zip.filename == '':
        return jsonify({'error': 'No selected file for resumes'}), 400
    if not job_description:
        return jsonify({'error': 'No job description provided'}), 400

    zip_filename = secure_filename(resume_zip.filename)
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
    try:
        resume_zip.save(zip_path)
    except Exception as e:
        return jsonify({'error': f'Failed to save ZIP file: {e}'}), 500

    results = []
    temp_extract_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_resumes')
    if not os.path.exists(temp_extract_dir):
        os.makedirs(temp_extract_dir)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(temp_extract_dir)

        jd_tokens = preprocess_text(job_description)

        for root, _, files in os.walk(temp_extract_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                candidate_name = os.path.splitext(filename)[0]  

                resume_text = None
                if filename.lower().endswith('.pdf'):
                    resume_text = extract_text_from_pdf(file_path)
                elif filename.lower().endswith('.docx'):
                    resume_text = extract_text_from_docx(file_path)
                else:
                    print(f"Skipping unsupported file type: {filename}")
                    continue

                if resume_text:
                    extracted_name = get_candidate_name_from_text(resume_text)
                    if extracted_name != "Unknown Candidate":
                        candidate_name = extracted_name

                    resume_tokens = preprocess_text(resume_text)
                    match_percentage, _, _ = calculate_match_score(resume_tokens, jd_tokens)

                    # Extract email with regex
                    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', resume_text)
                    email = email_match.group(0) if email_match else "Not Found"

                    results.append({
                        'email': email,
                        'candidate_name': candidate_name,
                        'match_percentage': round(match_percentage, 2),
                        'file_name': filename
                    })

    except zipfile.BadZipFile:
        return jsonify({'error': 'Uploaded file is not a valid ZIP file.'}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred during resume processing: {e}'}), 500
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        if os.path.exists(temp_extract_dir):
            import shutil
            shutil.rmtree(temp_extract_dir)

    results.sort(key=lambda x: x['match_percentage'], reverse=True)

    return jsonify({'message': 'Resumes processed successfully', 'results': results})

@app.route('/api/export/pdf', methods=['POST'])
def export_pdf():
    """
    Export matching results to PDF.
    Expects JSON body: { "results": [ { "candidate_name":.., "email":.., "match_percentage":.., "file_name":.. } ] }
    """
    data = request.get_json()
    results = data.get("results", [])

    if not results:
        return jsonify({"error": "No results provided"}), 400

    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], "match_report.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, height - 40, "Resume Match Report")

    y = height - 80
    c.setFont("Helvetica", 10)
    for idx, result in enumerate(results, start=1):
        line = f"{idx}. {result['candidate_name']} | {result['email']} | {result['match_percentage']}% | {result['file_name']}"
        c.drawString(40, y, line)
        y -= 20
        if y < 40:  # Create new page if space ends
            c.showPage()
            y = height - 40

    c.save()
    return send_file(pdf_path, as_attachment=True, download_name="match_report.pdf")

# ---------------- EXPORT AS EXCEL ----------------
@app.route('/api/export/excel', methods=['POST'])
def export_excel():
    """
    Export matching results to Excel.
    Expects JSON body: { "results": [...] }
    """
    data = request.get_json()
    results = data.get("results", [])

    if not results:
        return jsonify({"error": "No results provided"}), 400

    df = pd.DataFrame(results)
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], "match_report.xlsx")
    df.to_excel(excel_path, index=False)

    return send_file(excel_path, as_attachment=True, download_name="match_report.xlsx")


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, port=5000) # Run on port 5000 for development
