import { Moon, Sun, Users, Eye } from 'lucide-react';

interface HeaderProps {
  phase: string;
  roundNumber: number;
  aliveCount: number;
  totalPlayers: number;
  winner: string | null;
}

export default function Header({ phase, roundNumber, aliveCount, totalPlayers, winner }: HeaderProps) {
  const phaseLabel = (() => {
    if (winner) return 'Game Over';
    switch (phase) {
      case 'night': return 'Night';
      case 'day_discussion': return 'Day — Discussion';
      case 'day_voting': return 'Day — Voting';
      case 'day_result': return 'Day — Result';
      case 'game_over': return 'Game Over';
      default: return 'Waiting';
    }
  })();

  const isNight = phase === 'night' && !winner;
  const PhaseIcon = isNight ? Moon : Sun;

  return (
    <header className="header">
      <h1 className="header-title">
        AMONG <span className="accent">AGENTS</span>
      </h1>
      <p className="header-subtitle">Multi-Agent Social Deduction Simulation</p>
      <div className="header-status">
        <div className="status-badge">
          <PhaseIcon size={14} className={isNight ? 'phase-night' : 'phase-day'} />
          <span className="label">Phase</span>
          <span className="value">{phaseLabel}</span>
        </div>
        <div className="status-badge">
          <span className="label">Round</span>
          <span className="value">{roundNumber || '—'}</span>
        </div>
        <div className="status-badge">
          <Users size={14} />
          <span className="label">Alive</span>
          <span className="value">{aliveCount} / {totalPlayers}</span>
        </div>
      </div>
    </header>
  );
}
