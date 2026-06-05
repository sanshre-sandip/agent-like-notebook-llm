import React, { useState, useEffect, useRef } from 'react';
import './App.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface Source {
  name: string;
  status: 'indexed' | 'uploading' | 'error';
}

interface User {
  email: string;
  name: string;
}

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sources, setSources] = useState<Source[]>([]);
  const [isAuthChecking, setIsAuthChecking] = useState(true);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Check if user is authenticated
    const checkAuth = async () => {
      try {
        const response = await fetch('http://localhost:8000/auth/me', { credentials: 'include' });
        if (response.ok) {
          const data = await response.json();
          setUser(data);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setIsAuthChecking(false);
      }
    };
    checkAuth();
  }, []);

  const handleLogin = () => {
    window.location.href = 'http://localhost:8000/auth/login';
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const newSource: Source = { name: file.name, status: 'uploading' };
    setSources(prev => [...prev, newSource]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/rag/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Upload failed');

      setSources(prev => 
        prev.map(s => s.name === file.name ? { ...s, status: 'indexed' } : s)
      );
    } catch (error) {
      console.error('Error:', error);
      setSources(prev => 
        prev.map(s => s.name === file.name ? { ...s, status: 'error' } : s)
      );
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/rag/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          history: messages,
        }),
        credentials: 'include'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch response');
      }

      const data = await response.json();
      const assistantMessage: Message = { role: 'assistant', content: data.response };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Error:', error);
      const errorMessage: Message = { role: 'assistant', content: error.message || 'Sorry, something went wrong.' };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  if (isAuthChecking) {
    return <div className="loading-screen">Checking authentication...</div>;
  }

  if (!user) {
    return (
      <div className="login-screen">
        <h1>SANDYLLM</h1>
        <p>Production-ready RAG powered by Google Gemini</p>
        <button className="login-btn" onClick={handleLogin}>
          Sign in with Google
        </button>
      </div>
    );
  }

  return (
    <div className="notebook-layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>SANDYLLM</h2>
          <div className="user-info">{user.name}</div>
        </div>
        <div className="sources-section">
          <div className="section-title">
            <span>Sources</span>
            <button className="add-source-btn" onClick={() => fileInputRef.current?.click()}>+</button>
          </div>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            ref={fileInputRef}
            style={{ display: 'none' }}
          />
          <div className="sources-list">
            {sources.map((source, i) => (
              <div key={i} className={`source-item ${source.status}`}>
                <div className="source-icon">📄</div>
                <div className="source-info">
                  <div className="source-name">{source.name}</div>
                  <div className="source-status">{source.status}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="sidebar-footer">
           <button className="logout-btn" onClick={() => window.location.href = 'http://localhost:8000/auth/logout'}>Logout</button>
        </div>
      </aside>

      <main className="chat-area">
        <header className="chat-header">
          <div className="notebook-title">Research Workspace</div>
        </header>

        <div className="message-list">
          {messages.length === 0 && (
            <div className="welcome-hero">
              <h1>Welcome, {user.name.split(' ')[0]}</h1>
              <p>Your private SANDYLLM workspace is ready. Upload documents to begin.</p>
              <div className="suggested-actions">
                <button onClick={() => setInput("What can you help me with?")}>Quick Tour</button>
              </div>
            </div>
          )}
          {messages.map((msg, index) => (
            <div key={index} className={`message-row ${msg.role}`}>
              <div className="avatar">{msg.role === 'user' ? 'U' : 'S'}</div>
              <div className="message-content">
                <div className="sender-name">{msg.role === 'user' ? 'You' : 'SANDYLLM'}</div>
                <div className="text">{msg.content}</div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message-row assistant">
              <div className="avatar">S</div>
              <div className="message-content">
                <div className="sender-name">SANDYLLM</div>
                <div className="loading-dots">
                  <span>.</span><span>.</span><span>.</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <div className="input-box">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask a question about your sources..."
              rows={1}
            />
            <button className="send-btn" onClick={handleSend} disabled={isLoading || !input.trim()}>
              →
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
