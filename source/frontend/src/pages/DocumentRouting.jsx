import { useState } from 'react';
import { Route, Target, Send, Loader2, CheckCircle, User, Mail, Briefcase } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function DocumentRouting() {
  const [documentSummary, setDocumentSummary] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const exampleDocuments = [
    "Invoice for 50 tons of cement from supplier XYZ, total cost $15,000",
    "Safety incident report - worker fell from scaffolding on Level 3",
    "Blueprint approval needed for structural beam design in Building A",
    "Project timeline update for Phase 2 construction delayed by 2 weeks",
    "Concrete strength test results failing quality standards in Zone B"
  ];

  const handleRoute = async () => {
    if (!documentSummary.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/stakeholders/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_summary: documentSummary,
          top_k: 3,
          threshold: 0.6
        })
      });

      if (!response.ok) throw new Error('Routing failed');

      const data = await response.json();
      setResults(data);
    } catch (error) {
      alert('Failed to route document: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceBadge = (confidence) => {
    const colors = {
      high: 'bg-green-100 text-green-700',
      medium: 'bg-yellow-100 text-yellow-700',
      low: 'bg-red-100 text-red-700'
    };
    return colors[confidence] || 'bg-slate-100 text-slate-700';
  };

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
        <Route size={28} />
        Document Routing
      </h1>

      <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
        <h2 className="text-lg font-semibold mb-3">Document Summary</h2>
        
        <textarea
          value={documentSummary}
          onChange={(e) => setDocumentSummary(e.target.value)}
          placeholder="Enter document summary or content to find the best stakeholder..."
          className="w-full p-4 border-2 border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 h-32 mb-3"
        />

        <div className="flex flex-wrap gap-2 mb-4">
          <span className="text-sm text-slate-600">Examples:</span>
          {exampleDocuments.map((example, idx) => (
            <button
              key={idx}
              onClick={() => setDocumentSummary(example)}
              className="text-xs bg-blue-50 text-blue-600 px-3 py-1 rounded-full hover:bg-blue-100"
            >
              {example.slice(0, 40)}...
            </button>
          ))}
        </div>

        <button
          onClick={handleRoute}
          disabled={loading || !documentSummary.trim()}
          className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={20} />
              Finding best match...
            </>
          ) : (
            <>
              <Target size={20} />
              Route Document
            </>
          )}
        </button>
      </div>

      {results && (
        <div className="space-y-4">
          {results.fallback_used && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-2">
              <span className="text-yellow-600">⚠️</span>
              <div>
                <p className="font-medium text-yellow-800">Fallback Used</p>
                <p className="text-sm text-yellow-700">
                  No stakeholder matched above threshold. Routed to project manager as fallback.
                </p>
              </div>
            </div>
          )}

          <div className="bg-gradient-to-r from-blue-50 to-green-50 rounded-xl shadow-lg p-6 border-2 border-blue-200">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle size={24} className="text-green-600" />
              <h2 className="text-xl font-bold text-slate-800">Best Match</h2>
            </div>

            {results.best_match ? (
              <div className="bg-white rounded-lg p-6 shadow">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-2xl font-bold text-slate-800 mb-1">
                      {results.best_match.name}
                    </h3>
                    <p className="text-slate-600 flex items-center gap-2">
                      <Briefcase size={16} />
                      {results.best_match.role}
                    </p>
                  </div>
                  <span className={`px-4 py-2 rounded-full font-semibold text-sm ${getConfidenceBadge(results.best_match.confidence)}`}>
                    {results.best_match.confidence.toUpperCase()}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                  <div className="flex items-center gap-2 text-slate-600">
                    <Mail size={16} />
                    <a href={`mailto:${results.best_match.email}`} className="text-blue-600 hover:underline">
                      {results.best_match.email}
                    </a>
                  </div>
                  {results.best_match.phone && (
                    <div className="flex items-center gap-2 text-slate-600">
                      <span>📞</span>
                      {results.best_match.phone}
                    </div>
                  )}
                  {results.best_match.department && (
                    <div className="text-slate-600">
                      <span className="font-medium">Department:</span> {results.best_match.department}
                    </div>
                  )}
                  <div className="text-slate-600">
                    <span className="font-medium">Similarity:</span>{' '}
                    <span className="font-bold text-blue-600">
                      {(results.best_match.similarity * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                <div className="bg-slate-50 p-4 rounded-lg">
                  <p className="text-sm font-medium text-slate-700 mb-2">Responsibilities:</p>
                  <p className="text-sm text-slate-600">{results.best_match.responsibilities}</p>
                </div>
              </div>
            ) : (
              <p className="text-slate-600">No match found</p>
            )}
          </div>

          {results.matches && results.matches.length > 1 && (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Alternative Matches</h2>
              <div className="space-y-3">
                {results.matches.slice(1).map((match, idx) => (
                  <div key={idx} className="border border-slate-200 rounded-lg p-4 hover:border-blue-300 transition">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-semibold text-lg">{match.name}</h3>
                        <p className="text-sm text-slate-600">{match.role}</p>
                      </div>
                      <div className="text-right">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getConfidenceBadge(match.confidence)}`}>
                          {match.confidence}
                        </span>
                        <p className="text-sm text-slate-600 mt-1">
                          {(match.similarity * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                    <p className="text-sm text-slate-600">
                      <Mail size={12} className="inline mr-1" />
                      {match.email}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="text-center text-sm text-slate-500">
            Processed in {results.processing_time_ms.toFixed(0)}ms
          </div>
        </div>
      )}
    </div>
  );
}
