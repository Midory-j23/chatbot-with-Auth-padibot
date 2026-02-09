const TypingIndicator = () => {
  return (
    <div className="flex gap-3 p-4 message-fade-in">
      <div className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center bg-gradient-to-br from-primary/30 to-accent/20 text-primary glow-sm">
        <div className="w-5 h-5 flex items-center justify-center">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="4" cy="12" r="2" />
            <circle cx="12" cy="12" r="2" />
            <circle cx="20" cy="12" r="2" />
          </svg>
        </div>
      </div>
      <div className="glass rounded-2xl rounded-tl-sm px-5 py-4">
        <div className="flex gap-1.5">
          <span className="typing-dot w-2 h-2 rounded-full bg-primary" />
          <span className="typing-dot w-2 h-2 rounded-full bg-primary" />
          <span className="typing-dot w-2 h-2 rounded-full bg-primary" />
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
