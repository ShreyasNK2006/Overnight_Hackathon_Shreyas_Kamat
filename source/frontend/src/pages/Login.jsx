import { useNavigate } from 'react-router-dom';
import { ShieldCheck, User } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();

  const handleLogin = (role) => {
    localStorage.setItem('userRole', role);
    navigate('/dashboard/query');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-slate-800">InfraMind</h1>
          <p className="text-slate-500 mt-2">Intelligent Infrastructure RAG System</p>
        </div>

        <div className="space-y-4">
          <button onClick={() => handleLogin('admin')} className="w-full flex items-center justify-between bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-xl transition group">
            <div className="flex items-center gap-3">
              <ShieldCheck className="w-6 h-6 text-blue-200" />
              <div className="text-left">
                <div className="font-semibold">Admin Access</div>
                <div className="text-xs text-blue-200">Upload & Manage Documents</div>
              </div>
            </div>
          </button>

          <button onClick={() => handleLogin('employee')} className="w-full flex items-center justify-between bg-slate-100 hover:bg-slate-200 text-slate-800 p-4 rounded-xl transition group border border-slate-200">
            <div className="flex items-center gap-3">
              <User className="w-6 h-6 text-slate-500" />
              <div className="text-left">
                <div className="font-semibold">Employee Login</div>
                <div className="text-xs text-slate-500">Query Knowledge Base</div>
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}