import React, { useState } from 'react';
import { Download, Copy, AlertCircle } from 'lucide-react';

interface ActionItem {
  task: str;
  owner: str;
  deadline: str | null;
}

interface ProcessedNotes {
  meeting_title: str;
  meeting_date: str | null;
  summary: str;
  decisions: str[];
  action_items: ActionItem[];
  confidence: 'high' | 'medium' | 'low';
  confidence_note?: str;
}

const NotesPanel: React.FC = () => {
  const [notes, setNotes] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ProcessedNotes | null>(null);
  const [error, setError] = useState<str | null>(null);

  const processNotes = async () => {
    if (!notes.trim()) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/process-notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes })
      });
      
      if (!response.ok) {
        throw new Error('Failed to process notes');
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

  const exportCsv = () => {
    if (!result || result.action_items.length === 0) return;
    
    const headers = ['Task', 'Owner', 'Deadline'];
    const rows = result.action_items.map(item => 
      [
        `"${item.task.replace(/"/g, '""')}"`, 
        `"${item.owner}"`, 
        `"${item.deadline || ''}"`
      ].join(',')
    );
    
    const csvContent = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `action_items_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div>
      <h2 style={{ marginBottom: '16px' }}>Meeting Notes Processor</h2>
      <p style={{ color: 'var(--secondary-text)', marginBottom: '24px' }}>
        Paste your raw meeting notes below. We'll extract a clean summary, decisions, and trackable action items.
      </p>

      <textarea 
        className="input-area"
        placeholder="e.g. march 12 call - maya, jose, priya&#10;discussed grant deadline - jose said he'd check w funder by fri..."
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />

      <div style={{ marginBottom: '32px' }}>
        <button 
          className="btn-primary" 
          onClick={processNotes}
          disabled={isLoading || !notes.trim()}
        >
          {isLoading ? 'Extracting action items...' : 'Process Notes'}
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
            <h3 style={{ fontSize: '18px' }}>{result.meeting_title}</h3>
            <span className={`badge ${result.confidence}`}>
              Confidence: {result.confidence}
            </span>
          </div>
          
          {result.meeting_date && (
            <p style={{ color: 'var(--secondary-text)', fontSize: '14px', marginBottom: '16px' }}>
              Date: {result.meeting_date}
            </p>
          )}

          <div style={{ marginBottom: '24px' }}>
            <h4 style={{ marginBottom: '8px' }}>Summary</h4>
            <p>{result.summary}</p>
          </div>

          {result.decisions.length > 0 && (
            <div style={{ marginBottom: '24px' }}>
              <h4 style={{ marginBottom: '8px' }}>Decisions Made</h4>
              <ul style={{ paddingLeft: '20px' }}>
                {result.decisions.map((decision, idx) => (
                  <li key={idx}>{decision}</li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <div className="flex-between" style={{ marginBottom: '12px' }}>
              <h4 style={{ margin: 0 }}>Action Items ({result.action_items.length})</h4>
              <button className="btn-outline" onClick={exportCsv}>
                <Download size={16} /> Export CSV
              </button>
            </div>
            
            {result.action_items.length > 0 ? (
              <table className="action-table">
                <thead>
                  <tr>
                    <th>Task</th>
                    <th>Owner</th>
                    <th>Deadline</th>
                  </tr>
                </thead>
                <tbody>
                  {result.action_items.map((item, idx) => (
                    <tr key={idx}>
                      <td>{item.task}</td>
                      <td>{item.owner}</td>
                      <td>{item.deadline || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p style={{ color: 'var(--secondary-text)' }}>No action items identified.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotesPanel;
