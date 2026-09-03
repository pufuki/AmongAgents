interface Player {
  id: string;
  name: string;
  personality: string;
  alive: boolean;
  role?: string;
}

interface AgentCardProps {
  player: Player;
  isSpeaking?: boolean;
  showRole?: boolean;
  onClick?: () => void;
  isSelected?: boolean;
}

const personalityIcons: Record<string, string> = {
  analytical: 'A',
  aggressive: 'Ag',
  diplomatic: 'D',
  quiet: 'Q',
  chaotic: 'C',
};

export default function AgentCard({ player, isSpeaking, showRole, onClick, isSelected }: AgentCardProps) {
  const initials = player.name.charAt(0);

  return (
    <div
      className={`agent-card ${player.alive ? '' : 'dead'} ${isSpeaking ? 'speaking' : ''}`}
      onClick={onClick}
      style={isSelected ? { borderColor: 'var(--color-gold)', boxShadow: 'var(--shadow-glow)' } : undefined}
    >
      <div className="agent-avatar">{initials}</div>
      <div className="agent-name">{player.name}</div>
      <div className="agent-personality">{player.personality}</div>
      <div className={`agent-status ${player.alive ? 'alive' : 'dead'}`}>
        {player.alive ? 'Alive' : 'Eliminated'}
      </div>
      {showRole && player.role && (
        <div className="agent-role-reveal">{player.role}</div>
      )}
    </div>
  );
}
