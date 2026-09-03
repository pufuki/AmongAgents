import AgentCard from './AgentCard';
import EventTimeline from './EventTimeline';
import DiscussionPanel from './DiscussionPanel';
import AgentInspector from './AgentInspector';

interface Player {
  id: string;
  name: string;
  personality: string;
  alive: boolean;
  role?: string;
  suspicions?: Record<string, number>;
  memories?: Array<{ round: number; type: string; description: string }>;
  investigation_results?: Record<string, string>;
}

interface GameEvent {
  id: number;
  round_number: number;
  phase: string;
  event_type: string;
  message: string;
  public: boolean;
  metadata: Record<string, unknown>;
}

interface GameBoardProps {
  players: Player[];
  events: GameEvent[];
  discussion: Array<{ player_id: string; player_name: string; message: string }>;
  selectedPlayer: Player | null;
  debugMode: boolean;
  onCardClick: (id: string) => void;
  selectedPlayerId: string | null;
  canShowDebug: boolean;
}

export default function GameBoard({
  players, events, discussion, selectedPlayer, debugMode,
  onCardClick, selectedPlayerId, canShowDebug
}: GameBoardProps) {
  return (
    <>
      <div className="players-area">
        {players.map(player => (
          <AgentCard
            key={player.id}
            player={player}
            showRole={canShowDebug && debugMode}
            onClick={() => onCardClick(player.id)}
            isSelected={selectedPlayerId === player.id}
          />
        ))}
      </div>

      <div className="game-board">
        <EventTimeline events={events} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <DiscussionPanel discussion={discussion} />
          <AgentInspector
            selectedPlayer={selectedPlayer as any}
            debugMode={debugMode}
            allPlayers={players}
          />
        </div>
      </div>
    </>
  );
}
