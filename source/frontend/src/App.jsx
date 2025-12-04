import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Layout from './components/Layout';
import QueryEngine from './pages/QueryEngine';
import IngestionEngine from './pages/IngestionEngine';
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
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;