import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Layout from './components/Layout';
import QueryEngine from './pages/QueryEngine';
import IngestionEngine from './pages/IngestionEngine';
import StakeholderManagement from './pages/StakeholderManagement';
import DocumentRouting from './pages/DocumentRouting';
import AdminVisualization from './pages/AdminVisualization';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />

        <Route path="/dashboard" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard/query" replace />} />
          <Route path="query" element={<QueryEngine />} />

          <Route path="upload" element={
            <ProtectedRoute requiredRole="admin">
              <IngestionEngine />
            </ProtectedRoute>
          } />

          <Route path="stakeholders" element={
            <ProtectedRoute requiredRole="admin">
              <StakeholderManagement />
            </ProtectedRoute>
          } />

          <Route path="visualization" element={
            <ProtectedRoute requiredRole="admin">
              <AdminVisualization />
            </ProtectedRoute>
          } />

          <Route path="routing" element={<DocumentRouting />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;