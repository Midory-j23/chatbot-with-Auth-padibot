import { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { Bot, User, Copy, Check, Reply, ChevronDown, Brain } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "@/hooks/use-toast";
import { truncateQuote } from "@/lib/replyMessage";
import { getMessageTextAlign, isPersianText } from "@/lib/textDirection";

function formatModelLabel(id: string): string {
  const base = id.replace(/:latest$/, "");
  if (base === "gemma3") return "Gemma 3";
  if (base === "qwen3:4b") return "Qwen 3 4B";
  if (base.startsWith("qwen3")) return "Qwen 3";
  if (base.startsWith("qwen")) return "Qwen";
  if (base.startsWith("gemma3")) return "Gemma 3";
  return base;
}

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
  const [thinkingOpen, setThinkingOpen] = useState(true);
  const userToggledThinkingRef = useRef(false);
  const hadAnswerRef = useRef(false);
  const messageAlign = getMessageTextAlign(message);
  const thinkingAlign = getMessageTextAlign(thinking ?? "");
  const replyAlign = replyTo ? getMessageTextAlign(replyTo.content) : messageAlign;
  const stillThinking = Boolean(thinking && !message);

  useEffect(() => {
    if (!thinking) {
      userToggledThinkingRef.current = false;
      hadAnswerRef.current = false;
      return;
    }
    if (message && !hadAnswerRef.current) {
      hadAnswerRef.current = true;
      if (!userToggledThinkingRef.current) {
        setThinkingOpen(false);
      }
    }
  }, [thinking, message]);

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
                  "mb-3 rounded-xl border border-amber-500/30 bg-amber-500/5 overflow-hidden",
                  thinkingAlign
                )}
              >
                <button
                  type="button"
                  onClick={() => {
                    userToggledThinkingRef.current = true;
                    setThinkingOpen((v) => !v);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-amber-500/10 transition-colors"
                >
                  <Brain
                    className={cn(
                      "w-3.5 h-3.5 text-amber-600 dark:text-amber-400 flex-shrink-0",
                      stillThinking && "animate-pulse"
                    )}
                  />
                  <span className="text-[11px] font-semibold tracking-wide text-amber-700 dark:text-amber-300 flex-1">
                    {stillThinking ? "در حال فکر کردن..." : "فرآیند فکر کردن"}
                  </span>
                  <ChevronDown
                    className={cn(
                      "w-3.5 h-3.5 text-amber-600/80 transition-transform",
                      thinkingOpen && "rotate-180"
                    )}
                  />
                </button>
                {thinkingOpen && (
                  <p className="px-3 pb-2.5 text-xs leading-relaxed whitespace-pre-wrap break-words text-muted-foreground italic max-h-48 overflow-y-auto">
                    {thinking}
                  </p>
                )}
              </div>
            )}
            {!message && !thinking && !isUser && (
              <div className="flex gap-1.5 py-1">
                <span className="typing-dot w-2 h-2 rounded-full bg-primary" />
                <span className="typing-dot w-2 h-2 rounded-full bg-primary" />
                <span className="typing-dot w-2 h-2 rounded-full bg-primary" />
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
              <p className="text-xs text-muted-foreground animate-pulse font-vazir">
                در حال آماده‌سازی پاسخ...
              </p>
            )}
            {!isUser && model && (
              <p className="mt-2 text-[10px] text-muted-foreground/80 font-medium tracking-wide">
                {formatModelLabel(model)}
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
