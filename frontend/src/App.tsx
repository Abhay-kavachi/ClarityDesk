import React, { useState } from 'react';
import NotesPanel from './components/NotesPanel';
import SummarizePanel from './components/SummarizePanel';
import AskPanel from './components/AskPanel';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('notes');
  const [documents] = useState([{ name: 'sample_meeting_notes.txt' }, { name: 'sample_email.txt' }]);

  return (
    <div className="layout-container">
      <div className="sidebar">
        <h2>ClarityDesk</h2>
        <div style={{ marginTop: '32px' }}>
          <h3 style={{ fontSize: '13px', color: 'var(--secondary-text)', textTransform: 'uppercase', marginBottom: '12px' }}>
            Uploaded Notes
          </h3>
          <ul style={{ listStyle: 'none' }}>
            {documents.map((doc, idx) => (
              <li key={idx} style={{ marginBottom: '8px', fontSize: '14px' }}>
                <span style={{ marginRight: '8px' }}>📄</span>
                {doc.name}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="main-content">
        <div className="top-nav">
          <button 
            className={`nav-tab ${activeTab === 'summarize' ? 'active' : ''}`}
            onClick={() => setActiveTab('summarize')}
          >
            Summarize Email
          </button>
          <button 
            className={`nav-tab ${activeTab === 'notes' ? 'active' : ''}`}
            onClick={() => setActiveTab('notes')}
          >
            Process Notes
          </button>
          <button 
            className={`nav-tab ${activeTab === 'ask' ? 'active' : ''}`}
            onClick={() => setActiveTab('ask')}
          >
            Ask Past Notes
          </button>
        </div>

        <div className="panel-container">
          {activeTab === 'notes' && <NotesPanel />}
          {activeTab === 'summarize' && <SummarizePanel />}
          {activeTab === 'ask' && <AskPanel />}
        </div>
      </div>
    </div>
  );
}

export default App;
