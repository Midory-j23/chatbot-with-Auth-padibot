// import { useState, useRef } from "react";
// import type { KeyboardEvent } from "react";
// import { Send, Sparkles, ImagePlus, X } from "lucide-react";
// import { cn } from "@/lib/utils";

// interface ChatInputProps {
//   onSend: (message: string, image?: string) => void;
//   disabled?: boolean;
// }

// const ChatInput = ({ onSend, disabled = false }: ChatInputProps) => {
//   const [message, setMessage] = useState("");
//   const [image, setImage] = useState<string | null>(null);
//   const fileInputRef = useRef<HTMLInputElement>(null);

//   const handleSend = () => {
//     if ((message.trim() || image) && !disabled) {
//       onSend(message.trim(), image || undefined);
//       setMessage("");
//       setImage(null);
//     }
//   };

//   const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
//     const file = e.target.files?.[0];
//     if (file) {
//       const reader = new FileReader();
//       reader.onload = (event) => {
//         setImage(event.target?.result as string);
//       };
//       reader.readAsDataURL(file);
//     }
//   };

//   const removeImage = () => {
//     setImage(null);
//     if (fileInputRef.current) {
//       fileInputRef.current.value = "";
//     }
//   };

//   const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
//     if (e.key === "Enter" && !e.shiftKey) {
//       e.preventDefault();
//       handleSend();
//     }
//   };

//   return (
//     <div className="p-4 border-t border-border/50">
//       <div className="max-w-4xl mx-auto">
//         {/* Image Preview */}
//         {image && (
//           <div className="mb-3 relative inline-block">
//             <div className="relative rounded-xl overflow-hidden border border-border/50 glass">
//               <img
//                 src={image}
//                 alt="Attached"
//                 className="max-h-32 max-w-full object-contain"
//               />
//               <button
//                 onClick={removeImage}
//                 className="absolute top-1 right-1 w-6 h-6 rounded-full bg-background/80 backdrop-blur-sm flex items-center justify-center hover:bg-destructive hover:text-destructive-foreground transition-colors"
//               >
//                 <X className="w-3.5 h-3.5" />
//               </button>
//             </div>
//           </div>
//         )}

//         <div className="glass-input rounded-2xl input-glow transition-all duration-300">
//           <div className="flex items-end gap-2 p-2">
//             {/* Image Upload Button */}
//             <input
//               type="file"
//               ref={fileInputRef}
//               onChange={handleImageSelect}
//               accept="image/*"
//               className="hidden"
//             />
//             <button
//               onClick={() => fileInputRef.current?.click()}
//               disabled={disabled}
//               className={cn(
//                 "flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-colors",
//                 disabled
//                   ? "text-muted-foreground cursor-not-allowed"
//                   : "text-muted-foreground hover:text-primary hover:bg-primary/10"
//               )}
//             >
//               <ImagePlus className="w-5 h-5" />
//             </button>

//             <div className="flex-1 relative">
//               <textarea
//                 value={message}
//                 onChange={(e) => setMessage(e.target.value)}
//                 onKeyDown={handleKeyDown}
//                 placeholder="Type your message..."
//                 disabled={disabled}
//                 rows={1}
//                 className={cn(
//                   "w-full bg-transparent resize-none outline-none text-foreground placeholder:text-muted-foreground px-3 py-2.5 text-sm max-h-32",
//                   "scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent"
//                 )}
//                 style={{
//                   minHeight: "44px",
//                   height: "auto",
//                 }}
//                 onInput={(e) => {
//                   const target = e.target as HTMLTextAreaElement;
//                   target.style.height = "44px";
//                   target.style.height = Math.min(target.scrollHeight, 128) + "px";
//                 }}
//               />
//             </div>
//             <button
//               onClick={handleSend}
//               disabled={(!message.trim() && !image) || disabled}
//               className={cn(
//                 "flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center send-btn-hover",
//                 (message.trim() || image) && !disabled
//                   ? "bg-primary text-primary-foreground"
//                   : "bg-muted text-muted-foreground cursor-not-allowed"
//               )}
//             >
//               <Send className="w-4 h-4" />
//             </button>
//           </div>
//         </div>
//         <p className="text-center text-xs text-muted-foreground mt-3 flex items-center justify-center gap-1.5">
//           <Sparkles className="w-3 h-3" />
//           Powered by Ghasemian • Press Enter to send
//         </p>
//       </div>
//     </div>
//   );
// };

// export default ChatInput;





import { useState, useRef, useEffect } from "react";
import type { KeyboardEvent } from "react";
import { Send, Sparkles, ImagePlus, X, ChevronDown, Check, Brain } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

export const DEFAULT_MODEL_ID = "gemma3:latest";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

type AIModel = {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  badge?: string;
  badgeColor?: string;
};

function formatModelLabel(id: string): string {
  const base = id.replace(/:latest$/, "");
  if (base === "gemma3") return "Gemma 3";
  if (base === "qwen3:4b") return "Qwen 3 4B";
  if (base.startsWith("qwen3")) return "Qwen 3";
  if (base.startsWith("gemma3")) return "Gemma 3";
  return base;
}

const FALLBACK_MODELS: AIModel[] = [
  {
    id: "gemma3:latest",
    label: "Gemma 3",
    description: "Default · Smart & balanced",
    icon: <Brain className="w-4 h-4" />,
    badge: "Default",
    badgeColor: "bg-primary/20 text-primary",
  },
  {
    id: "qwen3:4b",
    label: "Qwen 3 4B",
    description: "Compact & capable",
    icon: <Sparkles className="w-4 h-4" />,
    badge: "Qwen",
    badgeColor: "bg-cyan-500/20 text-cyan-400",
  },
];

interface ChatInputProps {
  onSend: (message: string, image?: string) => void;
  selectedModelId: string;
  onModelChange: (modelId: string) => void;
  disabled?: boolean;
  replyTo?: {
    content: string;
    isUser: boolean;
  } | null;
  onCancelReply?: () => void;
}

const ChatInput = ({
  onSend,
  selectedModelId,
  onModelChange,
  disabled = false,
  replyTo = null,
  onCancelReply,
}: ChatInputProps) => {
  const [message, setMessage] = useState("");
  const [image, setImage] = useState<string | null>(null);
  const [availableModels, setAvailableModels] = useState<AIModel[]>(FALLBACK_MODELS);
  const [modelMenuOpen, setModelMenuOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const loadModels = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/ollama/available-models`);
        if (!res.ok) return;
        const data = await res.json();
        const ids: string[] = (data.models ?? []).filter(
          (id: string) => !id.toLowerCase().includes("cpu"),
        );
        if (ids.length === 0) return;

        const models: AIModel[] = ids.map((id, index) => ({
          id,
          label: formatModelLabel(id),
          description: "Installed locally",
          icon: id.includes("qwen") ? <Sparkles className="w-4 h-4" /> : <Brain className="w-4 h-4" />,
          badge: index === 0 ? "Default" : undefined,
          badgeColor: index === 0 ? "bg-primary/20 text-primary" : undefined,
        }));
        setAvailableModels(models);

        const preferred =
          ids.find((id) => id.startsWith("gemma3")) ?? ids[0];
        if (!ids.includes(selectedModelId)) {
          onModelChange(preferred);
        }
      } catch {
        // keep fallback list
      }
    };
    loadModels();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onModelChange]);

  const selectedModel =
    availableModels.find((m) => m.id === selectedModelId) ?? availableModels[0];

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
        {replyTo && (
          <div className="mb-2 flex items-start gap-2 rounded-xl border border-primary/30 bg-primary/5 px-3 py-2">
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-primary mb-0.5">
                Replying to {replyTo.isUser ? "You" : "AI"}
              </p>
              <p className="text-xs text-muted-foreground line-clamp-2 whitespace-pre-wrap">
                {replyTo.content}
              </p>
            </div>
            <button
              type="button"
              onClick={onCancelReply}
              className="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
              title="Cancel reply"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

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
            {/* <input
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
            </button> */}

            <div className="flex-1 relative">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={replyTo ? "Write your reply..." : "Type your message..."}
                disabled={disabled}
                rows={1}
                className={cn(
                  "w-full bg-transparent resize-none outline-none text-foreground placeholder:text-muted-foreground px-3 py-2.5 text-sm max-h-32",
                  "scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent"
                )}
                style={{
                  height: "auto",
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  // target.style.height = "44px";
                  target.style.height = Math.min(target.scrollHeight, 128) + "px";
                }}
              />
            </div>

            {/* AI Model Selector */}
            <div className="relative flex-shrink-0">
              <button
                type="button"
                onClick={() => setModelMenuOpen((prev) => !prev)}
                title="Select AI model"
                className={cn(
                  "flex items-center gap-1.5 h-10 px-3 rounded-xl border transition-all duration-200 text-xs font-medium",
                  modelMenuOpen
                    ? "border-primary/60 bg-primary/10 text-primary"
                    : "border-border/50 bg-background/40 text-muted-foreground hover:border-primary/40 hover:text-primary hover:bg-primary/5"
                )}
              >
                <span className={cn("transition-colors", modelMenuOpen ? "text-primary" : "")}>
                  {selectedModel.icon}
                </span>
                <span className="hidden sm:inline max-w-[80px] truncate">
                  {selectedModel.label.replace("Claude ", "")}
                </span>
                <ChevronDown
                  className={cn(
                    "w-3 h-3 transition-transform duration-200",
                    modelMenuOpen && "rotate-180"
                  )}
                />
              </button>

              {/* Dropdown */}
              {modelMenuOpen && (
                <>
                  {/* Backdrop */}
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setModelMenuOpen(false)}
                  />

                  <div className="absolute bottom-full mb-2 right-0 z-20 w-64 rounded-xl border border-border/60 bg-card/95 backdrop-blur-xl shadow-xl shadow-black/20 overflow-hidden">
                    {/* Header */}
                    <div className="px-3 py-2 border-b border-border/40">
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Select Model
                      </p>
                    </div>

                    {/* Model list */}
                    <div className="p-1.5 space-y-0.5">
                      {availableModels.map((model) => {
                        const isSelected = selectedModelId === model.id;
                        return (
                          <button
                            type="button"
                            key={model.id}
                            onClick={() => {
                              onModelChange(model.id);
                              setModelMenuOpen(false);
                              toast({
                                title: "Model changed",
                                description: `Now using ${model.label} (${model.id})`,
                                duration: 2000,
                              });
                            }}
                            className={cn(
                              "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-150 text-left",
                              isSelected
                                ? "bg-primary/15 text-foreground"
                                : "text-foreground/80 hover:bg-accent hover:text-foreground"
                            )}
                          >
                            {/* Icon */}
                            <div
                              className={cn(
                                "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors",
                                isSelected
                                  ? "bg-primary/20 text-primary"
                                  : "bg-muted text-muted-foreground"
                              )}
                            >
                              {model.icon}
                            </div>

                            {/* Text */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-medium truncate">
                                  {model.label}
                                </span>
                                {model.badge && (
                                  <span
                                    className={cn(
                                      "text-[10px] font-semibold px-1.5 py-0.5 rounded-full flex-shrink-0",
                                      model.badgeColor
                                    )}
                                  >
                                    {model.badge}
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-muted-foreground truncate">
                                {model.description}
                              </p>
                            </div>

                            {/* Check */}
                            {isSelected && (
                              <Check className="w-4 h-4 text-primary flex-shrink-0" />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Send Button */}
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
