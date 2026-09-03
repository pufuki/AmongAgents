interface PlayerPrivate {
  id: string;
  name: string;
  personality: string;
  role: string;
  alive: boolean;
  suspicions: Record<string, number>;
  memories: Array<{ round: number; type: string; description: string }>;
  investigation_results: Record<string, string>;
}

interface AgentInspectorProps {
  selectedPlayer: PlayerPrivate | null;
  debugMode: boolean;
  allPlayers: Array<{ id: string; name: string }>;
}

export default function AgentInspector({ selectedPlayer, debugMode, allPlayers }: AgentInspectorProps) {
  return (
    <div className="panel" style={{ minHeight: '300px' }}>
      <div className="panel-header">
        <span className="panel-title">Agent Inspector</span>
        {selectedPlayer && (
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
            {selectedPlayer.name}
          </span>
        )}
      </div>
      <div className="panel-body">
        {!selectedPlayer ? (
          <div className="inspector-empty">Select a player card to inspect.</div>
        ) : (
          <div className="inspector-player">
            <div className="inspector-section">
              <div className="inspector-label">Name</div>
              <div className="inspector-value">{selectedPlayer.name}</div>
            </div>

            <div className="inspector-section">
              <div className="inspector-label">Personality</div>
              <div className="inspector-value" style={{ textTransform: 'capitalize' }}>
                {selectedPlayer.personality}
              </div>
            </div>

            <div className="inspector-section">
              <div className="inspector-label">Status</div>
              <div className="inspector-value">
                {selectedPlayer.alive ? 'Alive' : 'Eliminated'}
              </div>
            </div>

            {debugMode && (
              <>
                <div className="inspector-section">
                  <div className="inspector-label">Role</div>
                  <div className="inspector-value" style={{ color: 'var(--color-gold)', textTransform: 'capitalize' }}>
                    {selectedPlayer.role}
                  </div>
                </div>

                {selectedPlayer.investigation_results &&
                  Object.keys(selectedPlayer.investigation_results).length > 0 && (
                  <div className="inspector-section">
                    <div className="inspector-label">Investigation Results</div>
                    {Object.entries(selectedPlayer.investigation_results).map(([pid, result]) => {
                      const player = allPlayers.find(p => p.id === pid);
                      return (
                        <div key={pid} className="inspector-value" style={{ fontSize: '0.8rem' }}>
                          {player?.name || pid}: <span style={{ color: result === 'mafia' ? 'var(--color-accent-hover)' : '#6fa873' }}>{result}</span>
                        </div>
                      );
                    })}
                  </div>
                )}

                <div className="inspector-section">
                  <div className="inspector-label">Suspicion Scores</div>
                  {Object.entries(selectedPlayer.suspicions || {})
                    .sort(([, a], [, b]) => b - a)
                    .map(([pid, score]) => {
                      const player = allPlayers.find(p => p.id === pid);
                      return (
                        <div key={pid} className="suspicion-bar">
                          <span className="name">{player?.name || pid}</span>
                          <div className="bar-track">
                            <div className="bar-fill" style={{ width: `${score * 100}%` }} />
                          </div>
                          <span className="score">{score.toFixed(2)}</span>
                        </div>
                      );
                    })}
                </div>

                {selectedPlayer.memories && selectedPlayer.memories.length > 0 && (
                  <div className="inspector-section">
                    <div className="inspector-label">Memory Log</div>
                    {selectedPlayer.memories.slice(-8).map((mem, i) => (
                      <div key={i} className="memory-item">
                        <span className="round-tag">[R{mem.round}]</span> {mem.description}
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {!debugMode && (
              <div className="inspector-section">
                <div className="inspector-label" style={{ color: 'var(--color-text-dim)' }}>
                  Enable debug mode after game ends to see roles, suspicions, and memories.
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
