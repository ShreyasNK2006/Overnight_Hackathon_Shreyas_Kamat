import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, FileText, Calendar, Hash } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function QueryEngine() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    
    // Add user message
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: userMessage,
          top_k: 5 
        })
      });

      if (!response.ok) throw new Error('Query failed');

      const data = await response.json();
      
      // Add assistant message with sources
      setMessages(prev => [...prev, { 
        type: 'assistant', 
        content: data.answer,
        sources: data.sources,
        processingTime: data.processing_time_ms
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        type: 'error', 
        content: `Error: ${error.message}. Make sure the API server is running at ${API_BASE}` 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto h-full flex flex-col">
      <h1 className="text-2xl font-bold text-slate-800 mb-4">Query Engine</h1>
      
      {/* Chat Messages */}
      <div className="flex-1 bg-gradient-to-b from-slate-50 to-white rounded-xl shadow-lg border border-slate-200 p-6 overflow-y-auto mb-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center text-slate-400">
              <FileText size={48} className="mx-auto mb-4 text-slate-300" />
              <p className="text-lg font-medium">Ask questions about your infrastructure documents</p>
              <p className="text-sm mt-2">Try: "What sensors are used for heart rate monitoring?"</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg, idx) => (
              <div key={idx}>
                {msg.type === 'user' && (
                  <div className="flex justify-end">
                    <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-2xl px-5 py-3 max-w-2xl shadow-md">
                      <p className="font-medium">{msg.content}</p>
                    </div>
                  </div>
                )}
                
                {msg.type === 'assistant' && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-slate-200 rounded-2xl px-5 py-4 max-w-3xl shadow-md">
                      <div className="text-slate-800 whitespace-pre-wrap leading-relaxed">{msg.content}</div>
                      
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-slate-200">
                          <p className="text-xs font-bold text-slate-700 mb-3 tracking-wide">📚 SOURCES ({msg.sources.length})</p>
                          <div className="space-y-2">
                            {msg.sources.map((source, i) => (
                              <div key={i} className="text-xs bg-gradient-to-r from-blue-50 to-slate-50 rounded-lg p-3 border border-blue-200 hover:border-blue-300 transition-colors">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-bold text-blue-600">[Source {source.source_number}]</span>
                                  <span className="text-slate-500">•</span>
                                  <span className="font-medium text-slate-700">{source.document}</span>
                                </div>
                                <div className="flex items-center gap-3 text-slate-500">
                                  <span className="flex items-center gap-1">
                                    <Hash size={12} />
                                    Page {source.page}
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <FileText size={12} />
                                    {source.section}
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <Calendar size={12} />
                                    {new Date(source.timestamp).toLocaleDateString()}
                                  </span>
                                </div>
                                <div className="mt-1 text-slate-400">
                                  Relevance: {(source.similarity_score * 100).toFixed(1)}%
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {msg.processingTime && (
                        <div className="mt-2 text-xs text-slate-400">
                          Processed in {msg.processingTime.toFixed(0)}ms
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {msg.type === 'error' && (
                  <div className="flex justify-center">
                    <div className="bg-red-50 text-red-600 rounded-lg px-4 py-3 text-sm">
                      {msg.content}
                    </div>
                  </div>
                )}
              </div>
            ))}
            
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-slate-200 rounded-2xl px-5 py-3 flex items-center gap-2 shadow-md">
                  <Loader2 className="animate-spin text-blue-600" size={18} />
                  <span className="text-slate-700 font-medium">Analyzing documents...</span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
      
      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your documents..." 
          className="flex-1 p-4 border-2 border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm"
          disabled={loading}
        />
        <button 
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-8 rounded-xl font-semibold hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-md transition-all"
        >
          {loading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
        </button>
      </form>
    </div>
  );
}