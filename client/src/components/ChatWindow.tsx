import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';
import { useError } from '../context/ErrorContext';

// define the shape of a message for the UI

interface Message {
    role: 'user' | 'assistant';
    content: string;
    files?: string[];
}

interface ChatWindowProps {
    conversationId: string | null;
    onNewChatCreated: (id: string) => void;
}

export default function ChatWindow({ conversationId, onNewChatCreated }: ChatWindowProps ) {
    const [ messages , setMessages ] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isSending, setIsSending] = useState(false);

    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const { showError } = useError();
    const scrollRef = useRef<HTMLDivElement>(null);

    const [isThinking, setIsThinking] = useState(false);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            // Convert FileList to Array and add to existing selection
            const newFiles = Array.from(e.target.files);
            setSelectedFiles(prev => [...prev, ...newFiles]);
        }
    };

    // 1. Autoscroll to bottom whenever messages update

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    // 2. Load history when conversationId changes

    useEffect(() => {
        const fetchHistory = async () => {
            if (!conversationId) {
                setMessages([]);
                return;
            }
            try {
                // result is the SuccessResponse { data: [...], message: null }
                const result = await api.get<any>(`/chat/conversations/${conversationId}`);

                // Access result.data to get the actual array of messages
                if (result && result.data && Array.isArray(result.data)) {
                    const history = result.data.flatMap((m: any) => [
                        { role: 'user', content: m.user_message },
                        { role: 'assistant', content: m.llm_response }
                    ]);
                    setMessages(history);
                }
            } catch (err: any) {
                showError("Could not load messages: " + err.message);
            }
        };
        fetchHistory();
    }, [conversationId, showError]);

    // 3. send message logic

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() && selectedFiles.length === 0) return;

        const messageText = input;
        const fileNames = selectedFiles.map(f => f.name); // 1. Capture names here

        // 2. Add user message to UI immediately with file names
        setMessages(prev => [...prev, {
            role: 'user',
            content: messageText,
            files: fileNames // 3. Store them here
        }]);

        const filesToUpload = [...selectedFiles];
        setInput('');
        setSelectedFiles([]); // Tray is now safe to clear
        setIsSending(true);
        setIsThinking(true);

        try {
            // 3. Construct FormData
            const formData = new FormData();
            formData.append('message', messageText);


            if (conversationId) {
                formData.append('conversation_id', conversationId);
            }

            // Append each file to the 'files' key (matches backend List[UploadFile])
            filesToUpload.forEach((file) => {
                formData.append('files', file);
            });

            // 4. API Call
            // Note: Ensure your api utility doesn't force 'Content-Type: application/json'
            const result = await api.post<any>('/chat/chat', formData);

            if (result.data?.answer) {
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: result.data.answer
                }]);

                if (!conversationId && result.data.conversation_id) {
                    onNewChatCreated(result.data.conversation_id);
                }
            }
        } catch (err: any) {
            showError("Failed to send message: " + err.message);
        } finally {
            setIsSending(false);
            setIsThinking(false);
        }
    };

return (
    <div className="flex flex-col h-full bg-slate-950">
        {/* 1. MESSAGES AREA */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
            {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] p-3 rounded-2xl flex flex-col gap-2 ${
                        m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-100'
                    }`}>

                        {/* --- FILE ATTACHMENTS (User Only) --- */}
                        {m.role === 'user' && m.files && m.files.length > 0 && (
                            <div className="flex flex-wrap gap-2 mb-1">
                                {m.files.map((fileName, idx) => (
                                    <div
                                        key={idx}
                                        className="flex items-center gap-1.5 bg-white/10 border border-white/20 px-2 py-1 rounded-md text-[10px] text-blue-50"
                                    >
                                        <span className="text-xs">📄</span>
                                        <span className="truncate max-w-[150px] font-medium">{fileName}</span>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* --- MESSAGE CONTENT --- */}
                        <div className="text-sm leading-relaxed whitespace-pre-wrap">
                            {m.content}
                        </div>
                    </div>
                </div>
            ))}

            {/* --- THINKING INDICATOR --- */}
            {isThinking && (
                <div className="flex justify-start animate-in fade-in slide-in-from-bottom-2 duration-300">
                    <div className="bg-slate-800/50 border border-slate-800 p-3 rounded-2xl flex items-center gap-3">
                        <div className="flex gap-1">
                            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce"></span>
                        </div>
                        <span className="text-xs text-slate-500 font-medium tracking-tight">Synapse is thinking...</span>
                    </div>
                </div>
            )}
        </div>

        {/* 2. INPUT AREA */}
        <div className="p-4 border-t border-slate-800">
            <div className="max-w-4xl mx-auto flex flex-col bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">

                {/* --- FILE PREVIEW TRAY --- */}
                {selectedFiles.length > 0 && (
                    <div className="flex gap-2 p-3 bg-slate-900/50 border-b border-slate-800 overflow-x-auto">
                        {selectedFiles.map((file, i) => (
                            <div key={i} className="flex items-center gap-2 bg-slate-800 px-3 py-1 rounded-full text-xs text-slate-200 whitespace-nowrap">
                                <span className="truncate max-w-[100px]">{file.name}</span>
                                <button
                                    type="button"
                                    onClick={() => removeFile(i)}
                                    className="text-slate-400 hover:text-red-400 font-bold"
                                >
                                    ✕
                                </button>
                            </div>
                        ))}
                    </div>
                )}

                <form onSubmit={handleSend} className="flex items-center p-2 gap-2">
                    {/* --- HIDDEN FILE INPUT --- */}
                    <input
                        type="file"
                        multiple
                        ref={fileInputRef}
                        onChange={handleFileChange}
                        className="hidden"
                    />

                    {/* --- ATTACH BUTTON --- */}
                    <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="p-2 text-slate-400 hover:text-blue-400 transition-colors"
                        title="Attach files"
                    >
                        📎
                    </button>

                    <input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder={isSending ? "Synapse is thinking..." : "Type a message or attach files..."}
                        className="flex-1 bg-transparent border-none focus:ring-0 text-slate-100 p-2 text-sm"
                        disabled={isSending}
                    />

                    <button
                        type="submit"
                        disabled={isSending || (!input.trim() && selectedFiles.length === 0)}
                        className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all"
                    >
                        {isSending ? "..." : "Send"}
                    </button>
                </form>
            </div>
        </div>
    </div>
);
}