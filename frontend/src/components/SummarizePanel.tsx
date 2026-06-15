import React, { useState } from 'react';
import { AlertCircle, Copy, CheckCircle2 } from 'lucide-react';

interface EmailSummary {
  summary: str;
  action_items: str[];
  deadlines: str;
  reply_urgency: 'urgent' | 'normal' | 'no-reply-needed';
  reply_tone?: str;
}

const SummarizePanel: React.FC = () => {
  const [emailContent, setEmailContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<EmailSummary | null>(null);
  const [error, setError] = useState<str | null>(null);
  const [copied, setCopied] = useState(false);

  const processEmail = async () => {
    if (!emailContent.trim()) return;
    
    setIsLoading(true);
    setError(null);
    setCopied(false);
    
    try {
      const response = await fetch('http://localhost:8000/api/summarize-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_content: emailContent })
      });
      
      if (!response.ok) {
        throw new Error('Failed to summarize email');
      }
      
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError('Something went wrong processing this file. Try pasting the text directly instead.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const copySummary = () => {
    if (!result) return;
    let text = result.summary + '\n\n';
    if (result.action_items.length > 0) {
      text += 'Action Items:\n' + result.action_items.map(item => `- ${item}`).join('\n') + '\n\n';
    }
    if (result.deadlines) text += `Deadlines: ${result.deadlines}\n`;
    
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div>
      <h2 style={{ marginBottom: '16px' }}>Email Summarizer</h2>
      <p style={{ color: 'var(--secondary-text)', marginBottom: '24px' }}>
        Paste a long email below. We'll give you a quick summary, extract action items, and suggest if you need to reply.
      </p>

      <textarea 
        className="input-area"
        placeholder="Paste email thread here..."
        value={emailContent}
        onChange={(e) => setEmailContent(e.target.value)}
      />

      <div style={{ marginBottom: '32px' }}>
        <button 
          className="btn-primary" 
          onClick={processEmail}
          disabled={isLoading || !emailContent.trim()}
        >
          {isLoading ? 'Summarizing...' : 'Summarize Email'}
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
          <div className="flex-between" style={{ marginBottom: '16px' }}>
            <h3 style={{ fontSize: '18px' }}>Summary</h3>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <span className={`badge ${result.reply_urgency === 'urgent' ? 'low' : result.reply_urgency === 'normal' ? 'medium' : ''}`}>
                Urgency: {result.reply_urgency.replace(/-/g, ' ')}
              </span>
              <button className="btn-outline" onClick={copySummary}>
                {copied ? <CheckCircle2 size={16} color="green" /> : <Copy size={16} />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>
          
          <p style={{ marginBottom: '24px', fontSize: '15px' }}>{result.summary}</p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            <div>
              <h4 style={{ marginBottom: '8px' }}>Action Items</h4>
              {result.action_items.length > 0 ? (
                <ul style={{ paddingLeft: '20px', color: 'var(--secondary-text)' }}>
                  {result.action_items.map((item, idx) => (
                    <li key={idx} style={{ marginBottom: '4px' }}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p style={{ color: 'var(--secondary-text)' }}>None identified.</p>
              )}
            </div>
            
            <div>
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ marginBottom: '4px' }}>Deadlines</h4>
                <p style={{ color: 'var(--secondary-text)' }}>{result.deadlines || 'None mentioned.'}</p>
              </div>
              
              {result.reply_tone && (
                <div>
                  <h4 style={{ marginBottom: '4px' }}>Suggested Tone</h4>
                  <p style={{ color: 'var(--secondary-text)' }}>{result.reply_tone}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SummarizePanel;
