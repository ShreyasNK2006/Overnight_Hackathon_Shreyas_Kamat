import { useState } from 'react';
import { Upload } from 'lucide-react';

export default function IngestionEngine() {
  const [logs, _setLogs] = useState(["> System Ready...", "> Waiting for file input..."]);

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Document Ingestion Engine</h1>

      <div className="border-2 border-dashed border-slate-300 rounded-xl p-12 text-center bg-white hover:bg-slate-50 transition cursor-pointer mb-8">
        <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <Upload size={32} />
        </div>
        <h3 className="text-lg font-semibold text-slate-700">Drop PDF Manuals Here</h3>
        <p className="text-slate-500 mt-2">Supports PDF, DOCX (Max 50MB)</p>
      </div>

      <div className="bg-slate-900 rounded-lg p-4 shadow-xl font-mono text-sm h-64 overflow-y-auto border border-slate-700">
        <div className="flex items-center gap-2 mb-4 border-b border-slate-700 pb-2">
          <span className="text-slate-400">processor_logs.txt</span>
        </div>
        <div className="space-y-1">
          {logs.map((log, i) => <div key={i} className="text-green-400">{log}</div>)}
          <div className="animate-pulse text-green-400">_</div>
        </div>
      </div>
    </div>
  );
}