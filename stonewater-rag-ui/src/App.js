import React, { useState, useRef, useEffect } from 'react';
import './App.css';

export default function App() {
  const [apiUrl, setApiUrl] = useState(localStorage.getItem('apiUrl') || '');
  const [apiKey, setApiKey] = useState(localStorage.getItem('apiKey') || '');
  const [isLoggedIn, setIsLoggedIn] = useState(!!apiUrl && !!apiKey);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [showStats, setShowStats] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleLogin = async (e) => {
    e.preventDefault();

    if (!apiUrl || !apiKey) {
      alert('Please enter both API URL and API Key');
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/health`, {
        method: 'GET',
      });

      if (response.ok) {
        localStorage.setItem('apiUrl', apiUrl);
        localStorage.setItem('apiKey', apiKey);
        setIsLoggedIn(true);
        setMessages([]);
        // Load stats on login
        loadStats();
      } else {
        alert('Failed to connect to API. Check your URL and try again.');
      }
    } catch (error) {
      alert(`Connection error: ${error.message}`);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/stats`, {
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const syncDocuments = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${apiUrl}/api/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${apiKey}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMessages([
          ...messages,
          {
            type: 'system',
            content: `Documents synced! Processed: ${data.new_files_processed} files, Total: ${data.total_documents} documents`,
          },
        ]);
        loadStats();
      } else {
        alert('Error syncing documents');
      }
    } catch (error) {
      setMessages([
        ...messages,
        {
          type: 'system',
          content: `Error syncing documents: ${error.message}`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!inputValue.trim()) {
      return;
    }

    const userMessage = {
      type: 'user',
      content: inputValue,
    };

    setMessages([...messages, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch(`${apiUrl}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({ question: inputValue }),
      });

      if (response.ok) {
        const data = await response.json();
        const assistantMessage = {
          type: 'assistant',
          content: data.answer,
          citations: data.citations || [],
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        alert('Error querying API');
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          type: 'system',
          content: `Error: ${error.message}`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('apiUrl');
    localStorage.removeItem('apiKey');
    setIsLoggedIn(false);
    setApiUrl('');
    setApiKey('');
    setMessages([]);
  };

  if (!isLoggedIn) {
    return (
      <div style={styles.loginContainer}>
        <div style={styles.loginBox}>
          <h1 style={styles.title}>Stonewater RAG</h1>
          <p style={styles.subtitle}>Document Search & Query System</p>

          <form onSubmit={handleLogin}>
            <div style={styles.formGroup}>
              <label htmlFor="apiUrl">API URL:</label>
              <input
                id="apiUrl"
                type="text"
                placeholder="http://localhost:5001"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                style={styles.input}
              />
            </div>

            <div style={styles.formGroup}>
              <label htmlFor="apiKey">API Key:</label>
              <input
                id="apiKey"
                type="password"
                placeholder="Your API Key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                style={styles.input}
              />
            </div>

            <button type="submit" style={styles.button}>
              Connect
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Stonewater RAG</h1>
        <div style={styles.headerButtons}>
          <button onClick={syncDocuments} disabled={isLoading} style={styles.headerButton}>
            🔄 Sync Documents
          </button>
          <button
            onClick={() => setShowStats(!showStats)}
            style={styles.headerButton}
          >
            📊 Stats
          </button>
          <button onClick={handleLogout} style={styles.headerButton}>
            Logout
          </button>
        </div>
      </div>

      {showStats && stats && (
        <div style={styles.statsBox}>
          <h3>Document Statistics</h3>
          <p>Total Documents: {stats.documents?.total || 0}</p>
          <p>Total Chunks Indexed: {stats.vector_store?.total_chunks || 0}</p>
          {stats.documents?.by_type && (
            <div>
              <strong>By Type:</strong>
              <ul>
                {Object.entries(stats.documents.by_type).map(([type, count]) => (
                  <li key={type}>
                    {type}: {count}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div style={styles.messagesContainer}>
        {messages.length === 0 && (
          <div style={styles.emptyState}>
            <p>👋 Welcome! Ask me anything about your documents.</p>
            <p style={{ fontSize: '12px', color: '#666' }}>
              Start by syncing your documents above, then ask questions!
            </p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={
              msg.type === 'user'
                ? styles.userMessage
                : msg.type === 'assistant'
                ? styles.assistantMessage
                : styles.systemMessage
            }
          >
            <div style={styles.messageContent}>{msg.content}</div>

            {msg.citations && msg.citations.length > 0 && (
              <div style={styles.citations}>
                <strong>Sources:</strong>
                {msg.citations.map((citation, i) => (
                  <div key={i} style={styles.citation}>
                    <div style={styles.citationTitle}>
                      📄 {citation.file_name}
                    </div>
                    <div style={styles.citationDetails}>
                      {citation.doc_type && (
                        <span>
                          <strong>Type:</strong> {citation.doc_type} |{' '}
                        </span>
                      )}
                      {citation.client_project && (
                        <span>
                          <strong>Project:</strong> {citation.client_project} |{' '}
                        </span>
                      )}
                      {citation.page_start && (
                        <span>
                          <strong>Pages:</strong> {citation.page_start}
                          {citation.page_end !== citation.page_start
                            ? `-${citation.page_end}`
                            : ''}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div style={styles.systemMessage}>
            <div style={styles.loadingSpinner}>⏳ Processing...</div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} style={styles.inputForm}>
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Ask a question about your documents..."
          disabled={isLoading}
          style={styles.inputField}
        />
        <button type="submit" disabled={isLoading} style={styles.submitButton}>
          Send
        </button>
      </form>
    </div>
  );
}

const styles = {
  loginContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  loginBox: {
    backgroundColor: 'white',
    padding: '40px',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    width: '100%',
    maxWidth: '400px',
  },
  title: {
    fontSize: '28px',
    marginBottom: '8px',
    color: '#333',
  },
  subtitle: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '24px',
  },
  formGroup: {
    marginBottom: '16px',
  },
  input: {
    width: '100%',
    padding: '10px',
    borderRadius: '4px',
    border: '1px solid #ddd',
    fontSize: '14px',
    boxSizing: 'border-box',
  },
  button: {
    width: '100%',
    padding: '10px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    cursor: 'pointer',
  },
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    backgroundColor: '#fff',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  header: {
    padding: '16px 20px',
    borderBottom: '1px solid #e0e0e0',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerButtons: {
    display: 'flex',
    gap: '8px',
  },
  headerButton: {
    padding: '8px 16px',
    backgroundColor: '#f0f0f0',
    border: '1px solid #ddd',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
  },
  statsBox: {
    padding: '12px 20px',
    backgroundColor: '#f9f9f9',
    borderBottom: '1px solid #e0e0e0',
    fontSize: '13px',
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  emptyState: {
    textAlign: 'center',
    color: '#999',
    marginTop: '40px',
  },
  userMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#007bff',
    color: 'white',
    padding: '12px 16px',
    borderRadius: '8px',
    maxWidth: '70%',
  },
  assistantMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#f0f0f0',
    color: '#333',
    padding: '12px 16px',
    borderRadius: '8px',
    maxWidth: '85%',
  },
  systemMessage: {
    alignSelf: 'center',
    backgroundColor: '#fff3cd',
    color: '#856404',
    padding: '12px 16px',
    borderRadius: '8px',
    fontSize: '13px',
    maxWidth: '80%',
  },
  messageContent: {
    wordWrap: 'break-word',
    whiteSpace: 'pre-wrap',
    lineHeight: '1.4',
  },
  citations: {
    marginTop: '12px',
    paddingTop: '12px',
    borderTop: '1px solid rgba(0,0,0,0.1)',
    fontSize: '12px',
  },
  citation: {
    marginTop: '8px',
    paddingLeft: '12px',
    borderLeft: '3px solid #007bff',
  },
  citationTitle: {
    fontWeight: 'bold',
    marginBottom: '4px',
  },
  citationDetails: {
    fontSize: '11px',
    color: '#666',
    lineHeight: '1.3',
  },
  inputForm: {
    display: 'flex',
    gap: '8px',
    padding: '16px 20px',
    borderTop: '1px solid #e0e0e0',
    backgroundColor: '#fff',
  },
  inputField: {
    flex: 1,
    padding: '10px 12px',
    borderRadius: '4px',
    border: '1px solid #ddd',
    fontSize: '14px',
  },
  submitButton: {
    padding: '10px 20px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  loadingSpinner: {
    textAlign: 'center',
  },
};
