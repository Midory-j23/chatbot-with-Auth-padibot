import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import ChatHeader from "./ChatHeader";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import TypingIndicator from "./TypingIndicator";
import WelcomeState from "./WelcomeState";
import ChatSidebar from "./ChatSidebar";
import { useAuth } from "@/hooks/AuthContext";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

type Message = {
  id: string | number;
  content: string;
  isUser: boolean;
  image?: string;
  created_at?: string;
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
  const { user } = useAuth();

  const [sessions, setSessions] = useState<Conversation[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Check auth & load sessions
  useEffect(() => {
    const checkAuthAndLoad = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/sessions`, {
          credentials: "include",
        });

        if (!res.ok) {
          if (res.status === 401) {
            navigate("/auth");
            return;
          }
          throw new Error("Failed to fetch sessions");
        }

        const data = await res.json();
        setSessions(data);

        // Auto-select most recent session if exists
        if (data.length > 0) {
          setActiveSessionId(data[0].id);
        }
      } catch (err) {
        console.error("Auth/sessions error:", err);
        navigate("/auth");
      }
    };

    checkAuthAndLoad();
  }, [navigate]);

  // Load messages when active session changes
  useEffect(() => {
    if (!activeSessionId) {
      setMessages([]);
      return;
    }

    const loadMessages = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/sessions/${activeSessionId}`, {
          credentials: "include",
        });

        if (!res.ok) throw new Error("Failed to load conversation");

        const data = await res.json();
        const formattedMessages = data.messages.map((m: any) => ({
          id: m.id,
          content: m.message,
          isUser: m.sender === "user",
          created_at: m.created_at,
        }));

        setMessages(formattedMessages);
      } catch (err) {
        console.error("Load messages error:", err);
        toast({
          title: "Error",
          description: "Could not load conversation",
          variant: "destructive",
        });
      }
    };

    loadMessages();
  }, [activeSessionId]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, isStreaming, scrollToBottom]);

  const handleStopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setIsTyping(false);
  };

  const streamResponse = async (
    response: Response,
    tempMessageId: string,
    _sessionId: number,
  ) => {
    setIsStreaming(true);
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let fullContent = "";

    if (!reader) {
      setIsStreaming(false);
      return;
    }

    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        // SSE format: data: chunk\n\n
        const lines = chunk.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const content = line.replace("data: ", "").trim();
            if (content === "[DONE]" || content === "") continue;
            fullContent += content;

            setMessages((prev) =>
              prev.map((m) =>
                m.id === tempMessageId ? { ...m, content: fullContent } : m,
              ),
            );
          }
        }
      }
    } catch (error: any) {
      if (error.name === "AbortError") {
        console.log("Streaming aborted by user");
      } else {
        console.error("Streaming error:", error);
      }
    } finally {
      setIsStreaming(false);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === tempMessageId
            ? { ...m, content: fullContent || "Response stopped." }
            : m,
        ),
      );
      scrollToBottom();
    }
  };

  const handleSend = async (
    content: string,
    image?: string,
    sessionIdOverride?: number | null,
  ) => {
    if (!content.trim() && !image) return;
    const sessionId = sessionIdOverride ?? activeSessionId;
    if (!sessionId) {
      // Create new session first, then send (pass new id so we don't re-enter)
      await handleNewConversation(content);
      return;
    }

    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      content,
      isUser: true,
      image,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);
    scrollToBottom();

    try {
      abortControllerRef.current = new AbortController();

      const res = await fetch(
        `${API_BASE}/api/sessions/${sessionId}/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ message: content, image }),
          credentials: "include",
          signal: abortControllerRef.current.signal,
        },
      );

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

      const tempAssistantId = `ai-${Date.now()}`;
      const assistantPlaceholder: Message = {
        id: tempAssistantId,
        content: "",
        isUser: false,
      };

      setMessages((prev) => [...prev, assistantPlaceholder]);
      setIsTyping(false);

      await streamResponse(res, tempAssistantId, sessionId);

      // Refresh session list (title may have changed)
      const sessionsRes = await fetch(`${API_BASE}/api/sessions`, {
        credentials: "include",
      });
      if (sessionsRes.ok) {
        setSessions(await sessionsRes.json());
      }
    } catch (err: any) {
      console.error("Send message error:", err);
      setIsTyping(false);
      setMessages(
        (prev) => prev.filter((m) => m.id !== `temp-${Date.now()}`), // cleanup failed user msg?
      );
      toast({
        title: "Error",
        description: "Failed to get response",
        variant: "destructive",
      });
    }
  };

  const handleNewConversation = async (firstMessage?: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: firstMessage ? firstMessage.slice(0, 40) : "New Chat",
        }),
        credentials: "include",
      });

      if (!res.ok) throw new Error("Failed to create session");

      const newSession = await res.json();
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setMessages([]);

      if (firstMessage) {
        await handleSend(firstMessage, undefined, newSession.id);
      }
    } catch (err) {
      console.error("Create session error:", err);
      toast({
        title: "Error",
        description: "Could not create new conversation",
        variant: "destructive",
      });
    }
  };

  const handleSelectConversation = (id: number) => {
    setActiveSessionId(id);
  };

  const handleDeleteConversation = async (id: number): Promise<void> => {
    try {
      const res = await fetch(`${API_BASE}/api/sessions/${id}`, {
        method: "DELETE",
        credentials: "include",
      });

      if (!res.ok) {
        const msg = res.status === 404 ? "Conversation not found" : "Delete failed";
        throw new Error(msg);
      }

      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeSessionId === id) {
        setActiveSessionId(null);
        setMessages([]);
      }
      toast({ title: "Conversation deleted" });
    } catch (err) {
      console.error("Delete error:", err);
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to delete conversation",
        variant: "destructive",
      });
      throw err; // rethrow so sidebar can keep dialog open if desired
    }
  };

  const handleClearChat = () => {
    // Optional: you can add a clear endpoint later
    // For now, just reset UI
    setMessages([]);
    toast({ title: "Chat cleared (local only)" });
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
        activeConversationId={activeSessionId} // ← no .toString()
        onSelectConversation={handleSelectConversation} // ← no need for Number()
        onNewConversation={() => handleNewConversation()}
        onDeleteConversation={handleDeleteConversation} // ← no Number()
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        userEmail={user?.email ?? ""}
      />

      <div
        className={cn(
          "flex flex-col flex-1 h-full transition-all duration-300",
          sidebarOpen ? "md:ml-72" : "ml-0",
        )}
      >
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
                    isUser={msg.isUser}
                    image={msg.image}
                  />
                ))}
                {isTyping && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        <ChatInput
          onSend={handleSend}
          // disabled={isTyping || isStreaming || !activeSessionId}   ← remove !activeSessionId
          disabled={isTyping || isStreaming}
        />
      </div>
    </div>
  );
};

export default ChatContainer;
