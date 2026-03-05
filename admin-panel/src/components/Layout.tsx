import { useState, type ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileText, 
  Search, 
  Settings2, 
  Terminal, 
  LogOut,
  Menu,
  X,
  Bot,
  Sliders,
  Globe,
  Zap
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import styles from './Layout.module.css';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/rag', icon: FileText, label: 'RAG Manager' },
  { path: '/rag-test', icon: Search, label: 'RAG Tester' },
  { path: '/rag-config', icon: Sliders, label: 'Config RAG' },
  { path: '/boosts', icon: Zap, label: 'Boosts' },
  { path: '/scrap', icon: Globe, label: 'Scraping' },
  { path: '/logs', icon: Terminal, label: 'Logs' },
  { path: '/ops', icon: Settings2, label: 'Operações' },
];

export default function Layout({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className={styles.layout}>
      {/* Mobile toggle */}
      <button 
        className={styles.mobileToggle}
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Sidebar */}
      <aside className={`${styles.sidebar} ${sidebarOpen ? styles.open : ''}`}>
        <div className={styles.sidebarHeader}>
          <Bot size={28} strokeWidth={1.5} />
          <span className={styles.brand}>TerezIA</span>
          <span className={styles.adminBadge}>Admin</span>
        </div>

        <nav className={styles.nav}>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) => 
                `${styles.navItem} ${isActive ? styles.active : ''}`
              }
              onClick={() => setSidebarOpen(false)}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className={styles.sidebarFooter}>
          <div className={styles.userInfo}>
            <div className={styles.avatar}>
              {user?.username?.charAt(0).toUpperCase()}
            </div>
            <div className={styles.userDetails}>
              <span className={styles.username}>{user?.username}</span>
              <span className={styles.role}>{user?.role}</span>
            </div>
          </div>
          <button onClick={handleLogout} className={styles.logoutBtn}>
            <LogOut size={18} />
          </button>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div 
          className={styles.overlay} 
          onClick={() => setSidebarOpen(false)} 
        />
      )}

      {/* Main content */}
      <main className={styles.main}>
        {children}
      </main>
    </div>
  );
}
