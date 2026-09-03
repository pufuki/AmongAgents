interface DiscussionEntry {
  player_id: string;
  player_name: string;
  message: string;
}

interface DiscussionPanelProps {
  discussion: DiscussionEntry[];
}

export default function DiscussionPanel({ discussion }: DiscussionPanelProps) {
  return (
    <div className="panel" style={{ minHeight: '200px' }}>
      <div className="panel-header">
        <span className="panel-title">Discussion</span>
      </div>
      <div className="panel-body">
        {discussion.length === 0 ? (
          <div className="inspector-empty">No discussion yet.</div>
        ) : (
          discussion.map((entry, i) => (
            <div key={i} className="discussion-message">
              <div className="discussion-sender">{entry.player_name}</div>
              <div className="discussion-text">{entry.message}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
