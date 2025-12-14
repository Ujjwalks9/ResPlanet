"use client";

import { useState } from 'react';
import { api, endpoints } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { UploadCloud, FileText, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import Navbar from '@/components/Navbar';
import { toast } from 'sonner';
import { useAuth } from '@/store/authStore';

export default function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const router = useRouter();
  const { user } = useAuth();

  const handleUpload = async () => {
    if (!file || !user?.id) {
      toast.error("Please log in and select a file");
      return;
    }
    
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', user.id);

    try {
      const res = await api.post(endpoints.projects.upload, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      toast.success("File uploaded successfully!");
      setFile(null);
      router.push(`/project/${res.data.id}`);
    } catch (error: any) {
      console.error(error);
      const errorMsg = error.response?.data?.detail || "Upload failed";
      toast.error(errorMsg);
      setLoading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles?.[0]) {
      const droppedFile = droppedFiles[0];
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile);
      } else {
        toast.error("Please drop a PDF file");
      }
    }
  };

  return (
    <div className="min-h-screen bg-muted/20">
      <Navbar />
      <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
        <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
          <Card className="w-full max-w-md p-8 text-center space-y-6 shadow-2xl border-primary/20">
            <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
              {loading ? (
                <Loader2 className="h-8 w-8 text-primary animate-spin" />
              ) : (
                <UploadCloud className="h-8 w-8 text-primary" />
              )}
            </div>
            
            <div>
              <h1 className="text-2xl font-bold">Publish Research</h1>
              <p className="text-muted-foreground mt-2">Upload your PDF thesis or paper to the network.</p>
            </div>

            <div 
              className={`border-2 border-dashed rounded-xl p-8 transition-colors ${
                dragActive 
                  ? 'border-primary bg-primary/10' 
                  : 'border-input hover:bg-muted/50'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
               <Input 
                  type="file" 
                  accept=".pdf" 
                  className="hidden" 
                  id="file-upload"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
               />
               <label htmlFor="file-upload" className="cursor-pointer block">
                 {file ? (
                   <div className="flex items-center justify-center gap-2 text-green-600 font-medium">
                     <FileText className="h-5 w-5" /> {file.name}
                   </div>
                 ) : (
                   <span className="text-sm text-muted-foreground">Click to browse or drag PDF here</span>
                 )}
               </label>
            </div>

            <Button 
              className="w-full h-11 text-base shadow-lg" 
              onClick={handleUpload}
              disabled={!file || loading}
            >
              {loading ? "Processing Paper..." : "Upload & Analyze"}
            </Button>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}