"use client";

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/store/authStore';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Bot, User, Lock, Loader2, AlertCircle, ArrowLeft } from 'lucide-react';
import { cn } from '@/lib/utils';
import Navbar from '@/components/Navbar';
import { toast } from 'sonner';

const getWsUrl = (projectId: string, userId: string) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//localhost:8000/ws/chat/${projectId}/${userId}`;
};

export default function ChatRoom() {
  const params = useParams(); 
  const projectId = params?.projectId as string; 
  
  const { user } = useAuth();
  const router = useRouter();

  const [messages, setMessages] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const ws = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!user || !projectId) return;
    
    const wsUrl = getWsUrl(projectId, user.id);
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => toast.success("Connected to chat room");
    
    ws.current.onmessage = (event) => setMessages(prev => [...prev, event.data]);

    ws.current.onerror = (error) => {
        console.error("WebSocket Error:", error);
        toast.error("Connection failed.");
    };

    return () => ws.current?.close();
  }, [projectId, user]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = () => {
    if (!input.trim() || !ws.current) return;
    if (ws.current.readyState !== WebSocket.OPEN) {
        toast.error("Connection lost. Refreshing...");
        return;
    }
    ws.current.send(input);
    setInput("");
  };

  // --- NEW: Helper to render formatting (Bold & Newlines) ---
  const renderMessageContent = (text: string) => {
    // 1. Split by new lines first to preserve structure
    return text.split('\n').map((line, i) => {
        // 2. Detect empty lines for spacing
        if (line.trim() === "") return <div key={i} className="h-2" />;

        // 3. Process Bold Markers (**text**) inside each line
        const parts = line.split(/(\*\*.*?\*\*)/g);
        
        return (
            <div key={i} className="min-h-[1.5em]">
                {parts.map((part, j) => {
                    if (part.startsWith('**') && part.endsWith('**')) {
                        // Render bold text without the ** markers
                        return <strong key={j} className="font-bold text-foreground/90">{part.slice(2, -2)}</strong>;
                    }
                    // Render normal text
                    return <span key={j}>{part}</span>;
                })}
            </div>
        );
    });
  };

  if (!user) return <Loader2 className="h-8 w-8 animate-spin mx-auto mt-10" />;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar />
      <div className="container max-w-4xl mx-auto py-6 flex-1 flex flex-col h-[calc(100vh-64px)]">
        
        <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
                <Button variant="ghost" size="icon" onClick={() => router.back()}>
                    <ArrowLeft className="h-5 w-5" />
                </Button>
                <div>
                    <h1 className="text-xl font-bold">Research Discussion</h1>
                    <p className="text-xs text-muted-foreground font-mono">Room ID: {projectId?.slice(0, 8)}...</p>
                </div>
            </div>
            <div className="bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 px-3 py-1 rounded-full text-xs font-medium flex items-center gap-2">
                <Bot className="h-3 w-3" /> Gemini AI Active
            </div>
        </div>

        <div className="flex-1 bg-card border rounded-2xl shadow-sm overflow-hidden flex flex-col relative">
          <ScrollArea className="flex-1 p-6">
            <div className="space-y-6">
              {messages.length === 0 && (
                  <div className="text-center text-muted-foreground/50 py-20 flex flex-col items-center gap-3">
                      <AlertCircle className="h-10 w-10 opacity-20" />
                      <p>No messages yet.</p>
                  </div>
              )}
              
              {messages.map((msg, i) => {
                const isMe = msg.startsWith(`User ${user.id}`); 
                const isAi = msg.includes("🤖 AI") || msg.includes("Gemini");
                
                // Clean content prefix
                let rawContent = msg;
                if(msg.includes(": ")) rawContent = msg.split(": ").slice(1).join(": ");

                return (
                  <div key={i} className={cn("flex w-full animate-in slide-in-from-bottom-2", isMe ? "justify-end" : "justify-start")}>
                    <div className={cn("flex gap-3 max-w-[85%]", isMe ? "flex-row-reverse" : "flex-row")}>
                        <div className={cn(
                            "w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1 shadow-sm", 
                            isAi ? "bg-purple-100 text-purple-600" : isMe ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                        )}>
                            {isAi ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
                        </div>
                        <div className={cn(
                            "p-3.5 rounded-2xl text-sm shadow-sm leading-relaxed", 
                            isMe ? "bg-primary text-primary-foreground rounded-tr-none" : "bg-muted/50 border rounded-tl-none", 
                            isAi && "bg-purple-50 dark:bg-purple-900/10 border-purple-100 dark:border-purple-900/50 text-foreground"
                        )}>
                          {/* Use Helper Function to Render Content */}
                          {renderMessageContent(rawContent)}
                        </div>
                    </div>
                  </div>
                );
              })}
              <div ref={scrollRef} />
            </div>
          </ScrollArea>

          <div className="p-4 bg-muted/20 border-t flex gap-3 items-center">
            <Input 
              value={input} 
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Type a message..." 
              className="h-12 rounded-xl bg-background shadow-sm"
            />
            <Button onClick={sendMessage} className="h-12 w-12 rounded-xl shadow-md">
              <Send className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}