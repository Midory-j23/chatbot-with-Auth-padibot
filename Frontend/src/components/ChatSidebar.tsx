// ChatSidebar.tsx
import { useState, useMemo } from "react";
import {
  MessageSquare,
  Plus,
  Trash2,
  PanelLeftClose,
  Search,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { cn } from "@/lib/utils";

export interface Conversation {
  id: number;
  title: string;
  lastMessage: string;
  createdAt: Date;
}

interface ChatSidebarProps {
  conversations: Conversation[];
  activeConversationId: number | null;
  onSelectConversation: (id: number) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: number) => void;
  isOpen: boolean;
  onToggle: () => void;
  userEmail?: string; // ← only email passed from parent
}

const ChatSidebar = ({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  isOpen,
  onToggle,
  userEmail = "user@example.com",
}: ChatSidebarProps) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [conversationToDelete, setConversationToDelete] = useState<
    number | null
  >(null);

  const filteredConversations = useMemo(() => {
    if (!searchQuery.trim()) return conversations;
    const q = searchQuery.toLowerCase();
    return conversations.filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        (c.lastMessage || "").toLowerCase().includes(q),
    );
  }, [conversations, searchQuery]);

  const handleDeleteClick = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    setConversationToDelete(id);
  };

  const handleConfirmDelete = () => {
    if (conversationToDelete !== null) {
      onDeleteConversation(conversationToDelete);
      setConversationToDelete(null);
    }
  };

  const pendingTitle =
    conversations.find((c) => c.id === conversationToDelete)?.title ||
    "this chat";

  return (
    <>
      <div
        className={cn(
          "fixed left-0 top-0 h-full bg-sidebar border-r border-sidebar-border z-40 transition-all duration-300 flex flex-col text-sidebar-foreground",
          isOpen ? "w-72 translate-x-0" : "w-72 -translate-x-full md:hidden",
        )}
      >
        {/* Header - New Chat + mobile close */}
        <div className="p-3 border-b border-sidebar-border flex items-center justify-between">
          <Button
            variant="ghost"
            className="flex-1 justify-start gap-2 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground text-base font-medium"
            onClick={onNewConversation}
          >
            <Plus className="h-5 w-5" />
            New chat
          </Button>

          <Button
            variant="ghost"
            size="icon"
            className="md:hidden text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent"
            onClick={onToggle}
          >
            <PanelLeftClose className="h-5 w-5" />
          </Button>
        </div>

        {/* Search bar */}
        <div className="p-3 border-b border-sidebar-border">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-sidebar-foreground/50" />
            <Input
              placeholder="Search chats"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-background border-sidebar-border text-sidebar-foreground placeholder:text-sidebar-foreground/50 focus-visible:ring-sidebar-ring focus-visible:border-sidebar-border"
            />
          </div>
        </div>

        {/* Conversations list */}
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {filteredConversations.length === 0 ? (
              <div className="px-4 py-10 text-center text-sm text-sidebar-foreground/60">
                {searchQuery
                  ? "No matching chats found"
                  : "No conversations yet"}
              </div>
            ) : (
              filteredConversations.map((conv) => {
                const isActive = activeConversationId === conv.id;

                return (

                  <div
                    key={conv.id}
                    className={cn(
                      "group relative flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors duration-150",
                      isActive
                        ? "bg-sidebar-accent text-sidebar-accent-foreground"
                        : "hover:bg-sidebar-accent/80 text-sidebar-foreground",
                    )}
                    onClick={() => onSelectConversation(conv.id)}
                  >
                    <MessageSquare className="h-4 w-4 opacity-80 flex-shrink-0 mt-0.5" />

                    <div className="flex-1 min-w-0 space-y-0.5">
                      {" "}
                      {/* ← space-y instead of mt */}
                      {/* Title - allow wrapping or at least show much more */}
                      <p
                        className={cn(
                          "text-sm font-medium",
                          // Option A: allow 2 lines max + ellipsis only at the end
                          "line-clamp-2", // ← most popular fix right now
                          // Option B: completely remove truncation → text can wrap
                          // ""                    // ← no truncate / line-clamp at all
                        )}
                      >
                        {conv.title || "New Chat"}
                      </p>
                      {/* Last message preview - usually 1–2 lines max */}
                      <p
                        className={cn(
                          "text-xs text-sidebar-foreground/60",
                          "line-clamp-2", // ← 2 lines is usually enough for previews
                          // or "" to allow full wrapping (but can look messy)
                        )}
                      >
                        {conv.lastMessage || "No messages yet"}
                      </p>
                    </div>

                    {/* Delete button - keep it on the right */}
                    <Button
                      variant="ghost"
                      size="icon"
                      className={cn(
                        "h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity",
                        "text-sidebar-foreground/70 hover:text-destructive hover:bg-destructive/10",
                        // Important: make sure delete button doesn't push content out
                        "flex-shrink-0",
                      )}
                      onClick={(e) => handleDeleteClick(e, conv.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                );
              })
            )}
          </div>
        </ScrollArea>

        {/* Bottom - only email */}
        <div className="p-3 border-t border-sidebar-border mt-auto bg-sidebar">
          <div className="text-sm text-sidebar-foreground/70 truncate text-center md:text-left">
            {userEmail}
          </div>
        </div>
      </div>

      {/* Delete confirmation dialog */}
      <AlertDialog
        open={conversationToDelete !== null}
        onOpenChange={(open) => !open && setConversationToDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete chat?</AlertDialogTitle>
            <AlertDialogDescription>
              "{pendingTitle}" and all its messages will be permanently deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700 text-white"
              onClick={handleConfirmDelete}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 md:hidden"
          onClick={onToggle}
        />
      )}
    </>
  );
};

export default ChatSidebar;



// git config --global user.name "m.ghasemian"
// git config --global user.email "mghasemian@padisarco.com"
