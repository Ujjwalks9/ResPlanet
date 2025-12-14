"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api, endpoints } from '@/lib/api';
import { useAuth } from '@/store/authStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { MessageSquare, UserPlus, Sparkles, BookOpen, Lock, CheckCircle, Clock, RefreshCw, Bug } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { toast } from 'sonner';

export default function ProjectDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const router = useRouter();
  
  const [project, setProject] = useState<any>(null);
  const [aiReview, setAiReview] = useState<string | null>(null);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [collabStatus, setCollabStatus] = useState<string>('none');
  const [verifying, setVerifying] = useState(false);

  // --- STATUS CHECKER ---
  const checkStatus = (data: any, currentUser: any) => {
      if (!data || !currentUser) return;
      const currentUserId = String(currentUser.id);
      const ownerId = String(data.user?.id);

      if (ownerId === currentUserId) {
          setCollabStatus('owner');
          return;
      }

      const list = data.collab_requests || data.collaborators || data.requests || [];
      const myRecord = list.find((c: any) => {
          return (
              String(c.sender_id) === currentUserId || 
              String(c.user_id) === currentUserId ||   
              String(c.sender?.id) === currentUserId   
          );
      });

      if (myRecord) {
          const status = myRecord.status ? myRecord.status.toLowerCase() : 'accepted';
          setCollabStatus(status);
      } else {
          setCollabStatus('none');
      }
  };

  useEffect(() => {
    if (id) {
      setVerifying(true);
      api.get(endpoints.projects.details(id as string))
         .then(res => {
            setProject(res.data);
            if (user) checkStatus(res.data, user);
         })
         .catch(err => console.error(err))
         .finally(() => setVerifying(false));
    }
  }, [id, user]);

  useEffect(() => {
      if(project && user) checkStatus(project, user);
  }, [user]);

  const handleRefresh = async () => {
      if(!id) return;
      setVerifying(true);
      try {
          const res = await api.get(endpoints.projects.details(id as string));
          setProject(res.data);
          if(user) checkStatus(res.data, user);
          toast.success("Data Refreshed");
      } catch(e) {
          toast.error("Failed to refresh");
      } finally {
          setVerifying(false);
      }
  };

  const handleCollab = async () => {
    if (!user) return toast.error("Please login to collaborate");
    try {
      await api.post(endpoints.collab.request, null, {
        params: { project_id: id, sender_id: user.id }
      });
      setCollabStatus('pending'); 
      toast.success("Collaboration Request Sent!");
      handleRefresh(); 
    } catch (e) {
      toast.error("Failed to send request");
    }
  };

  const extractTopics = (topics: any[]) => {
    if (!topics || topics.length === 0) return [];
    const isDirty = topics.some(t => t.length > 50 || t.includes("**") || t.includes("Here are"));
    if (isDirty) {
        const rawText = topics.join(" ");
        const boldMatches = rawText.match(/\*\*([^*]+)\*\*/g);
        if (boldMatches) return boldMatches.map((t: string) => t.replace(/\*\*/g, "").trim());
        const listMatches = rawText.match(/\d+\.\s*([^,.\n]+)/g);
        if (listMatches) return listMatches.map((t: string) => t.replace(/^\d+\.\s*/, "").trim());
    }
    return topics;
  };
  
  const cleanAiReview = (text: string | null) => {
      if (!text) return null;
      return text.replace(/^[\s\S]*?(?:Here is|Here's|Sure,|Below is|I have generated).*?:\s*/i, "")
          .replace(/\*\*(.*?)\*\*/g, "$1").replace(/#{1,6}\s?/g, "").trim();
  };

  const handleReview = async () => {
    setReviewLoading(true);
    try {
      const res = await api.post(endpoints.projects.review(id as string));
      setAiReview(res.data.ai_review);
    } catch (e) { toast.error("Failed to generate review"); } 
    finally { setReviewLoading(false); }
  };

  const displayTopics = project ? extractTopics(project.topics) : [];
  const displayReview = cleanAiReview(aiReview);

  if (!project) return <Skeleton className="h-screen w-full" />;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar />
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden h-[calc(100vh-64px)]">
        <div className="flex-1 bg-muted/30 p-4 border-r relative flex flex-col">
          <div className="bg-card rounded-xl shadow-sm border h-full w-full overflow-hidden relative group">
             <iframe src={endpoints.projects.file(project.id)} className="w-full h-full object-cover" title="PDF Viewer" />
          </div>
        </div>

        <div className="w-full lg:w-[480px] bg-background flex flex-col border-l shadow-2xl shadow-black/5 z-10 overflow-hidden">
          <div className="flex-shrink-0 border-b bg-background p-6 space-y-4">
            <div>
              <div className="flex justify-between items-start">
                  <Badge variant="outline" className="mb-3 text-muted-foreground text-xs">Research Paper</Badge>
                  <Button variant="ghost" size="icon" onClick={handleRefresh} title="Force Refresh Data">
                      <RefreshCw className={`h-4 w-4 ${verifying ? 'animate-spin' : ''}`} />
                  </Button>
              </div>
              <h1 className="text-xl font-bold leading-tight tracking-tight text-foreground line-clamp-3">{project.title}</h1>
              <div className="flex items-center gap-3 mt-4 p-3 bg-muted/30 rounded-lg border text-sm">
                <Avatar className="h-8 w-8 flex-shrink-0">
                  <AvatarFallback className="text-xs">{project.user?.name?.[0]}</AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold truncate">{project.user?.name || "Unknown"}</p>
                  <p className="text-xs text-muted-foreground">Author</p>
                </div>
                {collabStatus === 'owner' ? (
                     <Badge variant="secondary" className="bg-blue-100 text-blue-700 h-8 px-3">Owner</Badge>
                ) : collabStatus === 'accepted' ? (
                     <Badge variant="secondary" className="bg-green-100 text-green-700 h-8 px-3">
                        <CheckCircle className="h-3 w-3 mr-1" /> Collaborator
                     </Badge>
                ) : collabStatus === 'pending' ? (
                     <Button disabled size="sm" variant="outline" className="h-8 bg-yellow-50 text-yellow-700 border-yellow-200">
                        <Clock className="h-3 w-3 mr-1" /> Pending
                     </Button>
                ) : (
                     <Button size="sm" onClick={handleCollab} className="bg-primary hover:bg-primary/90 text-primary-foreground flex-shrink-0 text-xs h-8">
                        <UserPlus className="h-3 w-3 mr-1" /> Collab
                     </Button>
                )}
              </div>
            </div>
          </div>

          <Tabs defaultValue="overview" className="flex-1 flex flex-col overflow-hidden">
            <TabsList className="w-full grid grid-cols-3 bg-muted/50 p-1 rounded-lg m-4 flex-shrink-0">
              <TabsTrigger value="overview" className="text-xs">Overview</TabsTrigger>
              <TabsTrigger value="ai" className="text-xs">AI Review</TabsTrigger>
              <TabsTrigger value="chat" className="text-xs">Discussion</TabsTrigger>
            </TabsList>

            <div className="flex-1 overflow-hidden">
              <TabsContent value="overview" className="flex-1 overflow-hidden m-0">
                <ScrollArea className="h-full w-full">
                  <div className="p-6 space-y-4">
                     <div className="space-y-2">
                      <h3 className="font-semibold text-xs flex items-center gap-2 text-foreground/80"><BookOpen className="h-3 w-3" /> Abstract</h3>
                      <p className="text-xs text-muted-foreground leading-relaxed">{project.abstract}</p>
                    </div>
                    <div className="space-y-2">
                      <h3 className="font-semibold text-xs text-foreground/80">Topics</h3>
                      <div className="flex flex-wrap gap-2">
                        {displayTopics.map((t: string, i: number) => <Badge key={i} variant="secondary" className="px-2 py-0.5 text-xs">#{t}</Badge>)}
                      </div>
                    </div>
                  </div>
                </ScrollArea>
              </TabsContent>

              <TabsContent value="ai" className="flex-1 overflow-hidden m-0">
                 <ScrollArea className="h-full w-full">
                  <div className="p-6">
                    {!displayReview ? (
                      <div className="text-center py-12 border-2 border-dashed rounded-lg bg-muted/10 space-y-3 h-full flex flex-col items-center justify-center">
                        <Sparkles className="h-6 w-6 text-purple-600" />
                        <Button onClick={handleReview} disabled={reviewLoading} className="bg-purple-600 text-white text-xs h-8">
                          {reviewLoading ? "Analyzing..." : "Generate Review"}
                        </Button>
                      </div>
                    ) : (
                      <div className="bg-muted/30 p-4 rounded-lg text-xs border whitespace-pre-wrap text-muted-foreground">{displayReview}</div>
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>

              <TabsContent value="chat" className="flex-1 overflow-hidden m-0 data-[state=active]:flex data-[state=active]:flex-col">
                <ScrollArea className="h-full w-full">
                  <div className="p-6 h-full flex items-center justify-center">
                    {(collabStatus === 'accepted' || collabStatus === 'owner') ? (
                        <div className="text-center space-y-4 w-full">
                            <div className="bg-green-100 dark:bg-green-900/30 w-16 h-16 rounded-full flex items-center justify-center mx-auto">
                                <MessageSquare className="h-8 w-8 text-green-600 dark:text-green-400" />
                            </div>
                            <div>
                                <h3 className="font-bold text-lg">Research Room Unlocked</h3>
                                <p className="text-xs text-muted-foreground mt-1 mb-4">You have access to the real-time discussion.</p>
                                {/* 👇 THIS IS THE FIX: URL CHANGED TO /chat/${id} */}
                                <Button onClick={() => router.push(`/chat/${id}`)} className="w-full bg-primary hover:bg-primary/90 shadow-lg">
                                    Enter Chat Room
                                </Button>
                            </div>
                        </div>
                    ) : (
                        <div className="text-center space-y-3 w-full">
                            <div className="bg-muted w-16 h-16 rounded-full flex items-center justify-center mx-auto">
                                <Lock className="h-8 w-8 text-muted-foreground/50" />
                            </div>
                            <div>
                                <h3 className="font-medium text-sm text-foreground">
                                    {collabStatus === 'pending' ? "Request Pending" : "Collaboration Required"}
                                </h3>
                                <p className="text-xs text-muted-foreground mt-1 px-6">
                                    {collabStatus === 'pending' 
                                        ? "Waiting for author approval..."
                                        : "Connect with the author to unlock the research chat room."}
                                </p>
                            </div>
                        </div>
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>
            </div>
          </Tabs>
        </div>
      </div>
    </div>
  );
}