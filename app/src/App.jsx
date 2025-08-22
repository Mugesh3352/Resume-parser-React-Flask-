import React, { useState } from 'react';
import './App.css';

const App = () => {
  const [resumeZipFile, setResumeZipFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [matchingResults, setMatchingResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);

  // Handle file drag & drop
  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.name.endsWith('.zip')) {
      setResumeZipFile(file);
      setError('');
    } else {
      setError('Only ZIP files are allowed.');
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  // Handle normal file input
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file && file.name.endsWith('.zip')) {
      setResumeZipFile(file);
      setError('');
    } else {
      setError('Only ZIP files are allowed.');
    }
  };

  // Handle JD input
  const handleJobDescriptionChange = (event) => {
    setJobDescription(event.target.value);
    setError('');
  };

  // Submit form
  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!resumeZipFile || !jobDescription.trim()) {
      setError('Please upload a ZIP file and paste a job description.');
      return;
    }

    setLoading(true);
    setError('');
    setMatchingResults([]);
    setUploadProgress(30);

    const formData = new FormData();
    formData.append('resume_zip', resumeZipFile);
    formData.append('job_description', jobDescription);

    try {
      const response = await fetch('http://localhost:5000/api/match_resumes', {
        method: 'POST',
        body: formData,
      });

      setUploadProgress(70);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || ' Failed to process resumes.');
      }

      setUploadProgress(100);
      setMatchingResults(data.results || []);
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="container">
        <h1 className="title">Resume Matcher</h1>
        <p className="subtitle">Upload resumes (ZIP) + paste job description → Get a skill match report.</p>

        {/* Drag & Drop Upload Box */}
        <div
            className="upload-box"
            onClick={() => document.getElementById('resume_zip').click()}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            >
            {resumeZipFile ? (
                <p className="file-selected"> {resumeZipFile.name}</p>
            ) : (
                <p>Drag & drop ZIP here, or <span className="file-link">browse</span></p>
            )}
            <input
                type="file"
                id="resume_zip"
                accept=".zip"
                onChange={handleFileChange}
                hidden
            />
        </div>

        {/* Progress bar */}
        {uploadProgress > 0 && (
          <div className="progress-bar">
            <div className="progress" style={{ width: `${uploadProgress}%` }}></div>
          </div>
        )}

        {/* Job Description */}
        <div className="form-group">
          <label htmlFor="job_description">Job Description</label>
          <textarea
            id="job_description"
            value={jobDescription}
            onChange={handleJobDescriptionChange}
            rows="6"
            placeholder="Paste the job description here..."
          />
        </div>

        <button type="button" disabled={loading} className="btn-primary" onClick={handleSubmit}>
          {loading ? '⏳ Processing...' : '🔍 Generate Match Report'}
        </button>

        {/* Error Alert */}
        {error && (
          <div className="alert error">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Results */}
        {matchingResults.length > 0 && (
          <div className="results">
            <h2 className="results-title">📊 Match Report</h2>
            <div className="table-container">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Candidate</th>
                    <th>Email</th>
                    <th>Match %</th>
                  </tr>
                </thead>
                <tbody>
                  {matchingResults.map((result, index) => (
                    <tr key={index}>
                      <td>{result.candidate_name}</td>
                      <td>{result.email}</td>
                      <td className="match">{result.match_percentage?.toFixed(2)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Export */}
            <div className="export">
            <button 
                className="btn-secondary" 
                onClick={async () => {
                const response = await fetch("http://localhost:5000/api/export/excel", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ results: matchingResults })
                });
                const blob = await response.blob();
                const link = document.createElement("a");
                link.href = window.URL.createObjectURL(blob);
                link.download = "match_report.xlsx";
                link.click();
                }}
            >
                📥 Export Excel
            </button>

            <button 
                className="btn-secondary"
                onClick={async () => {
                const response = await fetch("http://localhost:5000/api/export/pdf", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ results: matchingResults })
                });
                const blob = await response.blob();
                const link = document.createElement("a");
                link.href = window.URL.createObjectURL(blob);
                link.download = "match_report.pdf";
                link.click();
                }}
            >
                📥 Export PDF
            </button>
            </div>

          </div>
        )}
      </div>
    </div>
  );
};

export default App;
