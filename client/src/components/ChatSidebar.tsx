import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useError } from '../context/ErrorContext';

interface Conversation {
    conversation_id: string;
    title: string;
    created_at: string;
}

interface ChatSidebarProps {
    activeId: string | null;
    onSelect: (id: string, title:string) => void;
    refreshTrigger: number;
}

export default function ChatSidebar({ activeId, onSelect,refreshTrigger }: ChatSidebarProps) {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const { showError } = useError();

    // 1. fetch conversations from the backend
    const fetchConversations = async () => {
        console.log("DEBUG: fetchConversations called"); // See if this prints
        setIsLoading(true);
        try {
            const response = await api.get<{ data: Conversation[] }>('/chat/conversations');
            console.log("DEBUG: Backend response received:", response);
            setConversations(response.data);
        } catch (err: any) {
            console.error("DEBUG: Fetch error:", err);
        } finally {
            setIsLoading(false);
        }
    };
    //load on mount

    useEffect(() => {
        fetchConversations();
    }, [refreshTrigger]);

    return (
        <aside className="w-64 flex-shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col h-full">
            {/* New Chat Button */}
            <div className="p-4">
                <button
                    onClick={() => onSelect('')} // Passing empty string or null starts fresh
                    className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold transition flex items-center justify-center gap-2"
                >
                    <span className="text-xl">+</span> New Chat
                </button>
            </div>

            {/* Conversation List */}
            <div className="flex-1 overflow-y-auto custom-scrollbar">
                {isLoading && (
                    <div className="p-4 text-slate-500 text-sm animate-pulse">Loading history...</div>
                )}

                {!isLoading && conversations.length === 0 && (
                    <div className="p-4 text-slate-500 text-sm italic">No conversations yet</div>
                )}

                {conversations.map((chat) => (
                    <button
                        key={chat.conversation_id}
                        onClick={() => onSelect(chat.conversation_id, chat.title)}
                        className={`w-full text-left p-3 text-sm transition-colors border-b border-slate-800/50 ${
                            activeId === chat.conversation_id
                                ? 'bg-slate-800 text-blue-400 border-l-4 border-l-blue-500'
                                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                        }`}
                    >
                        <div className="truncate font-medium">{chat.title || 'Untitled Chat'}</div>
                        <div className="text-[10px] text-slate-600 mt-1">
                            {new Date(chat.created_at).toLocaleDateString()}
                        </div>
                    </button>
                ))}
            </div>

            {/* User Profile / Settings (Optional placeholder) */}
            <div className="p-4 border-t border-slate-800 text-slate-500 text-xs">
                Synapse v1.0
            </div>
        </aside>
    );
}