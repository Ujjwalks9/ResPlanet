"use client";

import { useEffect, useState } from 'react';
import { api, endpoints } from '@/lib/api';
import { useAuth } from '@/store/authStore';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Check, X } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { toast } from 'sonner';

export default function CollabDashboard() {
  const { user } = useAuth();
  const [requests, setRequests] = useState([]);

  useEffect(() => {
    if (user) {
      api.get(endpoints.collab.myRequests(user.id))
         .then(res => setRequests(res.data));
    }
  }, [user]);

  const handleAction = async (id: string, status: string) => {
    try {
        await api.put(endpoints.collab.update(id, status));
        toast.success(`Request ${status.toLowerCase()}`);
        // Refresh requests
        const res = await api.get(endpoints.collab.myRequests(user!.id));
        setRequests(res.data);
    } catch (e) {
        toast.error("Failed to update status");
    }
  };

  return (
    <div className="min-h-screen bg-muted/20">
      <Navbar />
      <div className="container max-w-2xl mx-auto py-10 px-4">
        <h1 className="text-2xl font-bold mb-6">Collaboration Requests</h1>
        <div className="space-y-4">
          {requests.map((req: any) => (
            <Card key={req.id}>
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="font-semibold">{req.sender?.name} <span className="text-muted-foreground font-normal">wants to join</span></p>
                  <p className="text-sm text-primary font-medium">{req.project?.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">Status: {req.status}</p>
                </div>
                {req.status === 'PENDING' && (
                  <div className="flex gap-2">
                    <Button size="sm" className="bg-green-600 hover:bg-green-700" onClick={() => handleAction(req.id, 'ACCEPTED')}>
                      <Check className="h-4 w-4" />
                    </Button>
                    <Button size="sm" variant="destructive" onClick={() => handleAction(req.id, 'REJECTED')}>
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                )}
                {req.status === 'ACCEPTED' && (
                    <Button variant="outline" size="sm" onClick={() => window.location.href=`/chat/${req.project.id}`}>
                        Open Chat
                    </Button>
                )}
              </CardContent>
            </Card>
          ))}
          {requests.length === 0 && (
              <div className="text-center text-muted-foreground p-10">No pending requests.</div>
          )}
        </div>
      </div>
    </div>
  );
}