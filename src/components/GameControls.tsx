import { Play, Pause, SkipForward, RotateCcw, Plus } from 'lucide-react';

interface GameControlsProps {
  onNewGame: () => void;
  onNext: () => void;
  onAutoPlay: () => void;
  onReset: () => void;
  isAutoPlaying: boolean;
  disabled: boolean;
  gameActive: boolean;
  gameOver: boolean;
}

export default function GameControls({
  onNewGame, onNext, onAutoPlay, onReset,
  isAutoPlaying, disabled, gameActive, gameOver
}: GameControlsProps) {
  return (
    <div className="game-controls">
      <button className="btn btn-primary" onClick={onNewGame} disabled={disabled}>
        <Plus size={16} />
        Start New Game
      </button>
      <button className="btn" onClick={onNext} disabled={disabled || !gameActive || gameOver}>
        <SkipForward size={16} />
        Next Event
      </button>
      <button
        className="btn"
        onClick={onAutoPlay}
        disabled={disabled || !gameActive || gameOver}
      >
        {isAutoPlaying ? <Pause size={16} /> : <Play size={16} />}
        {isAutoPlaying ? 'Pause' : 'Auto Play'}
      </button>
      <button className="btn" onClick={onReset} disabled={disabled || !gameActive}>
        <RotateCcw size={16} />
        Reset
      </button>
    </div>
  );
}
