# **Resume Matcher Backend**
This Flask backend powers the Resume Matcher application, designed to streamline the resume screening process for HR and recruiters. It automates the parsing of multiple resumes from a ZIP file, compares them against a specified job description, and generates a detailed match report.
## **✨ Features**
- **Bulk Resume Processing:** Accepts a ZIP file containing multiple resumes (PDF and DOCX formats).
- **Job Description Input:** Integrates a job description provided as plain text.
- **Text Extraction:** Extracts textual content from both PDF and DOCX resume files.
- **NLP Preprocessing:** Utilizes spaCy for tokenization, lemmatization, stopword removal, and cleaning of text from resumes and job descriptions.
- **Match Scoring:** Calculates a match percentage for each resume against the job description based on shared keywords/skills.
- **Skill Identification:** Identifies "top skills" (common to both resume and JD) and "missing skills" (JD requirements not found in the resume).
- **Dynamic Candidate Naming:** Attempts to extract candidate names directly from resume content for better reporting.
- **API Endpoint:** Provides a clean RESTful API endpoint for integration with a frontend.
- **Temporary File Handling:** Manages temporary storage and cleanup of uploaded ZIPs and extracted resumes.
## **🛠️ Tech Stack**
- **Backend Framework:** Flask (Python)
- **PDF Parsing:** pdfplumber
- **DOCX Parsing:** python-docx
- **Natural Language Processing (NLP):** spaCy (en\_core\_web\_sm model)
- **File Handling:** os, zipfile, werkzeug.utils
## **🚀 Getting Started**
Follow these steps to set up and run the backend server.
### **Prerequisites**
Ensure you have Python 3.8+ installed on your system.
### **Installation**
1. Clone this repository (or save the app.py file):\
   If you have the file, save it as app.py in your desired directory.
1. **Navigate to the project directory:**\
   cd your-project-directory
1. **Create a virtual environment (recommended):**\
   python -m venv venv
1. **Activate the virtual environment:**
   1. **On Windows:**\
      .\venv\Scripts\activate
   1. **On macOS/Linux:**\
      source venv/bin/activate
1. **Install the required Python packages:**\
   pip install Flask pdfplumber python-docx spacy
1. Download the spaCy English language model:\
   This model is crucial for NLP processing. The application will attempt to download it if missing, but you can do it manually:\
   python -m spacy download en\_core\_web\_sm
### **Running the Application**
Once all dependencies are installed, you can start the Flask development server:

python app.py

The backend will typically run on http://127.0.0.1:5000.
## **💡 API Endpoint**
The backend exposes a single API endpoint for processing resumes.
### **POST /api/match\_resumes**
This endpoint accepts a ZIP file containing resumes and a job description, processes them, and returns a JSON report.

- **URL:** /api/match\_resumes
- **Method:** POST
- **Content-Type:** multipart/form-data
### **Request Body Parameters**

|**Parameter**|**Type**|**Description**|**Required**|
| :- | :- | :- | :- |
|resume\_zip|File|A ZIP archive containing PDF and/or DOCX resume files.|Yes|
|job\_description|Text|The plain text content of the job description.|Yes|
### **Example curl Request (for testing)**
curl -X POST \\
`  `http://127.0.0.1:5000/api/match\_resumes \\
`  `-H 'Content-Type: multipart/form-data' \\
`  `-F 'resume\_zip=@"/path/to/your/resumes.zip"' \\
`  `-F 'job\_description="We are looking for a software engineer with strong Python, React, and database skills. Experience with Flask and NLP is a plus."'

*Replace /path/to/your/resumes.zip with the actual path to your ZIP file.*
### **Response Format (JSON)**
Upon successful processing, the API returns a JSON object containing a list of match results.

{\
`  `"message": "Resumes processed successfully",\
`  `"results": [\
`    `{\
`      `"candidate\_name": "John Doe",\
`      `"match\_percentage": 85.50,\
`      `"top\_skills": ["python", "react", "database"],\
`      `"missing\_skills": ["flask", "nlp"]\
`    `},\
`    `{\
`      `"candidate\_name": "Jane Smith",\
`      `"match\_percentage": 60.00,\
`      `"top\_skills": ["python", "database"],\
`      `"missing\_skills": ["react", "flask", "nlp"]\
`    `}\
`    `// ... more candidate results\
`  `]\
}
## **🧑‍💻 Core Logic Breakdown**
The backend orchestrates several key functions to achieve the resume matching:
### **File Extraction and Parsing**
- **extract\_text\_from\_pdf(pdf\_path):** Uses pdfplumber to extract text page-by-page from a given PDF file path.
- **extract\_text\_from\_docx(docx\_path):** Employs python-docx to read and concatenate text from paragraphs within a DOCX file.
- **get\_candidate\_name\_from\_text(text):** A heuristic function that attempts to parse a candidate's name from the initial lines of the extracted resume text using regular expressions to find capitalized word sequences.
### **NLP Preprocessing**
- **preprocess\_text(text):** This crucial function leverages spaCy to clean and normalize the raw text. It performs:
  - **Lowercasing:** Converts all text to lowercase.
  - **Tokenization:** Breaks down text into individual words or meaningful units.
  - **Stopword Removal:** Eliminates common words (e.g., "a", "the", "is") that carry little semantic value.
  - **Punctuation Removal:** Removes punctuation marks.
  - **Lemmatization:** Reduces words to their base or dictionary form (e.g., "running", "ran", "runs" all become "run"). This ensures consistent matching regardless of word conjugations.
### **Match Scoring**
- **calculate\_match\_score(resume\_tokens, jd\_tokens):** This function takes preprocessed lists of tokens (skills/keywords) from both the resume and the job description.
  - It converts these lists into sets for efficient identification of common and unique elements.
  - **common\_skills**: The intersection of the resume and JD token sets.
  - **match\_percentage**: Calculated as (number of common skills / total unique skills in JD) \* 100.
  - **top\_skills**: The skills found in both.
  - **missing\_skills**: The skills present in the JD but absent from the resume.
## **⚠️ Error Handling and Cleanup**
The backend includes robust error handling for various scenarios, such as missing files, invalid ZIP formats, and issues during file saving or processing. It ensures that all temporary uploaded ZIP files and extracted resume directories are removed from the server once processing is complete, regardless of whether the operation was successful or encountered an error.
## **📈 Future Enhancements**
- **Advanced NLP:** Implement more sophisticated NLP models (e.g., Hugging Face transformers for NER or sentence embeddings) for more accurate skill extraction and semantic matching.
- **Database Integration:** Add a database (e.g., SQLite, MongoDB) to store job descriptions, parsed resume data, and historical match reports.
- **Asynchronous Processing:** For larger datasets, integrate a task queue (e.g., Celery) to handle resume processing asynchronously, preventing timeouts for the frontend.
- **Report Export:** Implement functionality to export the match results directly to Excel or PDF format from the backend.
