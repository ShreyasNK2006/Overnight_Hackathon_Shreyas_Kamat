import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { MessageSquare, UploadCloud, LogOut, ShieldAlert, Users, Route, BarChart3 } from 'lucide-react';

export default function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const role = localStorage.getItem('userRole') || 'employee';

  const handleLogout = () => {
    localStorage.removeItem('userRole');
    navigate('/');
  };

  const isActive = (path) => location.pathname === path 
    ? "bg-blue-600 text-white" 
    : "text-slate-400 hover:bg-slate-800 hover:text-white";

  return (
    <div className="flex h-screen bg-slate-100 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col shadow-xl">
        <div className="p-6 border-b border-slate-700">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <ShieldAlert className="text-blue-500" /> Insomnia Coders
          </h2>
          <span className="text-xs text-slate-500 uppercase tracking-widest mt-1 block">
            {role === 'admin' ? 'Admin Panel' : 'Employee Panel'}
          </span>
        </div>

        <nav className="flex-1 p-4 space-y-2 mt-4">
          <Link to="/dashboard/query" className={`flex items-center gap-3 p-3 rounded-lg transition-all ${isActive('/dashboard/query')}`}>
            <MessageSquare size={20} />
            <span className="font-medium">Query Engine</span>
          </Link>

          {role === 'admin' && (
            <>
              <Link to="/dashboard/upload" className={`flex items-center gap-3 p-3 rounded-lg transition-all ${isActive('/dashboard/upload')}`}>
                <UploadCloud size={20} />
                <span className="font-medium">Ingestion Engine</span>
              </Link>

              <Link to="/dashboard/stakeholders" className={`flex items-center gap-3 p-3 rounded-lg transition-all ${isActive('/dashboard/stakeholders')}`}>
                <Users size={20} />
                <span className="font-medium">Stakeholders</span>
              </Link>

              <Link to="/dashboard/visualization" className={`flex items-center gap-3 p-3 rounded-lg transition-all ${isActive('/dashboard/visualization')}`}>
                <BarChart3 size={20} />
                <span className="font-medium">Visualization</span>
              </Link>
            </>
          )}

          <Link to="/dashboard/routing" className={`flex items-center gap-3 p-3 rounded-lg transition-all ${isActive('/dashboard/routing')}`}>
            <Route size={20} />
            <span className="font-medium">Document Routing</span>
          </Link>
        </nav>

        <div className="p-4 border-t border-slate-700">
          <button onClick={handleLogout} className="flex items-center gap-3 text-slate-400 hover:text-red-400 transition w-full p-2">
            <LogOut size={20} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-slate-50 p-8">
        <Outlet />
      </main>
    </div>
  );
}