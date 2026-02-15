import { useState } from "react";
import { MessageSquare, Plus, Trash2, PanelLeftClose } from "lucide-react";
import { Button } from "@/components/ui/button";
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
}

const ChatSidebar = ({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  isOpen,
  onToggle,
}: ChatSidebarProps) => {
  const [conversationToDelete, setConversationToDelete] = useState<number | null>(null);

  const handleDeleteClick = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    e.preventDefault();
    setConversationToDelete(id);
  };

  const handleConfirmDelete = () => {
    if (conversationToDelete !== null) {
      onDeleteConversation(conversationToDelete);
      setConversationToDelete(null);
    }
  };

  const handleCancelDelete = () => {
    setConversationToDelete(null);
  };

  const pendingTitle = conversationToDelete !== null
    ? conversations.find((c) => c.id === conversationToDelete)?.title || "this chat"
    : "";

  return (
    <>
      {/* Sidebar */}
      <div
        className={cn(
          "fixed left-0 top-0 h-full bg-sidebar-background border-r border-sidebar-border z-40 transition-all duration-300 ease-in-out flex flex-col",
          isOpen ? "w-72 translate-x-0" : "w-72 -translate-x-full md:hidden", // improved mobile behavior
        )}
      >
        {/* Header */}
        <div className="p-4 border-b border-sidebar-border flex items-center justify-between">
          <h2 className="text-lg font-semibold text-sidebar-foreground">Chats</h2>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={onNewConversation}
              className="text-sidebar-primary hover:bg-sidebar-accent"
              title="New conversation"
            >
              <Plus className="h-5 w-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={onToggle}
              className="text-muted-foreground hover:text-foreground hover:bg-sidebar-accent md:hidden"
              title="Close sidebar"
            >
              <PanelLeftClose className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* Conversations list */}
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {conversations.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground text-sm">
                No conversations yet
              </div>
            ) : (
              conversations.map((conversation) => {
                const isActive = activeConversationId === conversation.id;

                return (
                  <div
                    key={conversation.id}
                    className={cn(
                      "group relative flex items-center gap-3 px-3 py-3 rounded-lg cursor-pointer transition-all duration-200",
                      isActive
                        ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                        : "hover:bg-sidebar-accent/60 text-muted-foreground hover:text-sidebar-foreground"
                    )}
                    onClick={() => onSelectConversation(conversation.id)}
                  >
                    <MessageSquare className="h-4 w-4 flex-shrink-0 opacity-80" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {conversation.title || "New Chat"}
                      </p>
                      <p className="text-xs text-muted-foreground truncate mt-0.5">
                        {conversation.lastMessage || "No messages yet"}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className={cn(
                        "h-7 w-7 shrink-0 transition-opacity",
                        "opacity-60 hover:opacity-100 hover:text-destructive"
                      )}
                      onClick={(e) => handleDeleteClick(e, conversation.id)}
                      title="Delete conversation"
                    >
                      <Trash2 className="h-4 w-4 text-muted-foreground" />
                    </Button>
                  </div>
                );
              })
            )}
          </div>
        </ScrollArea>
      </div>

      <AlertDialog open={conversationToDelete !== null} onOpenChange={(open) => !open && handleCancelDelete()}>
        <AlertDialogContent onClick={(e) => e.stopPropagation()}>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete conversation?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete &quot;{pendingTitle}&quot; and all its messages. This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancelDelete}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-sm z-30 md:hidden"
          onClick={onToggle}
        />
      )}
    </>
  );
};

export default ChatSidebar;