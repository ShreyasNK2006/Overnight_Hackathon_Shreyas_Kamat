import { useState, useRef } from 'react';
import { Upload, CheckCircle, XCircle, Loader2, FileText } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function IngestionEngine() {
  const [logs, setLogs] = useState([
    { text: "> System Ready...", type: "info" },
    { text: "> Waiting for file input...", type: "info" }
  ]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const addLog = (text, type = "info") => {
    setLogs(prev => [...prev, { text, type, timestamp: new Date().toISOString() }]);
  };

  const handleFile = async (file) => {
    if (!file) return;

    // Validate file type
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!validTypes.includes(file.type)) {
      addLog(`✗ Error: Invalid file type. Only PDF and DOCX are supported.`, "error");
      return;
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
      addLog(`✗ Error: File too large. Maximum size is 50MB.`, "error");
      return;
    }

    setUploading(true);
    addLog(`> Processing ${file.name}...`, "info");
    addLog(`> File size: ${(file.size / 1024 / 1024).toFixed(2)}MB`, "info");

    try {
      const formData = new FormData();
      formData.append('file', file);

      addLog(`> Uploading to ingestion pipeline...`, "info");
      
      const response = await fetch(`${API_BASE}/ingest`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
      }

      const data = await response.json();
      
      addLog(`✓ Document ingested successfully!`, "success");
      addLog(`> Parent nodes: ${data.stats.parent_nodes}`, "info");
      addLog(`> Child vectors: ${data.stats.child_vectors}`, "info");
      addLog(`> Tables processed: ${data.stats.tables_processed}`, "info");
      addLog(`> Text sections: ${data.stats.text_sections}`, "info");
      addLog(`> Images uploaded: ${data.stats.images_uploaded}`, "info");
      addLog(`> Processing time: ${data.processing_time_ms.toFixed(0)}ms`, "info");
      addLog(`> Ready for queries!`, "success");
      
    } catch (error) {
      addLog(`✗ Ingestion failed: ${error.message}`, "error");
      addLog(`> Make sure API server is running at ${API_BASE}`, "error");
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const getLogColor = (type) => {
    switch(type) {
      case 'success': return 'text-green-400';
      case 'error': return 'text-red-400';
      case 'warning': return 'text-yellow-400';
      default: return 'text-green-400';
    }
  };

  const getLogIcon = (type) => {
    switch(type) {
      case 'success': return <CheckCircle size={14} className="inline mr-1" />;
      case 'error': return <XCircle size={14} className="inline mr-1" />;
      default: return null;
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Document Ingestion Engine</h1>

      <div 
        className={`border-2 border-dashed rounded-xl p-12 text-center bg-white transition cursor-pointer mb-8 ${
          dragActive 
            ? 'border-blue-500 bg-blue-50' 
            : uploading 
            ? 'border-slate-300 bg-slate-50 cursor-not-allowed'
            : 'border-slate-300 hover:bg-slate-50'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
      >
        <input 
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx"
          onChange={(e) => e.target.files && handleFile(e.target.files[0])}
          className="hidden"
          disabled={uploading}
        />
        
        <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 ${
          uploading ? 'bg-blue-100 text-blue-600' : 'bg-blue-100 text-blue-600'
        }`}>
          {uploading ? <Loader2 size={32} className="animate-spin" /> : <Upload size={32} />}
        </div>
        
        <h3 className="text-lg font-semibold text-slate-700">
          {uploading ? 'Processing Document...' : 'Drop PDF/DOCX Here'}
        </h3>
        <p className="text-slate-500 mt-2">
          {uploading ? 'Please wait...' : 'Supports PDF, DOCX (Max 50MB)'}
        </p>
        {!uploading && (
          <button className="mt-4 text-blue-600 font-medium hover:underline">
            or click to browse
          </button>
        )}
      </div>

      <div className="bg-slate-900 rounded-lg p-4 shadow-xl font-mono text-sm h-96 overflow-y-auto border border-slate-700">
        <div className="flex items-center gap-2 mb-4 border-b border-slate-700 pb-2">
          <FileText size={16} className="text-slate-400" />
          <span className="text-slate-400">processor_logs.txt</span>
        </div>
      </div>

      {/* Terminal Output */}
      <div className="bg-slate-900 rounded-lg p-4 shadow-xl font-mono text-sm h-64 overflow-y-auto border border-slate-700 flex flex-col-reverse">
        {/* flex-col-reverse keeps the latest log at the bottom automatically */}
        <div className="space-y-1">
          {logs.map((log, i) => (
            <div key={i} className={getLogColor(log.type)}>
              {getLogIcon(log.type)}
              {log.text}
            </div>
          ))}
          {uploading && <div className="animate-pulse text-green-400">_</div>}
        </div>
      </div>
    </div>
  );
}