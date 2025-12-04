export default function QueryEngine() {
  return (
    <div className="max-w-4xl mx-auto h-full flex flex-col">
      <h1 className="text-2xl font-bold text-slate-800 mb-4">Query Engine</h1>
      <div className="flex-1 bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex items-center justify-center text-slate-400">
        Chat Interface Coming Soon...
      </div>
      <div className="mt-4 flex gap-2">
        <input type="text" placeholder="Ask about safety protocols..." className="flex-1 p-3 border rounded-lg" />
        <button className="bg-blue-600 text-white px-6 rounded-lg font-medium">Send</button>
      </div>
    </div>
  );
}