import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";

interface ChatMessageProps {
  message: string;
  isUser: boolean;
  isNew?: boolean;
  image?: string;
}

const ChatMessage = ({ message, isUser, isNew = false, image }: ChatMessageProps) => {
  return (
    <div
      className={cn(
        "flex gap-3 p-4",
        isNew && "message-fade-in",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      <div
        className={cn(
          "flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center",
          isUser
            ? "bg-primary/20 text-primary"
            : "bg-gradient-to-br from-primary/30 to-accent/20 text-primary glow-sm"
        )}
      >
        {isUser ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
      </div>
      <div
        className={cn(
          "max-w-[75%] rounded-2xl px-4 py-3 transition-shadow",
          isUser
            ? "bg-primary text-primary-foreground rounded-tr-sm shadow-md"
            : "glass rounded-tl-sm shadow-sm dark:shadow-none"
        )}
      >
        {image && (
          <div className="mb-2">
            <img
              src={image}
              alt="Attached"
              className="max-w-full rounded-lg max-h-64 object-contain"
            />
          </div>
        )}
        {message && (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message}</p>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
