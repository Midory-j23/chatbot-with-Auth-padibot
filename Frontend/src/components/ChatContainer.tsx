// src/components/ChatContainer.tsx
import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ChatHeader from "./ChatHeader";
import ChatMessage from "./ChatMessage";
import ChatInput, { DEFAULT_MODEL_ID } from "./ChatInput";
import TypingIndicator from "./TypingIndicator";
import WelcomeState from "./WelcomeState";
import ChatSidebar from "./ChatSidebar";
import { useAuth } from "@/hooks/AuthContext";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";
import {
  decodeReplyMessage,
  encodeReplyMessage,
  type ReplyTarget,
} from "@/lib/replyMessage";

type Message = {
  id: string | number;
  content: string;
  isUser: boolean;
  image?: string;
  created_at?: string;
  thinking?: string;
  model?: string;
  replyTo?: {
    content: string;
    isUser: boolean;
  };
};

type Conversation = {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  last_message_preview?: string;
};

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const ChatContainer = () => {
  const navigate = useNavigate();
  const { sessionId: urlSessionId } = useParams<{ sessionId: string }>();
  const { user } = useAuth();

  const [sessions, setSessions] = useState<Conversation[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const streamReaderRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null);
  const streamEpochRef = useRef(0);
  const activeAssistantIdRef = useRef<string | null>(null);
  const [selectedModelId, setSelectedModelId] = useState(() => {
    try {
      return localStorage.getItem("chatbot-selected-model") || DEFAULT_MODEL_ID;
    } catch {
      return DEFAULT_MODEL_ID;
    }
  });
  const selectedModelRef = useRef(selectedModelId);
  const [replyTo, setReplyTo] = useState<ReplyTarget | null>(null);
  const skipMessageReloadRef = useRef(false);
  const sendingSessionIdRef = useRef<number | null>(null);

  const handleModelChange = useCallback((modelId: string) => {
    selectedModelRef.current = modelId;
    setSelectedModelId(modelId);
    try {
      localStorage.setItem("chatbot-selected-model", modelId);
    } catch {
      // ignore storage errors
    }
  }, []);

  // Check auth & load sessions
  useEffect(() => {
    const checkAuthAndLoad = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/sessions`, { credentials: "include" });
        if (!res.ok) {
          if (res.status === 401) { navigate("/auth"); return; }
          throw new Error("Failed to fetch sessions");
        }
        const data: Conversation[] = await res.json();
        setSessions(data);
      } catch (err) {
        console.error("Auth/sessions error:", err);
        navigate("/auth");
      }
    };
    checkAuthAndLoad();
  }, [navigate]);

  // Sync URL -> active session
  useEffect(() => {
    if (urlSessionId) {
      const id = Number(urlSessionId);
      if (!Number.isNaN(id)) {
        setActiveSessionId(id);
        return;
      }
    }
    // Don't clear mid first-message send while URL is catching up
    if (sendingSessionIdRef.current != null) return;
    setActiveSessionId(null);
  }, [urlSessionId]);

  // Load messages when active session changes
  useEffect(() => {
    if (!activeSessionId) {
      if (!skipMessageReloadRef.current) {
        setMessages([]);
      }
      return;
    }

    // Keep optimistic first-message UI while creating/sending in a new session
    if (
      skipMessageReloadRef.current ||
      sendingSessionIdRef.current === activeSessionId
    ) {
      skipMessageReloadRef.current = false;
      return;
    }

    const loadMessages = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/sessions/${activeSessionId}`, {
          credentials: "include",
        });
        if (!res.ok) throw new Error("Failed to load conversation");
        const data = await res.json();
        const formatted: Message[] = data.messages.map((m: any) => {
          const parsed = decodeReplyMessage(m.message ?? "");
          return {
            id: m.id,
            content: parsed.content,
            isUser: m.sender === "user",
            created_at: m.created_at,
            replyTo: parsed.replyTo,
          };
        });
        setMessages(formatted);
        setReplyTo(null);
      } catch (err) {
        console.error("Load messages error:", err);
        toast({ title: "خطا", description: "بارگذاری گفتگو ناموفق بود", variant: "destructive" });
      }
    };
    loadMessages();
  }, [activeSessionId]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, isTyping, isStreaming, scrollToBottom]);

  const removeIncompleteAssistantFromUi = useCallback((prev: Message[]) => {
    if (prev.length === 0) return prev;
    const last = prev[prev.length - 1];
    if (!last.isUser) {
      return prev.slice(0, -1);
    }
    return prev;
  }, []);

  const refreshSessions = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/sessions`, { credentials: "include" });
      if (res.ok) setSessions(await res.json());
    } catch (err) {
      console.error("Failed to refresh sessions:", err);
    }
  };

  const handleStopStreaming = async () => {
    const sessionId = activeSessionId;
    const stoppedAssistantId = activeAssistantIdRef.current;

    // Invalidate any in-flight stream updates immediately
    streamEpochRef.current += 1;
    activeAssistantIdRef.current = null;

    // Stop UI stream first so the bubble freezes/disappears instantly
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    streamReaderRef.current?.cancel().catch(() => {});
    streamReaderRef.current = null;

    setMessages((prev) => {
      if (stoppedAssistantId) {
        return prev.filter((m) => m.id !== stoppedAssistantId);
      }
      return removeIncompleteAssistantFromUi(prev);
    });
    setIsStreaming(false);
    setIsTyping(false);

    // Then cancel backend generation so it won't save or continue
    if (sessionId) {
      try {
        await fetch(`${API_BASE}/api/sessions/${sessionId}/cancel`, {
          method: "POST",
          credentials: "include",
        });
      } catch (err) {
        console.error("Cancel stream error:", err);
      }
    }

    toast({
      title: "Stopped",
      description: "Generation stopped. Your question was kept — ask again anytime.",
    });
  };

  const streamResponse = async (
    response: Response,
    tempMessageId: string,
    signal: AbortSignal,
    epoch: number,
  ): Promise<boolean> => {
    setIsStreaming(true);
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let fullContent = "";
    let fullThinking = "";
    let wasStopped = false;

    const isCurrentStream = () =>
      streamEpochRef.current === epoch && !signal.aborted;

    if (!reader) {
      setIsStreaming(false);
      return false;
    }
    streamReaderRef.current = reader;
    activeAssistantIdRef.current = tempMessageId;

    try {
      while (true) {
        if (!isCurrentStream()) {
          wasStopped = true;
          break;
        }
        const { value, done } = await reader.read();
        if (done) break;
        if (!isCurrentStream()) {
          wasStopped = true;
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          if (!isCurrentStream()) {
            wasStopped = true;
            break;
          }
          const content = line.substring(6);
          if (content === "[DONE]") continue;
          if (content === "[CANCELLED]") {
            wasStopped = true;
            break;
          }
          if (content === "[THINK_END]") continue;
          if (content.startsWith("[MODEL]")) {
            const modelName = content.substring(7).trim();
            setMessages((prev) =>
              prev.map((m) =>
                m.id === tempMessageId ? { ...m, model: modelName } : m,
              ),
            );
            continue;
          }
          if (content.startsWith("[THINK]")) {
            fullThinking += content.substring(7);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === tempMessageId ? { ...m, thinking: fullThinking } : m,
              ),
            );
            scrollToBottom();
            continue;
          }
          if (content.startsWith("[ERROR]")) {
            console.error("Stream error:", content);
            fullContent += "خطا رخ داد. لطفاً دوباره تلاش کنید.";
            setMessages((prev) =>
              prev.map((m) =>
                m.id === tempMessageId ? { ...m, content: fullContent } : m,
              ),
            );
            break;
          }
          if (content) {
            fullContent += content;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === tempMessageId ? { ...m, content: fullContent } : m,
              ),
            );
            scrollToBottom();
          }
        }
        if (wasStopped) break;
      }
    } catch (error: unknown) {
      if (
        error instanceof DOMException &&
        (error.name === "AbortError" || signal.aborted)
      ) {
        wasStopped = true;
      } else if (signal.aborted || streamEpochRef.current !== epoch) {
        wasStopped = true;
      } else {
        console.error("Streaming error:", error);
        if (isCurrentStream()) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === tempMessageId
                ? { ...m, content: "خطا: دریافت پاسخ ناموفق بود" }
                : m,
            ),
          );
        }
      }
    } finally {
      if (streamReaderRef.current === reader) {
        streamReaderRef.current = null;
      }
      if (activeAssistantIdRef.current === tempMessageId) {
        activeAssistantIdRef.current = null;
      }
      if (streamEpochRef.current === epoch) {
        setIsStreaming(false);
      }
      scrollToBottom();

      if (wasStopped || streamEpochRef.current !== epoch) {
        setMessages((prev) => prev.filter((m) => m.id !== tempMessageId));
        wasStopped = true;
      }
    }
    return wasStopped;
  };

  const handleSend = async (
    content: string,
    image?: string,
    sessionIdOverride?: number | null,
  ) => {
    if (!content.trim() && !image) return;
    const model = selectedModelRef.current || selectedModelId;
    console.log("[chat] sending with model:", model);
    const sessionId = sessionIdOverride ?? activeSessionId;
    const activeReply = replyTo;
    if (!sessionId) { await handleNewConversation(content); return; }

    // If a previous generation is still winding down, cancel it first
    if (isStreaming || abortControllerRef.current) {
      streamEpochRef.current += 1;
      abortControllerRef.current?.abort();
      abortControllerRef.current = null;
      streamReaderRef.current?.cancel().catch(() => {});
      streamReaderRef.current = null;
      activeAssistantIdRef.current = null;
      setIsStreaming(false);
      setIsTyping(false);
      try {
        await fetch(`${API_BASE}/api/sessions/${sessionId}/cancel`, {
          method: "POST",
          credentials: "include",
        });
      } catch {
        // ignore
      }
    }

    sendingSessionIdRef.current = sessionId;

    const storedMessage = activeReply
      ? encodeReplyMessage(content, activeReply)
      : content;

    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      content,
      isUser: true,
      image,
      replyTo: activeReply
        ? { content: activeReply.content, isUser: activeReply.isUser }
        : undefined,
    };
    setMessages((prev) => [...prev, userMessage]);
    setReplyTo(null);
    setIsTyping(true);
    scrollToBottom();

    const epoch = ++streamEpochRef.current;

    try {
      abortControllerRef.current = new AbortController();
      const { signal } = abortControllerRef.current;

      const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: storedMessage,
          image,
          model,
          reply_to: activeReply
            ? {
                content: activeReply.content,
                role: activeReply.isUser ? "user" : "assistant",
              }
            : null,
        }),
        credentials: "include",
        signal,
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);

      if (streamEpochRef.current !== epoch || signal.aborted) {
        setIsTyping(false);
        return;
      }

      const tempAssistantId = `ai-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        { id: tempAssistantId, content: "", isUser: false, model },
      ]);
      setIsTyping(false);

      const stopped = await streamResponse(res, tempAssistantId, signal, epoch);
      if (abortControllerRef.current?.signal === signal) {
        abortControllerRef.current = null;
      }
      if (!stopped && streamEpochRef.current === epoch) {
        await refreshSessions();
      }
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setIsTyping(false);
        setIsStreaming(false);
        return;
      }
      console.error("Send message error:", err);
      setIsTyping(false);
      setIsStreaming(false);
      toast({ title: "خطا", description: "دریافت پاسخ ناموفق بود", variant: "destructive" });
    } finally {
      if (sendingSessionIdRef.current === sessionId) {
        sendingSessionIdRef.current = null;
      }
    }
  };

  const handleNewConversation = async (firstMessage?: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: firstMessage ? firstMessage.slice(0, 40) : "New Chat" }),
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to create session");

      const newSession: Conversation = await res.json();
      skipMessageReloadRef.current = true;
      sendingSessionIdRef.current = firstMessage ? newSession.id : null;
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      if (!firstMessage) {
        setMessages([]);
      }
      setReplyTo(null);
      navigate(`/chat/${newSession.id}`);

      if (firstMessage) {
        await handleSend(firstMessage, undefined, newSession.id);
      }
    } catch (err) {
      console.error("Create session error:", err);
      skipMessageReloadRef.current = false;
      sendingSessionIdRef.current = null;
      toast({ title: "خطا", description: "ایجاد گفتگوی جدید ناموفق بود", variant: "destructive" });
    }
  };

  const handleSelectConversation = (id: number) => {
    sendingSessionIdRef.current = null;
    skipMessageReloadRef.current = false;
    navigate(`/chat/${id}`);
  };

  const handleDeleteConversation = async (id: number): Promise<void> => {
    try {
      const res = await fetch(`${API_BASE}/api/sessions/${id}`, {
        method: "DELETE", credentials: "include",
      });
      if (!res.ok) {
        const msg = res.status === 404 ? "گفتگو یافت نشد" : "حذف ناموفق بود";
        throw new Error(msg);
      }
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeSessionId === id) {
        setActiveSessionId(null);
        setMessages([]);
        navigate("/");
      }
      toast({ title: "گفتگو حذف شد" });
    } catch (err) {
      console.error("Delete error:", err);
      toast({
        title: "خطا",
        description: err instanceof Error ? err.message : "حذف گفتگو ناموفق بود",
        variant: "destructive",
      });
      throw err;
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    toast({ title: "گفتگو پاک شد (فقط محلی)" });
  };

  const sidebarConversations = sessions.map((s) => ({
    id: s.id,
    title: s.title || "Untitled",
    lastMessage: s.last_message_preview || "",
    createdAt: new Date(s.updated_at || s.created_at),
  }));

  return (
    <div className="flex h-screen max-h-screen bg-background">
      <ChatSidebar
        conversations={sidebarConversations}
        activeConversationId={activeSessionId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={() => handleNewConversation()}
        onDeleteConversation={handleDeleteConversation}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        userEmail={user?.email ?? ""}
      />

      <div
        className={cn(
          "flex flex-col flex-1 h-full transition-all duration-300",
          sidebarOpen ? "md:ml-72" : "ml-0"
        )}
      >
        <div className="fixed inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gradient-to-b from-primary/5 to-transparent rounded-full blur-3xl" />
        </div>

        <ChatHeader
          onClearChat={handleClearChat}
          messageCount={messages.length}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          isStreaming={isStreaming}
          onStopStreaming={handleStopStreaming}
        />

        <div className="flex-1 overflow-y-auto relative">
          <div className="max-w-4xl mx-auto">
            {messages.length === 0 && !activeSessionId ? (
              <WelcomeState />
            ) : (
              <div className="py-4">
                {messages.map((msg) => (
                  <ChatMessage
                    key={msg.id}
                    message={msg.content}
                    thinking={msg.thinking}
                    isUser={msg.isUser}
                    image={msg.image}
                    model={msg.model}
                    replyTo={msg.replyTo}
                    canReply={!isTyping && !isStreaming && !!msg.content.trim()}
                    onReply={() =>
                      setReplyTo({
                        id: msg.id,
                        content: msg.content,
                        isUser: msg.isUser,
                      })
                    }
                  />
                ))}
                {isTyping && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        <ChatInput
          onSend={(message, image) => handleSend(message, image)}
          disabled={isTyping || isStreaming}
          selectedModelId={selectedModelId}
          onModelChange={handleModelChange}
          replyTo={replyTo}
          onCancelReply={() => setReplyTo(null)}
        />
      </div>
    </div>
  );
};

export default ChatContainer;
