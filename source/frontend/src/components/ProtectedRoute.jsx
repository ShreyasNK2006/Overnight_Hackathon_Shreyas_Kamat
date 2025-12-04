import { Navigate } from 'react-router-dom';

export default function ProtectedRoute({ children, requiredRole }) {
  const userRole = localStorage.getItem('userRole');

  if (!userRole) {
    return <Navigate to="/" replace />;
  }

  // If admin is required but user is just an employee
  if (requiredRole === 'admin' && userRole !== 'admin') {
    return <Navigate to="/dashboard/query" replace />;
  }

  return children;
}