import { useState, useRef } from 'react';
import { Upload, FileText, FileCode, FileType, Loader, AlertCircle, CheckCircle } from 'lucide-react';

export default function IngestionEngine() {
  const [logs, setLogs] = useState(["> System Ready...", "> Waiting for file input..."]);
  const [isProcessing, setIsProcessing] = useState(false);
  const fileInputRef = useRef(null);

  const addLog = (msg) => setLogs(prev => [...prev, `> ${msg}`]);

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // UI Updates
    setIsProcessing(true);
    addLog(`File detected: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`);
    addLog("Uploading to Analysis Engine...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      // Sending to backend (It handles DOCX/TXT/PDF automatically)
      const response = await fetch("http://localhost:8000/process-pdf", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (data.status === "success") {
        addLog(`Parsing Complete for ${file.name} ✅`);
        addLog("Extracted Content Preview:");
        addLog("--------------------------------");
        // Show a preview of the text
        addLog(data.markdown_content.substring(0, 150) + "...");
      } else {
        addLog(`Error: ${data.message} ❌`);
      }

    } catch (error) {
      addLog("Connection Failed. Is the backend running? ❌");
      console.error(error);
    } finally {
      setIsProcessing(false);
      // Reset input so you can upload the same file again if needed
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Document Ingestion Engine</h1>
      
      {/* 1. ALLOWED FORMATS UPDATED HERE */}
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileSelect} 
        className="hidden" 
        accept=".pdf,.docx,.doc,.txt,.md,.html"
      />

      {/* Upload Zone */}
      <div 
        onClick={() => !isProcessing && fileInputRef.current.click()}
        className={`border-2 border-dashed border-slate-300 rounded-xl p-12 text-center bg-white hover:bg-slate-50 transition cursor-pointer mb-8 relative ${isProcessing ? 'opacity-75 pointer-events-none' : ''}`}
      >
        <div className="w-20 h-20 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
          {isProcessing ? (
            <Loader className="animate-spin" size={40} />
          ) : (
            <div className="relative">
              <Upload size={40} />
              {/* Decorative Icons for formats */}
              <FileText size={16} className="absolute -bottom-1 -right-2 text-slate-500" />
              <FileCode size={16} className="absolute -bottom-1 -left-2 text-slate-500" />
            </div>
          )}
        </div>
        
        <h3 className="text-xl font-semibold text-slate-700">
          {isProcessing ? "Analyzing Document Structure..." : "Drop Any Document Here"}
        </h3>
        
        <div className="flex justify-center gap-2 mt-3">
            <span className="px-2 py-1 bg-slate-100 text-slate-600 text-xs rounded-md font-mono">.PDF</span>
            <span className="px-2 py-1 bg-slate-100 text-slate-600 text-xs rounded-md font-mono">.DOCX</span>
            <span className="px-2 py-1 bg-slate-100 text-slate-600 text-xs rounded-md font-mono">.TXT</span>
            <span className="px-2 py-1 bg-slate-100 text-slate-600 text-xs rounded-md font-mono">.MD</span>
        </div>
      </div>

      {/* Terminal Output */}
      <div className="bg-slate-900 rounded-lg p-4 shadow-xl font-mono text-sm h-64 overflow-y-auto border border-slate-700 flex flex-col-reverse">
        {/* flex-col-reverse keeps the latest log at the bottom automatically */}
        <div className="space-y-1">
          {logs.map((log, i) => (
            <div key={i} className={`break-words ${log.includes('❌') ? 'text-red-400' : log.includes('✅') ? 'text-green-400' : 'text-slate-300'}`}>
              {log}
            </div>
          ))}
          <div className="animate-pulse text-blue-400 pt-2">_</div>
        </div>
      </div>
    </div>
  );
}