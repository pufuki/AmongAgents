interface GameEvent {
  id: number;
  round_number: number;
  phase: string;
  event_type: string;
  message: string;
  public: boolean;
  metadata: Record<string, unknown>;
}

interface EventTimelineProps {
  events: GameEvent[];
}

export default function EventTimeline({ events }: EventTimelineProps) {
  return (
    <div className="panel" style={{ minHeight: '300px' }}>
      <div className="panel-header">
        <span className="panel-title">Event Timeline</span>
      </div>
      <div className="panel-body">
        {events.length === 0 ? (
          <div className="inspector-empty">No events yet. Start a new game.</div>
        ) : (
          <div className="event-timeline">
            {events.map((event) => (
              <div key={event.id} className={`event-item phase-${event.phase}`}>
                <div className="event-marker" />
                <div className="event-content">
                  <div className="event-message">{event.message}</div>
                  <div className="event-meta">
                    Round {event.round_number} · {event.phase.replace(/_/g, ' ')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
