import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import RAGManager from './pages/RAGManager';
import RAGTester from './pages/RAGTester';
import RAGConfig from './pages/RAGConfig';
import Logs from './pages/Logs';
import Ops from './pages/Ops';
import Scrap from './pages/Scrap';
import Boosts from './pages/Boosts';
import Alerts from './pages/Alerts';
import Tickets from './pages/Tickets';
import './styles/globals.css';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        color: '#737373'
      }}>
        Carregando...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter basename="/tereziadmin">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/rag" element={<ProtectedRoute><RAGManager /></ProtectedRoute>} />
          <Route path="/rag-test" element={<ProtectedRoute><RAGTester /></ProtectedRoute>} />
          <Route path="/rag-config" element={<ProtectedRoute><RAGConfig /></ProtectedRoute>} />
          <Route path="/logs" element={<ProtectedRoute><Logs /></ProtectedRoute>} />
          <Route path="/ops" element={<ProtectedRoute><Ops /></ProtectedRoute>} />
          <Route path="/scrap" element={<ProtectedRoute><Scrap /></ProtectedRoute>} />
          <Route path="/boosts" element={<ProtectedRoute><Boosts /></ProtectedRoute>} />
          <Route path="/alerts" element={<ProtectedRoute><Alerts /></ProtectedRoute>} />
          <Route path="/tickets" element={<ProtectedRoute><Tickets /></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
