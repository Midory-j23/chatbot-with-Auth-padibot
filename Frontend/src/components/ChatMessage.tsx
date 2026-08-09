import { useState } from "react";
import { cn } from "@/lib/utils";
import { Bot, User, Copy, Check, Reply } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "@/hooks/use-toast";
import { truncateQuote } from "@/lib/replyMessage";
import { getMessageTextAlign, isPersianText } from "@/lib/textDirection";

interface ChatMessageProps {
  message: string;
  thinking?: string;
  isUser: boolean;
  isNew?: boolean;
  image?: string;
  model?: string;
  replyTo?: {
    content: string;
    isUser: boolean;
  };
  onReply?: () => void;
  canReply?: boolean;
}

const ChatMessage = ({
  message,
  thinking,
  isUser,
  isNew = false,
  image,
  model,
  replyTo,
  onReply,
  canReply = false,
}: ChatMessageProps) => {
  const [copied, setCopied] = useState(false);
  const messageAlign = getMessageTextAlign(message);
  const thinkingAlign = getMessageTextAlign(thinking ?? "");
  const replyAlign = replyTo ? getMessageTextAlign(replyTo.content) : messageAlign;

  const handleCopy = async () => {
    const textToCopy = thinking
      ? `Thinking:\n${thinking}\n\nAnswer:\n${message}`
      : message;
    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      toast({
        title: "Copied!",
        description: "Message copied to clipboard",
        duration: 2000,
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
      toast({
        title: "Error",
        description: "Failed to copy message",
        variant: "destructive",
        duration: 2000,
      });
    }
  };

  return (
    <div
      className={cn(
        "flex gap-3 p-4 w-full group",
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
          "flex-1 max-w-[75%] min-w-0",
          isUser ? "flex justify-end" : "flex justify-start"
        )}
      >
        <div className="relative group/message">
          <div
            className={cn(
              "rounded-2xl px-4 py-3 transition-shadow break-words overflow-hidden",
              "w-full",
              isUser
                ? "bg-primary text-primary-foreground rounded-tr-sm shadow-md"
                : "glass rounded-tl-sm shadow-sm dark:shadow-none"
            )}
          >
            {replyTo && (
              <div
                dir={isPersianText(replyTo.content) ? "rtl" : "ltr"}
                className={cn(
                  "mb-2 rounded-lg border-l-2 px-2.5 py-1.5 text-xs",
                  replyAlign,
                  isUser
                    ? "border-primary-foreground/50 bg-primary-foreground/10 text-primary-foreground/90"
                    : "border-primary/50 bg-muted/50 text-muted-foreground"
                )}
              >
                <p className="font-semibold mb-0.5 opacity-80">
                  Replying to {replyTo.isUser ? "You" : "AI"}
                </p>
                <p className="line-clamp-2 whitespace-pre-wrap">
                  {truncateQuote(replyTo.content, 160)}
                </p>
              </div>
            )}

            {image && (
              <div className="mb-2">
                <img
                  src={image}
                  alt="Attached"
                  className="max-w-full rounded-lg max-h-64 object-contain"
                />
              </div>
            )}
            {thinking && (
              <div
                dir={isPersianText(thinking) ? "rtl" : "ltr"}
                className={cn(
                  "mb-3 rounded-lg border border-border/60 bg-muted/40 px-3 py-2",
                  thinkingAlign
                )}
              >
                <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground mb-1.5">
                  Thinking
                </p>
                <p className="text-xs leading-relaxed whitespace-pre-wrap break-words text-muted-foreground italic">
                  {thinking}
                </p>
              </div>
            )}
            {message && (
              <p
                dir={isPersianText(message) ? "rtl" : "ltr"}
                className={cn(
                  "text-sm leading-relaxed whitespace-pre-wrap break-words",
                  messageAlign
                )}
              >
                {message}
              </p>
            )}
            {!message && thinking && (
              <p className="text-xs text-muted-foreground animate-pulse">Generating answer...</p>
            )}
            {!isUser && model && (
              <p className="mt-2 text-[10px] text-muted-foreground/80 font-medium tracking-wide">
                {model}
              </p>
            )}
          </div>

          <div
            className={cn(
              "absolute -top-2 flex gap-1 opacity-0 group-hover/message:opacity-100 transition-all duration-200",
              isUser ? "-left-2" : "-right-2"
            )}
          >
            {canReply && message && onReply && (
              <Button
                variant="ghost"
                size="icon"
                title="Reply"
                className="h-8 w-8 rounded-full bg-background border border-border shadow-sm hover:bg-accent hover:scale-105"
                onClick={onReply}
              >
                <Reply className="h-3.5 w-3.5" />
              </Button>
            )}
            {!isUser && (message || thinking) && (
              <Button
                variant="ghost"
                size="icon"
                title="Copy"
                className="h-8 w-8 rounded-full bg-background border border-border shadow-sm hover:bg-accent hover:scale-105"
                onClick={handleCopy}
              >
                {copied ? (
                  <Check className="h-3.5 w-3.5 text-green-500" />
                ) : (
                  <Copy className="h-3.5 w-3.5" />
                )}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
