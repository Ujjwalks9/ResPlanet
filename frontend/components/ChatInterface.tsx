"use client";

import { useEffect, useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Send, Bot, User } from "lucide-react";
import { useAuth } from "@/store/authStore";

interface Message {
  sender: string;
  content: string;
  isAi?: boolean;
}

interface ChatInterfaceProps {
  projectId: string;
}

export default function ChatInterface({ projectId }: ChatInterfaceProps) {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const ws = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  useEffect(() => {
    if (!user) return;
    const socket = new WebSocket(`ws://localhost:8000/ws/chat/${projectId}/${user.id}`);

    socket.onopen = () => console.log("Connected to Chat");
    
    socket.onmessage = (event) => {
      const text = event.data;
      let isAi = false;
      let sender = "Unknown";
      let content = text;

      if (text.includes("🤖 AI:")) {
        isAi = true;
        sender = "AI";
        content = text.replace("🤖 AI:", "").trim();
      } else if (text.includes(":")) {
        const parts = text.split(":");
        sender = parts[0].replace("User ", "").trim();
        content = parts.slice(1).join(":").trim();
      }
      setMessages((prev) => [...prev, { sender, content, isAi }]);
    };

    ws.current = socket;
    return () => socket.close();
  }, [projectId, user]);

  const sendMessage = () => {
    if (!input.trim() || !ws.current) return;
    ws.current.send(input);
    setInput("");
  };

  return (
    <div className="flex flex-col h-full border rounded-xl overflow-hidden bg-background">
      <div className="p-2 border-b bg-muted/50 text-[10px] text-center text-muted-foreground">
        Type <span className="font-bold">@bot</span> to ask AI
      </div>
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-3">
          {messages.map((msg, i) => {
            const isMe = msg.sender === user?.id;
            return (
              <div key={i} className={`flex gap-2 ${isMe ? "flex-row-reverse" : "flex-row"}`}>
                <Avatar className="h-6 w-6">
                  <AvatarFallback className={msg.isAi ? "bg-purple-100 text-purple-600" : ""}>
                    {msg.isAi ? <Bot className="h-3 w-3" /> : <User className="h-3 w-3" />}
                  </AvatarFallback>
                </Avatar>
                <div className={`p-2 rounded-lg text-sm max-w-[80%] ${msg.isAi ? "bg-purple-50 border border-purple-100 text-purple-900" : isMe ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                  <p>{msg.content}</p>
                </div>
              </div>
            );
          })}
          <div ref={scrollRef} />
        </div>
      </ScrollArea>
      <div className="p-2 border-t flex gap-2">
        <Input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && sendMessage()} placeholder="Message..." />
        <Button onClick={sendMessage} size="icon"><Send className="h-4 w-4" /></Button>
      </div>
    </div>
  );
}