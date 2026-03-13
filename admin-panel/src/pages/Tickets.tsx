import { useState } from 'react';
import { ShieldAlert, Image as ImageIcon, MapPin } from 'lucide-react';
import styles from './Tickets.module.css';

interface Ticket {
    id: string;
    protocol: string;
    category: string;
    description: string;
    address: string;
    citizen: string;
    createdAt: string;
    status: 'Aberto' | 'Em Andamento' | 'Concluído';
    hasImage: boolean;
}

const MOCK_TICKETS: Ticket[] = [
    {
        id: '1',
        protocol: '2026-8A3F9',
        category: 'Buraco na Via',
        description: 'Cratera na faixa da direita, risco de acidentes.',
        address: 'Av. Paulista, 1578',
        citizen: 'João Silva (11) 99999-9999',
        createdAt: '2026-03-05T14:30:00Z',
        status: 'Aberto',
        hasImage: true,
    },
    {
        id: '2',
        protocol: '2026-X7M2P',
        category: 'Iluminação Pública',
        description: 'Poste apagado há mais de 3 dias na rua inteira.',
        address: 'Rua Augusta, 450',
        citizen: 'Maria Souza (11) 98888-8888',
        createdAt: '2026-03-05T09:15:00Z',
        status: 'Em Andamento',
        hasImage: false,
    },
    {
        id: '3',
        protocol: '2026-B4L9K',
        category: 'Entulho',
        description: 'Descarte irregular de móveis na calçada.',
        address: 'Praça da Sé, s/n',
        citizen: 'Carlos Roberto (11) 97777-7777',
        createdAt: '2026-03-04T16:45:00Z',
        status: 'Concluído',
        hasImage: true,
    }
];

export default function Tickets() {
    const [tickets] = useState<Ticket[]>(MOCK_TICKETS);

    const getStatusClass = (status: Ticket['status']) => {
        switch (status) {
            case 'Aberto': return styles.statusAberto;
            case 'Em Andamento': return styles.statusAndamento;
            case 'Concluído': return styles.statusConcluido;
            default: return '';
        }
    };

    const formatDate = (dateString: string) => {
        const d = new Date(dateString);
        return `${d.toLocaleDateString('pt-BR')} ${d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;
    };

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <h1 className={styles.title}>Gestão de Ouvidoria / Chamados</h1>
                <p className={styles.subtitle}>Gerenciamento de manifestações recebidas pelo atendimento via Chatbot.</p>
            </header>

            <div className={styles.grid}>
                <div className={styles.card}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                        <h2 className={styles.cardTitle} style={{ marginBottom: 0 }}>
                            Tickets Recentes <ShieldAlert size={20} style={{ marginLeft: 8, verticalAlign: 'middle', color: 'var(--accent-primary)' }} />
                        </h2>
                        <button className={styles.actionButton}>Exportar Dados</button>
                    </div>

                    <div className={styles.tableContainer}>
                        <table className={styles.table}>
                            <thead>
                                <tr>
                                    <th>Protocolo</th>
                                    <th>Data/Hora</th>
                                    <th>Categoria</th>
                                    <th>Endereço</th>
                                    <th>Cidadão</th>
                                    <th>Anexos</th>
                                    <th>Status</th>
                                    <th>Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                {tickets.map((ticket) => (
                                    <tr key={ticket.id}>
                                        <td><span className={styles.protocol}>{ticket.protocol}</span></td>
                                        <td>{formatDate(ticket.createdAt)}</td>
                                        <td style={{ fontWeight: 500 }}>{ticket.category}</td>
                                        <td>
                                            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                <MapPin size={14} style={{ color: 'var(--text-muted)' }} />
                                                {ticket.address}
                                            </span>
                                        </td>
                                        <td>{ticket.citizen}</td>
                                        <td>
                                            {ticket.hasImage ? (
                                                <span title="Contém imagem"><ImageIcon size={18} style={{ color: 'var(--info)' }} /></span>
                                            ) : (
                                                <span style={{ color: 'var(--text-muted)' }}>-</span>
                                            )}
                                        </td>
                                        <td>
                                            <span className={`${styles.statusBadge} ${getStatusClass(ticket.status)}`}>
                                                {ticket.status}
                                            </span>
                                        </td>
                                        <td>
                                            <button className={styles.actionButton}>Visualizar</button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
