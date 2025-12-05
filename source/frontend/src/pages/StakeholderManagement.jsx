import { useState } from 'react';
import { Users, UserPlus, Search, Mail, Phone, Briefcase, Building2, CheckCircle, XCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function StakeholderManagement() {
  const [stakeholders, setStakeholders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    role: '',
    department: '',
    phone: '',
    responsibilities: ''
  });

  const fetchStakeholders = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/stakeholders`);
      const data = await response.json();
      setStakeholders(data);
    } catch (error) {
      console.error('Failed to fetch stakeholders:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/stakeholders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!response.ok) throw new Error('Failed to create stakeholder');

      // Reset form and refresh list
      setFormData({
        name: '',
        email: '',
        role: '',
        department: '',
        phone: '',
        responsibilities: ''
      });
      setShowForm(false);
      fetchStakeholders();
    } catch (error) {
      alert('Failed to create stakeholder: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to deactivate this stakeholder?')) return;

    try {
      const response = await fetch(`${API_BASE}/stakeholders/${id}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Failed to delete stakeholder');
      fetchStakeholders();
    } catch (error) {
      alert('Failed to delete stakeholder: ' + error.message);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <Users size={28} />
          Stakeholder Management
        </h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700"
        >
          <UserPlus size={20} />
          Add Stakeholder
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6 border border-slate-200">
          <h2 className="text-xl font-semibold mb-4">New Stakeholder</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="John Doe"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Email *
                </label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="john@company.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Role *
                </label>
                <input
                  type="text"
                  required
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Safety Officer"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Department
                </label>
                <input
                  type="text"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Safety & Compliance"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Phone
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="+1-555-0100"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Responsibilities * (Be detailed for accurate routing)
              </label>
              <textarea
                required
                value={formData.responsibilities}
                onChange={(e) => setFormData({ ...formData, responsibilities: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 h-32"
                placeholder="I handle all safety-related matters including structural inspections, site accidents, hazard assessments..."
              />
              <p className="text-xs text-slate-500 mt-1">
                Min 20 characters. Include specific tasks, domains, and keywords that might appear in documents.
              </p>
            </div>

            <div className="flex gap-2">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Stakeholder'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="bg-slate-200 text-slate-700 px-6 py-2 rounded-lg hover:bg-slate-300"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Stakeholders</h2>
          <button
            onClick={fetchStakeholders}
            className="text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            <Search size={16} />
            Refresh
          </button>
        </div>

        {loading && stakeholders.length === 0 ? (
          <div className="text-center py-8 text-slate-500">Loading...</div>
        ) : stakeholders.length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            No stakeholders yet. Click "Add Stakeholder" to create one.
          </div>
        ) : (
          <div className="space-y-3">
            {stakeholders.map((stakeholder) => (
              <div
                key={stakeholder.id}
                className="border border-slate-200 rounded-lg p-4 hover:border-blue-300 transition"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold text-lg">{stakeholder.name}</h3>
                      {stakeholder.is_active ? (
                        <CheckCircle size={16} className="text-green-500" />
                      ) : (
                        <XCircle size={16} className="text-red-500" />
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-sm text-slate-600">
                      <div className="flex items-center gap-1">
                        <Briefcase size={14} />
                        {stakeholder.role}
                      </div>
                      {stakeholder.department && (
                        <div className="flex items-center gap-1">
                          <Building2 size={14} />
                          {stakeholder.department}
                        </div>
                      )}
                      <div className="flex items-center gap-1">
                        <Mail size={14} />
                        {stakeholder.email}
                      </div>
                      {stakeholder.phone && (
                        <div className="flex items-center gap-1">
                          <Phone size={14} />
                          {stakeholder.phone}
                        </div>
                      )}
                    </div>

                    <div className="mt-3 text-sm text-slate-700 bg-slate-50 p-3 rounded">
                      <span className="font-medium">Responsibilities:</span>
                      <p className="mt-1">{stakeholder.responsibilities}</p>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDelete(stakeholder.id)}
                    className="ml-4 text-red-600 hover:text-red-700"
                  >
                    <XCircle size={20} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
