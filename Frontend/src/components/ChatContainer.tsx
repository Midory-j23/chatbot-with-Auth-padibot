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

const decodeSseChunk = (raw: string) => raw.replace(/\\n/g, "\n");

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
  const activeSessionIdRef = useRef<number | null>(null);
  const streamingSessionIdRef = useRef<number | null>(null);
  const explicitStopRef = useRef(false);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    activeSessionIdRef.current = activeSessionId;
  }, [activeSessionId]);

  const formatMessagesFromApi = useCallback((rawMessages: any[]): Message[] => {
    return rawMessages.map((m: any) => {
      const parsed = decodeReplyMessage(m.message ?? "");
      return {
        id: m.id,
        content: parsed.content,
        isUser: m.sender === "user",
        created_at: m.created_at,
        replyTo: parsed.replyTo,
      };
    });
  }, []);

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const handleUnauthorized = useCallback(() => {
    toast({
      title: "Session expired",
      description: "Please sign in again.",
      variant: "destructive",
    });
    navigate("/auth");
  }, [navigate]);

  const pollForAssistantReply = useCallback(
    (sessionId: number) => {
      stopPolling();
      let attempts = 0;
      let lastContent = "";
      let stableCount = 0;

      const pollOnce = async () => {
        attempts += 1;
        if (attempts > 60 || activeSessionIdRef.current !== sessionId) {
          stopPolling();
          if (activeSessionIdRef.current === sessionId) {
            setIsTyping(false);
            setIsStreaming(false);
          }
          return;
        }
        try {
          const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
            credentials: "include",
          });
          if (res.status === 401) {
            stopPolling();
            handleUnauthorized();
            return;
          }
          if (!res.ok) return;
          const data = await res.json();
          const msgs = data.messages ?? [];
          const last = msgs[msgs.length - 1];
          const isGenerating = Boolean(data.is_generating);

          if (msgs.length === 0) {
            if (!isGenerating && activeSessionIdRef.current === sessionId) {
              setIsTyping(false);
              setIsStreaming(false);
              stopPolling();
            }
            return;
          }

          if (last?.sender === "assistant") {
            if (streamingSessionIdRef.current === sessionId) {
              return;
            }
            const formatted = formatMessagesFromApi(msgs);
            const content = formatted[formatted.length - 1]?.content ?? "";
            if (activeSessionIdRef.current === sessionId) {
              setMessages(formatted);
              if (isGenerating || !content.trim()) {
                setIsTyping(true);
              } else {
                setIsTyping(false);
              }
            }
            if (!isGenerating) {
              if (content === lastContent) {
                stableCount += 1;
              } else {
                stableCount = 0;
                lastContent = content;
              }
              if (stableCount >= 2 && content.trim()) {
                stopPolling();
                if (activeSessionIdRef.current === sessionId) {
                  setIsStreaming(false);
                  setIsTyping(false);
                }
                try {
                  const sRes = await fetch(`${API_BASE}/api/sessions`, {
                    credentials: "include",
                  });
                  if (sRes.ok) setSessions(await sRes.json());
                } catch {
                  // ignore
                }
              }
            } else {
              stableCount = 0;
              lastContent = content;
            }
          } else if (last?.sender === "user" || isGenerating) {
            if (activeSessionIdRef.current === sessionId) {
              setIsStreaming(isGenerating);
              if (last?.sender === "user") {
                setMessages((prev) => {
                  const lastMsg = prev[prev.length - 1];
                  if (lastMsg && !lastMsg.isUser) return prev;
                  return [
                    ...formatMessagesFromApi(msgs),
                    { id: `pending-${sessionId}`, content: "", isUser: false },
                  ];
                });
              }
            }
          }
        } catch {
          // keep polling
        }
      };

      pollOnce();
      pollTimerRef.current = setInterval(pollOnce, 2000);
    },
    [formatMessagesFromApi, stopPolling, handleUnauthorized],
  );

  useEffect(() => () => stopPolling(), [stopPolling]);

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
    stopPolling();

    if (!activeSessionId) {
      if (!skipMessageReloadRef.current) {
        setMessages([]);
      }
      setIsTyping(false);
      setIsStreaming(false);
      return;
    }

    const activelySending = sendingSessionIdRef.current === activeSessionId;

    // Keep optimistic first-message UI while creating/sending in a new session
    if (skipMessageReloadRef.current || activelySending) {
      skipMessageReloadRef.current = false;
      if (!activelySending) {
        setIsTyping(false);
        setIsStreaming(false);
      }
      return;
    }

    setIsTyping(false);
    setIsStreaming(false);

    const loadMessages = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/sessions/${activeSessionId}`, {
          credentials: "include",
        });
        if (res.status === 401) {
          handleUnauthorized();
          return;
        }
        if (!res.ok) throw new Error("Failed to load conversation");
        const data = await res.json();
        const formatted = formatMessagesFromApi(data.messages ?? []);
        const last = formatted[formatted.length - 1];
        const isGenerating = Boolean(data.is_generating);
        const awaitingReply =
          formatted.length > 0 &&
          (isGenerating ||
            !!last?.isUser ||
            (last && !last.isUser && !last.content.trim()));

        if (awaitingReply && last?.isUser) {
          setMessages([
            ...formatted,
            { id: `pending-${activeSessionId}`, content: "", isUser: false },
          ]);
          setIsTyping(false);
          setIsStreaming(isGenerating);
          pollForAssistantReply(activeSessionId);
        } else if (awaitingReply) {
          setMessages(formatted);
          setIsTyping(false);
          setIsStreaming(isGenerating);
          pollForAssistantReply(activeSessionId);
        } else {
          setMessages(formatted);
          setIsTyping(false);
          setIsStreaming(false);
        }
        setReplyTo(null);
      } catch (err) {
        console.error("Load messages error:", err);
        toast({ title: "خطا", description: "بارگذاری گفتگو ناموفق بود", variant: "destructive" });
      }
    };
    loadMessages();
  }, [activeSessionId, formatMessagesFromApi, pollForAssistantReply, stopPolling, handleUnauthorized]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, isTyping, isStreaming, scrollToBottom]);

  const refreshSessions = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/sessions`, { credentials: "include" });
      if (res.status === 401) {
        navigate("/auth");
        return;
      }
      if (res.ok) setSessions(await res.json());
    } catch (err) {
      console.error("Failed to refresh sessions:", err);
    }
  };

  const isStreamInterruptError = (error: unknown) => {
    if (error instanceof DOMException && error.name === "AbortError") return true;
    if (error instanceof TypeError) {
      const msg = error.message.toLowerCase();
      return msg.includes("input stream") || msg.includes("networkerror");
    }
    return false;
  };

  const handleStopStreaming = async () => {
    const sessionId = activeSessionId;
    const stoppedAssistantId = activeAssistantIdRef.current;
    // Hold local refs before any async work so finally in streamResponse can't race them away
    const reader = streamReaderRef.current;
    const controller = abortControllerRef.current;
    explicitStopRef.current = true;
    streamEpochRef.current += 1;

    // Tell backend to hang up Ollama NOW (stops CPU), in parallel with aborting the UI stream
    const cancelPromise =
      sessionId != null
        ? fetch(`${API_BASE}/api/sessions/${sessionId}/cancel`, {
            method: "POST",
            credentials: "include",
            keepalive: true,
          }).catch((err) => {
            console.error("Cancel stream error:", err);
          })
        : Promise.resolve();

    activeAssistantIdRef.current = null;
    streamingSessionIdRef.current = null;

    if (controller) {
      controller.abort();
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
      }
    }
    if (reader) {
      try {
        await reader.cancel();
      } catch {
        // already closed / raced with streamResponse finally
      }
      if (streamReaderRef.current === reader) {
        streamReaderRef.current = null;
      }
    }

    // Keep whatever was already written; only drop a still-empty placeholder bubble.
    setMessages((prev) => {
      if (!stoppedAssistantId) return prev;
      return prev.filter((m) => {
        if (m.id !== stoppedAssistantId) return true;
        return Boolean(m.content.trim() || m.thinking?.trim());
      });
    });
    setIsStreaming(false);
    setIsTyping(false);

    await cancelPromise;

    toast({
      title: "Stopped",
      description: "Generation stopped. Partial reply was kept.",
    });
  };

  const streamResponse = async (
    response: Response,
    tempMessageId: string,
    signal: AbortSignal,
    epoch: number,
    streamSessionId: number,
  ): Promise<boolean> => {
    setIsStreaming(true);
    streamingSessionIdRef.current = streamSessionId;
    explicitStopRef.current = false;
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let fullContent = "";
    let fullThinking = "";
    let wasStopped = false;

    const patchAssistantMessage = () => {
      patchMessage((m) => ({
        ...m,
        content: fullContent,
        thinking: fullThinking.trim() || undefined,
      }));
    };

    const isCurrentStream = () =>
      streamEpochRef.current === epoch && !signal.aborted;

    const patchMessage = (updater: (m: Message) => Message) => {
      if (activeSessionIdRef.current !== streamSessionId) return;
      setMessages((prev) =>
        prev.map((m) => (m.id === tempMessageId ? updater(m) : m)),
      );
    };

    if (!reader) {
      setIsStreaming(false);
      streamingSessionIdRef.current = null;
      return false;
    }
    streamReaderRef.current = reader;
    activeAssistantIdRef.current = tempMessageId;
    let lineBuffer = "";

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

        lineBuffer += decoder.decode(value, { stream: true });
        const lines = lineBuffer.split("\n");
        lineBuffer = lines.pop() ?? "";

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
          if (content === "[THINK_END]") {
            patchAssistantMessage();
            continue;
          }
          if (content.startsWith("[FINAL]")) {
            fullContent = decodeSseChunk(content.substring(7));
            patchAssistantMessage();
            scrollToBottom();
            continue;
          }
          if (content.startsWith("[MODEL]")) {
            const modelName = content.substring(7).trim();
            patchMessage((m) => ({ ...m, model: modelName }));
            continue;
          }
          if (content.startsWith("[THINK]")) {
            fullThinking += decodeSseChunk(content.substring(7));
            patchAssistantMessage();
            scrollToBottom();
            continue;
          }
          if (content.startsWith("[ERROR]")) {
            console.error("Stream error:", content);
            fullContent = "خطا رخ داد. لطفاً دوباره تلاش کنید.";
            patchAssistantMessage();
            break;
          }
          if (content) {
            fullContent += decodeSseChunk(content);
            patchAssistantMessage();
            scrollToBottom();
          }
        }
        if (wasStopped) break;
      }
      if (lineBuffer.startsWith("data: ") && isCurrentStream() && !wasStopped) {
        const content = lineBuffer.substring(6);
        if (content.startsWith("[FINAL]")) {
          fullContent = decodeSseChunk(content.substring(7));
          patchAssistantMessage();
        } else if (content.startsWith("[THINK]")) {
          fullThinking += decodeSseChunk(content.substring(7));
          patchAssistantMessage();
        } else if (content && !content.startsWith("[")) {
          fullContent += decodeSseChunk(content);
          patchAssistantMessage();
        }
      }
      patchAssistantMessage();
    } catch (error: unknown) {
      if (
        isStreamInterruptError(error) ||
        signal.aborted ||
        streamEpochRef.current !== epoch
      ) {
        wasStopped = true;
      } else {
        console.error("Streaming error:", error);
        if (isCurrentStream()) {
          patchMessage((m) => ({
            ...m,
            content: "خطا: دریافت پاسخ ناموفق بود",
          }));
        }
      }
    } finally {
      if (streamReaderRef.current === reader) {
        streamReaderRef.current = null;
      }
      if (activeAssistantIdRef.current === tempMessageId) {
        activeAssistantIdRef.current = null;
      }
      if (streamingSessionIdRef.current === streamSessionId) {
        streamingSessionIdRef.current = null;
      }
      if (streamEpochRef.current === epoch) {
        setIsStreaming(false);
      }
      scrollToBottom();
      // On Stop: leave the partial assistant message in the thread as-is.
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

    // If a previous generation is still winding down in THIS session, cancel it first
    if ((isStreaming || abortControllerRef.current) && streamingSessionIdRef.current === sessionId) {
      const prevReader = streamReaderRef.current;
      const prevController = abortControllerRef.current;
      explicitStopRef.current = true;
      streamEpochRef.current += 1;
      try {
        await fetch(`${API_BASE}/api/sessions/${sessionId}/cancel`, {
          method: "POST",
          credentials: "include",
        });
      } catch {
        // ignore
      }
      prevController?.abort();
      if (abortControllerRef.current === prevController) {
        abortControllerRef.current = null;
      }
      if (prevReader) {
        try {
          await prevReader.cancel();
        } catch {
          // ignore
        }
        if (streamReaderRef.current === prevReader) {
          streamReaderRef.current = null;
        }
      }
      activeAssistantIdRef.current = null;
      setIsStreaming(false);
      setIsTyping(false);
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

    const tempAssistantId = `ai-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { id: tempAssistantId, content: "", isUser: false, model },
    ]);
    setIsTyping(false);
    setIsStreaming(true);
    streamingSessionIdRef.current = sessionId;
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
      if (!res.ok) {
        if (res.status === 401) {
          setMessages((prev) => prev.filter((m) => m.id !== tempAssistantId));
          setIsStreaming(false);
          handleUnauthorized();
          return;
        }
        throw new Error(`Server error: ${res.status}`);
      }

      if (streamEpochRef.current !== epoch || signal.aborted) {
        setIsStreaming(false);
        return;
      }

      const stopped = await streamResponse(
        res,
        tempAssistantId,
        signal,
        epoch,
        sessionId,
      );
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
      setMessages((prev) => prev.filter((m) => m.id !== tempAssistantId));
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
      stopPolling();
      setIsTyping(false);
      setIsStreaming(false);
      streamingSessionIdRef.current = null;
      activeAssistantIdRef.current = null;

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

  const detachFromStream = () => {
    streamEpochRef.current += 1;
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    streamReaderRef.current?.cancel().catch(() => {});
    streamReaderRef.current = null;
    activeAssistantIdRef.current = null;
    streamingSessionIdRef.current = null;
    setIsStreaming(false);
    setIsTyping(false);
  };

  const handleSelectConversation = (id: number) => {
    stopPolling();
    if (activeSessionId !== id && (isStreaming || abortControllerRef.current)) {
      // Leave backend generation running; only detach this UI stream
      detachFromStream();
    } else if (activeSessionId !== id) {
      setIsTyping(false);
      setIsStreaming(false);
    }
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
        stopPolling();
        setIsTyping(false);
        setIsStreaming(false);
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
            {messages.length === 0 ? (
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
                {isTyping && messages.every((m) => m.isUser) && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        <ChatInput
          onSend={(message, image) => handleSend(message, image)}
          disabled={isStreaming && messages.some((m) => !m.isUser)}
          isStreaming={isStreaming}
          onStopStreaming={handleStopStreaming}
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
