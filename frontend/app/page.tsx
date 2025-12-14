"use client";

import { useEffect, useState } from 'react';
import { api, endpoints } from '@/lib/api';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { motion } from 'framer-motion';
import { Eye, Clock, ArrowRight, TrendingUp } from 'lucide-react';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import Navbar from '@/components/Navbar';

interface Project {
  id: string;
  title: string;
  abstract: string;
  created_at: string;
  user?: { name: string };
  topics: string[];
  views_count: number;
}

export default function Home() {
  const [feed, setFeed] = useState<Project[]>([]);
  const [trending, setTrending] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [feedRes, trendRes] = await Promise.all([
          api.get(endpoints.feed.main),
          api.get(endpoints.feed.trending)
        ]);
        setFeed(feedRes.data);
        setTrending(trendRes.data);
      } catch (error) {
        console.error("Feed error", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // --- HELPER FUNCTION TO CLEAN TOPICS ---
  const extractTopics = (topics: string[]) => {
    if (!topics || topics.length === 0) return [];
    
    // Detect "dirty" AI response (long text or contains markdown/sentences)
    const isDirty = topics.some(t => t.length > 50 || t.includes("**") || t.includes("Here are"));

    if (isDirty) {
        const rawText = topics.join(" ");
        // Regex 1: Extract bolded text **Topic**
        const boldMatches = rawText.match(/\*\*([^*]+)\*\*/g);
        if (boldMatches) {
            return boldMatches.map(t => t.replace(/\*\*/g, "").trim());
        }
        // Regex 2: Extract numbered lists 1. Topic
        const listMatches = rawText.match(/\d+\.\s*([^,.\n]+)/g);
        if (listMatches) {
             return listMatches.map(t => t.replace(/^\d+\.\s*/, "").trim());
        }
    }
    return topics;
  };

  return (
    <div className="min-h-screen bg-muted/20">
      <Navbar />
      <main className="container px-4 py-8 mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        <div className="lg:col-span-8 space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Latest Research</h1>
            <div className="text-sm text-muted-foreground">{feed.length} papers published</div>
          </div>
          
          {loading ? (
             <div className="grid gap-6">
               {[1,2,3].map(i => <Skeleton key={i} className="h-64 w-full rounded-xl" />)}
             </div>
          ) : (
            <div className="grid gap-6">
              {feed.map((project, index) => {
                
                // Clean the topics before rendering
                const cleanTopics = extractTopics(project.topics);

                return (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    key={project.id}
                  >
                    <Link href={`/project/${project.id}`}>
                      <Card className="group border-border/60 hover:border-primary/50 transition-all duration-300 hover:shadow-xl hover:shadow-primary/5 cursor-pointer overflow-hidden bg-card/50 backdrop-blur-sm">
                        <CardHeader className="flex flex-row items-start justify-between pb-3">
                          <div className="flex gap-4">
                            <Avatar className="h-12 w-12 border-2 border-background shadow-sm">
                              <AvatarFallback>{project.user?.name?.[0] || '?'}</AvatarFallback>
                            </Avatar>
                            <div>
                              <h3 className="font-semibold text-xl leading-tight group-hover:text-primary transition-colors">
                                {project.title}
                              </h3>
                              <p className="text-sm text-muted-foreground flex items-center gap-2 mt-1">
                                {project.user?.name || 'Unknown Author'} • 
                                <span className="text-xs bg-muted px-2 py-0.5 rounded-full">
                                  {formatDistanceToNow(new Date(project.created_at))} ago
                                </span>
                              </p>
                            </div>
                          </div>
                        </CardHeader>
                        
                        <CardContent>
                          <p className="text-muted-foreground line-clamp-2 text-sm leading-relaxed">
                            {project.abstract || "Processing abstract..."}
                          </p>
                          <div className="flex flex-wrap gap-2 mt-4">
                            {/* Use the cleaned topics here */}
                            {cleanTopics.slice(0, 3).map((topic, i) => (
                              <Badge key={i} variant="secondary" className="bg-primary/5 text-primary hover:bg-primary/10 border-transparent">
                                #{topic}
                              </Badge>
                            ))}
                          </div>
                        </CardContent>

                        <CardFooter className="border-t bg-muted/10 py-3 px-6 flex justify-between text-xs text-muted-foreground mt-2">
                          <div className="flex items-center gap-4">
                            <span className="flex items-center gap-1.5"><Eye className="h-3.5 w-3.5" /> {project.views_count} views</span>
                            <span className="flex items-center gap-1.5"><Clock className="h-3.5 w-3.5" /> 5 min read</span>
                          </div>
                          <div className="flex items-center gap-1 text-primary font-medium group-hover:translate-x-1 transition-transform">
                            Read Paper <ArrowRight className="h-3.5 w-3.5" />
                          </div>
                        </CardFooter>
                      </Card>
                    </Link>
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>

        <div className="lg:col-span-4 space-y-6">
          <div className="sticky top-24">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-foreground">
              <TrendingUp className="h-5 w-5 text-red-500" />
              Trending Now
            </h2>
            <Card className="bg-card/50 backdrop-blur-sm border-border/60 shadow-sm">
              <CardContent className="p-0">
                {trending.map((t, i) => (
                   <Link href={`/project/${t.id}`} key={t.id} className="block group border-b last:border-0">
                     <div className="flex items-start gap-4 p-4 hover:bg-muted/50 transition-colors">
                       <span className="text-2xl font-bold text-muted-foreground/20 group-hover:text-primary/20 transition-colors">0{i+1}</span>
                       <div>
                         <h4 className="font-medium text-sm line-clamp-2 group-hover:text-primary transition-colors leading-snug">
                           {t.title}
                         </h4>
                         <p className="text-xs text-muted-foreground mt-1.5 flex items-center gap-1">
                           <Eye className="h-3 w-3" /> {t.views_count} reads
                         </p>
                       </div>
                     </div>
                   </Link>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}