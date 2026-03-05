import { useState } from 'react';
import { Bot } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import styles from './Login.module.css';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(username, password);
      window.location.href = '/tereziadmin/';
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setError(axiosError.response?.data?.detail || 'Erro ao fazer login');
      } else {
        setError('Erro ao fazer login');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.background}>
        <div className={styles.grid} />
      </div>
      
      <div className={styles.card}>
        <div className={styles.logo}>
          <Bot size={48} strokeWidth={1.5} />
          <h1>TerezIA</h1>
          <span className={styles.badge}>Admin Panel</span>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <Input
            label="Usuário"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Digite seu usuário"
            required
          />

          <Input
            label="Senha"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Digite sua senha"
            required
          />

          {error && <div className={styles.error}>{error}</div>}

          <Button type="submit" isLoading={isLoading} className={styles.submitBtn}>
            {isLoading ? 'Entrando...' : 'Entrar'}
          </Button>
        </form>

        <div className={styles.footer}>
          <span className={styles.version}>v1.0.0</span>
        </div>
      </div>
    </div>
  );
}
