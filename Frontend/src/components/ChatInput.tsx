import { useState, useRef } from "react";
import type { KeyboardEvent } from "react";
import { Send, Sparkles, ImagePlus, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string, image?: string) => void;
  disabled?: boolean;
}

const ChatInput = ({ onSend, disabled = false }: ChatInputProps) => {
  const [message, setMessage] = useState("");
  const [image, setImage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if ((message.trim() || image) && !disabled) {
      onSend(message.trim(), image || undefined);
      setMessage("");
      setImage(null);
    }
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setImage(event.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-4 border-t border-border/50">
      <div className="max-w-4xl mx-auto">
        {/* Image Preview */}
        {image && (
          <div className="mb-3 relative inline-block">
            <div className="relative rounded-xl overflow-hidden border border-border/50 glass">
              <img
                src={image}
                alt="Attached"
                className="max-h-32 max-w-full object-contain"
              />
              <button
                onClick={removeImage}
                className="absolute top-1 right-1 w-6 h-6 rounded-full bg-background/80 backdrop-blur-sm flex items-center justify-center hover:bg-destructive hover:text-destructive-foreground transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        <div className="glass-input rounded-2xl input-glow transition-all duration-300">
          <div className="flex items-end gap-2 p-2">
            {/* Image Upload Button */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageSelect}
              accept="image/*"
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled}
              className={cn(
                "flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-colors",
                disabled
                  ? "text-muted-foreground cursor-not-allowed"
                  : "text-muted-foreground hover:text-primary hover:bg-primary/10"
              )}
            >
              <ImagePlus className="w-5 h-5" />
            </button>

            <div className="flex-1 relative">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                disabled={disabled}
                rows={1}
                className={cn(
                  "w-full bg-transparent resize-none outline-none text-foreground placeholder:text-muted-foreground px-3 py-2.5 text-sm max-h-32",
                  "scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent"
                )}
                style={{
                  minHeight: "44px",
                  height: "auto",
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = "44px";
                  target.style.height = Math.min(target.scrollHeight, 128) + "px";
                }}
              />
            </div>
            <button
              onClick={handleSend}
              disabled={(!message.trim() && !image) || disabled}
              className={cn(
                "flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center send-btn-hover",
                (message.trim() || image) && !disabled
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground cursor-not-allowed"
              )}
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
        <p className="text-center text-xs text-muted-foreground mt-3 flex items-center justify-center gap-1.5">
          <Sparkles className="w-3 h-3" />
          Powered by Ghasemian • Press Enter to send
        </p>
      </div>
    </div>
  );
};

export default ChatInput;
