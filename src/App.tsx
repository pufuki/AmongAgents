import { useState, useEffect, useRef, useCallback } from 'react';
import Header from './components/Header';
import GameBoard from './components/GameBoard';
import GameControls from './components/GameControls';
import { AlertCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

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

interface GameState {
  id: string;
  phase: string;
  round_number: number;
  players: Player[];
  events: GameEvent[];
  winner: string | null;
  alive_count: number;
}

function App() {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiConfigured, setAiConfigured] = useState(true);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);
  const [debugMode, setDebugMode] = useState(false);
  const [selectedPlayerId, setSelectedPlayerId] = useState<string | null>(null);
  const [debugPlayers, setDebugPlayers] = useState<Player[]>([]);
  const autoPlayRef = useRef<boolean>(false);

  // Check API health on mount
  useEffect(() => {
    fetch(`${API_BASE}/`)
      .then(res => res.json())
      .then(data => {
        setAiConfigured(data.ai_configured);
        if (!data.ai_configured) {
          setError(data.message);
        }
      })
      .catch(() => {
        setError('Cannot connect to backend. Make sure the server is running on port 8000.');
        setAiConfigured(false);
      });
  }, []);

  const handleNewGame = useCallback(async () => {
    setLoading(true);
    setError(null);
    setDebugMode(false);
    setDebugPlayers([]);
    setSelectedPlayerId(null);
    try {
      const res = await fetch(`${API_BASE}/games`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to create game');
      const data = await res.json();
      setGameState(data.state);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create game');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleNext = useCallback(async () => {
    if (!gameState) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/games/${gameState.id}/next`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to advance game');
      const data = await res.json();

      // Fetch full state
      const stateRes = await fetch(`${API_BASE}/games/${gameState.id}`);
      const stateData = await stateRes.json();
      setGameState(stateData);

      if (data.game_over) {
        autoPlayRef.current = false;
        setIsAutoPlaying(false);
        // Fetch debug data
        const debugRes = await fetch(`${API_BASE}/games/${gameState.id}?debug=true`);
        const debugData = await debugRes.json();
        setDebugPlayers(debugData.players || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to advance game');
      autoPlayRef.current = false;
      setIsAutoPlaying(false);
    } finally {
      setLoading(false);
    }
  }, [gameState]);

  const handleReset = useCallback(async () => {
    if (!gameState) return;
    setLoading(true);
    setError(null);
    setDebugMode(false);
    setDebugPlayers([]);
    try {
      const res = await fetch(`${API_BASE}/games/${gameState.id}/reset`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to reset game');
      const data = await res.json();
      setGameState(data.state);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset game');
    } finally {
      setLoading(false);
    }
  }, [gameState]);

  // Auto-play loop
  useEffect(() => {
    autoPlayRef.current = isAutoPlaying;
  }, [isAutoPlaying]);

  useEffect(() => {
    if (!isAutoPlaying || !gameState || gameState.winner) return;

    const timer = setTimeout(() => {
      handleNext();
    }, 1500);

    return () => clearTimeout(timer);
  }, [isAutoPlaying, gameState, handleNext]);

  // Stop autoplay when game is over
  useEffect(() => {
    if (gameState?.winner) {
      setIsAutoPlaying(false);
    }
  }, [gameState?.winner]);

  const handleAutoPlay = () => {
    if (isAutoPlaying) {
      setIsAutoPlaying(false);
    } else {
      setIsAutoPlaying(true);
    }
  };

  const handleCardClick = (playerId: string) => {
    setSelectedPlayerId(selectedPlayerId === playerId ? null : playerId);
  };

  // Get selected player data
  const selectedPlayer = (() => {
    if (!selectedPlayerId) return null;
    if (debugMode && debugPlayers.length > 0) {
      return debugPlayers.find(p => p.id === selectedPlayerId) || null;
    }
    return gameState?.players.find(p => p.id === selectedPlayerId) || null;
  })();

  // Extract discussion messages from events
  const discussionEntries = gameState?.events
    .filter(e => e.event_type === 'discussion')
    .map(e => {
      const match = e.message.match(/^(\w+) spoke: "(.*)"$/);
      if (match) {
        const playerName = match[1];
        const message = match[2];
        const player = gameState.players.find(p => p.name === playerName);
        return {
          player_id: player?.id || '',
          player_name: playerName,
          message,
        };
      }
      return null;
    })
    .filter((e): e is NonNullable<typeof e> => e !== null) || [];

  const isGameOver = gameState?.winner !== null && gameState?.winner !== undefined;
  const canShowDebug = isGameOver;

  return (
    <div className="app">
      <div className="app-content">
        <Header
          phase={gameState?.phase || 'waiting'}
          roundNumber={gameState?.round_number || 0}
          aliveCount={gameState?.alive_count || 0}
          totalPlayers={gameState?.players.length || 5}
          winner={gameState?.winner || null}
        />

        {error && (
          <div className="error-banner">
            <AlertCircle size={18} className="icon" />
            <span>{error}</span>
          </div>
        )}

        {isGameOver && gameState?.winner && (
          <div className="game-over-banner">
            <div className="winner">{gameState.winner === 'mafia' ? 'Mafia Wins' : 'Citizens Win'}</div>
            <div className="subtitle">The game has ended. Enable debug mode to inspect all agents.</div>
          </div>
        )}

        {/* Game Board */}
        {gameState && (
          <GameBoard
            players={gameState.players}
            events={gameState.events}
            discussion={discussionEntries}
            selectedPlayer={selectedPlayer as any}
            debugMode={debugMode}
            onCardClick={handleCardClick}
            selectedPlayerId={selectedPlayerId}
            canShowDebug={canShowDebug}
          />
        )}

        {/* Debug Toggle */}
        {canShowDebug && (
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '16px' }}>
            <label className="debug-toggle">
              <input
                type="checkbox"
                checked={debugMode}
                onChange={(e) => setDebugMode(e.target.checked)}
              />
              Debug Mode — Reveal roles, suspicions & memories
            </label>
          </div>
        )}

        {/* Controls */}
        <GameControls
          onNewGame={handleNewGame}
          onNext={handleNext}
          onAutoPlay={handleAutoPlay}
          onReset={handleReset}
          isAutoPlaying={isAutoPlaying}
          disabled={loading}
          gameActive={!!gameState}
          gameOver={isGameOver}
        />

        {loading && (
          <div style={{ textAlign: 'center', marginTop: '12px' }} className="loading-spinner">
            <div className="loading-dot" />
            <div className="loading-dot" />
            <div className="loading-dot" />
            <span>Processing...</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
