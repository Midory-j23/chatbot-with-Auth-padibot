import { Bot, MoreVertical, Trash2, PanelLeft, StopCircle, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import ThemeToggle from "./ThemeToggle";
import { useAuth } from "@/hooks/AuthContext";

interface ChatHeaderProps {
  onClearChat: () => void;
  messageCount: number;
  onToggleSidebar: () => void;
  isStreaming?: boolean;
  onStopStreaming?: () => void;
}

const ChatHeader = ({ onClearChat, messageCount, onToggleSidebar, isStreaming, onStopStreaming }: ChatHeaderProps) => {
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <header className="flex items-center justify-between px-4 py-3 border-b border-border/50 glass">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleSidebar}
          className="text-muted-foreground hover:text-foreground hover:bg-accent"
        >
          <PanelLeft className="h-5 w-5" />
        </Button>
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/30 to-accent/20 flex items-center justify-center glow-sm">
          <Bot className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="font-semibold text-foreground">Padi Bot</h2>
          <p className="text-xs text-muted-foreground">
            {messageCount > 0 ? `${messageCount} messages` : "Online"}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {isStreaming && onStopStreaming && (
          <Button
            variant="outline"
            size="sm"
            onClick={onStopStreaming}
            className="gap-2 text-destructive border-destructive/50 hover:bg-destructive/10"
          >
            <StopCircle className="h-4 w-4" />
            <span className="hidden sm:inline">Stop</span>
          </Button>
        )}
        
        {!isStreaming && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-xs font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            Active
          </div>
        )}

        <ThemeToggle />
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="w-9 h-9 rounded-lg hover:bg-secondary flex items-center justify-center transition-colors">
              <MoreVertical className="w-4 h-4 text-muted-foreground" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="glass">
            <DropdownMenuItem onClick={onClearChat} className="text-destructive focus:text-destructive">
              <Trash2 className="w-4 h-4 mr-2" />
              Clear conversation
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout}>
              <LogOut className="w-4 h-4 mr-2" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};

export default ChatHeader;
