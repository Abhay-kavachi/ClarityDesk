import React, { useState } from 'react';
import { AlertCircle, Search, Upload } from 'lucide-react';

interface QAResult {
  answer: str;
  source_citation?: str;
  matched_text?: str;
  found: boolean;
}

const AskPanel: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<QAResult | null>(null);
  const [error, setError] = useState<str | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    
    setIsUploading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('http://localhost:8000/api/documents', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Upload failed');
      // Success logic here (could update sidebar list)
    } catch (err) {
      setError('Failed to upload document.');
      console.error(err);
    } finally {
      setIsUploading(false);
      e.target.value = ''; // reset file input
    }
  };

  const askQuestion = async () => {
    if (!question.trim()) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      
      if (!response.ok) {
        throw new Error('Failed to ask question');
      }
      
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError('Something went wrong asking the question.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: '16px' }}>Ask Past Notes</h2>
      <p style={{ color: 'var(--secondary-text)', marginBottom: '24px' }}>
        Ask questions about any document you've uploaded. The AI will strictly use your documents to answer.
      </p>

      <div style={{ marginBottom: '24px' }}>
        <input 
          type="file" 
          id="fileUpload" 
          style={{ display: 'none' }} 
          onChange={handleFileUpload}
          accept=".txt,.pdf,.docx"
        />
        <label htmlFor="fileUpload" className="btn-outline" style={{ cursor: 'pointer' }}>
          <Upload size={16} /> 
          {isUploading ? 'Uploading...' : 'Upload Document'}
        </label>
      </div>

      <div style={{ display: 'flex', gap: '12px', marginBottom: '32px' }}>
        <input 
          type="text" 
          className="input-area"
          style={{ minHeight: 'auto', marginBottom: 0, padding: '12px 16px' }}
          placeholder="e.g. What did we decide about the grant deadline?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && askQuestion()}
        />
        <button 
          className="btn-primary" 
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          onClick={askQuestion}
          disabled={isLoading || !question.trim()}
        >
          <Search size={16} />
          {isLoading ? 'Searching...' : 'Ask'}
        </button>
      </div>

      {error && (
        <div className="card" style={{ borderLeft: '4px solid var(--error-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--error-color)' }}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        </div>
      )}

      {result && (
        <div className="card">
          <h3 style={{ fontSize: '16px', marginBottom: '12px', color: 'var(--secondary-text)' }}>Answer</h3>
          <p style={{ fontSize: '16px', marginBottom: '24px', fontWeight: 500 }}>
            {result.answer}
          </p>
          
          {result.found && result.source_citation && (
            <div style={{ backgroundColor: '#F9F9F8', padding: '16px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '13px', color: 'var(--secondary-text)', fontFamily: 'monospace', marginBottom: '8px' }}>
                {result.source_citation}
              </div>
              {result.matched_text && (
                <div>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: '#666', marginBottom: '4px', textTransform: 'uppercase' }}>
                    Matched Text:
                  </div>
                  <div style={{ fontSize: '14px', fontStyle: 'italic', color: '#444' }}>
                    "{result.matched_text}"
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AskPanel;
