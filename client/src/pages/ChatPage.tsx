import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ChatSidebar from '../components/ChatSidebar';
import ChatWindow from '../components/ChatWindow';

export default function ChatPage() {
    const navigate = useNavigate();
    const { id } = useParams(); // Use this as the source of truth for the ID

    const [activeTitle, setActiveTitle] = useState<string>("New Message");

    const [sidebarRefreshTrigger, setSidebarRefreshTrigger] = useState(0);

    // Keep state in sync with URL
    const activeChatId = id || null;

    const handleSelectConversation = (id: string, title: string) => {
    setActiveTitle(title || "Conversation");
    navigate(`/chat/${id}`);
    };

    const handleNewChat = (newId: string) => {
      setSidebarRefreshTrigger(prev => prev + 1); // This is the "poke"
      if (id !== newId) {
        navigate(`/chat/${newId}`);
      }
    };

    return (
    <div className="flex h-screen w-full bg-slate-950 overflow-hidden text-slate-200">
      {/* 1. Sidebar */}
      <ChatSidebar
        activeId={activeChatId}
        onSelect={handleSelectConversation}
        refreshTrigger={sidebarRefreshTrigger}
      />

      {/* 2. Main Chat Area */}
      <main className="flex-1 flex flex-col min-w-0 h-full">
        {/* Header */}
        <header className="h-16 border-b border-slate-800 flex items-center px-8 bg-slate-950/50 backdrop-blur">
          <h1 className="font-medium">
            {activeChatId ? `Conversation: ${activeTitle}` : 'New Message'}
          </h1>
        </header>

        {/* 3. Chat Window */}
        <div className="flex-1 relative overflow-hidden">
          <ChatWindow
            conversationId={activeChatId}
            onNewChatCreated={handleNewChat}
          />
        </div>
      </main>
    </div>
    );
}