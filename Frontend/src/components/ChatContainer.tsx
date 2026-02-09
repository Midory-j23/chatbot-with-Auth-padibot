import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { User, Session } from "@supabase/supabase-js";
import ChatHeader from "./ChatHeader";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import TypingIndicator from "./TypingIndicator";
import WelcomeState from "./WelcomeState";
import ChatSidebar, { Conversation } from "./ChatSidebar";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  isNew?: boolean;
  image?: string;
}

interface ConversationData {
  id: string;
  messages: Message[];
  title: string;
  lastMessage: string;
  createdAt: Date;
}

const ChatContainer = () => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const [conversations, setConversations] = useState<ConversationData[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<
    string | null
  >(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
      if (!session?.user) {
        navigate("/auth");
      }
    });

    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
      if (!session?.user) {
        navigate("/auth");
      }
    });

    return () => subscription.unsubscribe();
  }, [navigate]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, isStreaming]);

  const handleStopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setIsTyping(false);
  };

  const streamFromServer = async (
    response: Response,
    messageId: string,
    conversationId: string
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
        fullContent += chunk;

        setMessages((prev) =>
          prev.map((m) =>
            m.id === messageId ? { ...m, content: fullContent } : m
          )
        );
      }
    } catch (error) {
      if ((error as Error).name === "AbortError") {
        console.log("Stream cancelled by user");
      } else {
        throw error;
      }
    } finally {
      setIsStreaming(false);
      const finalMessage: Message = {
        id: messageId,
        content: fullContent || "پاسخ متوقف شد.",
        isUser: false,
        isNew: true,
      };

      setMessages((prev) =>
        prev.map((m) => (m.id === messageId ? finalMessage : m))
      );

      // Update conversation with AI response
      setConversations((prev) =>
        prev.map((c) =>
          c.id === conversationId
            ? {
                ...c,
                messages: [
                  ...c.messages.filter((m) => m.id !== messageId),
                  finalMessage,
                ],
              }
            : c
        )
      );
    }
  };

  const handleSend = async (message: string, image?: string) => {
    if (!message.trim() && !image) return;

    // Create new conversation if none active
    let currentConversationId = activeConversationId;
    if (!currentConversationId) {
      const newConversation: ConversationData = {
        id: `conv-${Date.now()}`,
        messages: [],
        title: message.slice(0, 30) + (message.length > 30 ? "..." : ""),
        lastMessage: message,
        createdAt: new Date(),
      };
      setConversations((prev) => [newConversation, ...prev]);
      setActiveConversationId(newConversation.id);
      currentConversationId = newConversation.id;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      content: message,
      isUser: true,
      image,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    // Update conversation's last message
    setConversations((prev) =>
      prev.map((c) =>
        c.id === currentConversationId
          ? {
              ...c,
              lastMessage: message,
              messages: [...c.messages, userMessage],
            }
          : c
      )
    );

    try {
      // Create abort controller for cancellation
      abortControllerRef.current = new AbortController();

      // Get conversation history for context (including images)
      const currentConversation = conversations.find(
        (c) => c.id === currentConversationId
      );
      const history =
        currentConversation?.messages.map((m) => ({
          role: m.isUser ? "user" : "assistant",
          content: m.content,
          image: m.image, // Include image in history
        })) || [];

      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          history,
          image,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) throw new Error("Network error");

      const aiMessageId = `ai-${Date.now()}`;

      setIsTyping(false);

      const aiMessage: Message = {
        id: aiMessageId,
        content: "",
        isUser: false,
        isNew: false,
      };

      setMessages((prev) => [...prev, aiMessage]);

      await streamFromServer(response, aiMessageId, currentConversationId);
    } catch (error) {
      console.error("AI Error:", error);
      setIsTyping(false);
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        content: "خطا در ارتباط با سرور یا Ollama.",
        isUser: false,
      };
      setMessages((prev) => [...prev, errorMessage]);

      setConversations((prev) =>
        prev.map((c) =>
          c.id === currentConversationId
            ? { ...c, messages: [...c.messages, errorMessage] }
            : c
        )
      );
    }
  };

  const handleClearChat = () => {
    if (activeConversationId) {
      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConversationId ? { ...c, messages: [] } : c
        )
      );
    }
    setMessages([]);
    setIsTyping(false);
    setIsStreaming(false);
  };

  const handleNewConversation = () => {
    setActiveConversationId(null);
    setMessages([]);
    setIsTyping(false);
    setIsStreaming(false);
  };

  const handleSelectConversation = (id: string) => {
    const conversation = conversations.find((c) => c.id === id);
    if (conversation) {
      setActiveConversationId(id);
      setMessages(conversation.messages);
    }
  };

  const handleDeleteConversation = (id: string) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeConversationId === id) {
      setActiveConversationId(null);
      setMessages([]);
    }
  };

  const sidebarConversations: Conversation[] = conversations.map((c) => ({
    id: c.id,
    title: c.title,
    lastMessage: c.lastMessage,
    createdAt: c.createdAt,
  }));

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex h-screen max-h-screen bg-background">
      <ChatSidebar
        conversations={sidebarConversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
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
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    message={message.content}
                    isUser={message.isUser}
                    isNew={message.isNew}
                    image={message.image}
                  />
                ))}
                {isTyping && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        <ChatInput onSend={handleSend} disabled={isTyping || isStreaming} />
      </div>
    </div>
  );
};

export default ChatContainer;
