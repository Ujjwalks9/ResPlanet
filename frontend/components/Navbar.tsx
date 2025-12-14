"use client";

import Link from 'next/link';
import { useAuth } from '@/store/authStore';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { Bell, PenTool, Search, LogOut } from 'lucide-react';
import { useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

function AuthHandler() {
  const { login } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const userId = searchParams.get('user_id');
    const name = searchParams.get('name');
    
    if (userId && name) {
      login({ id: userId, name: name });
      router.replace('/'); 
    }
  }, [searchParams, login, router]);

  return null;
}

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
      <Suspense fallback={null}>
        <AuthHandler />
      </Suspense>

      <div className="container flex h-16 items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 font-bold text-xl tracking-tighter hover:opacity-80 transition">
          <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center text-primary-foreground shadow-lg shadow-blue-500/20">R</div>
          ResPlanet
        </Link>

        <div className="hidden md:flex items-center bg-muted/40 px-4 py-2 rounded-full w-96 border border-transparent focus-within:border-primary/50 focus-within:bg-background transition-all">
          <Search className="h-4 w-4 text-muted-foreground mr-2" />
          <input 
            placeholder="Search research papers..." 
            className="bg-transparent border-none outline-none text-sm w-full placeholder:text-muted-foreground/70"
          />
        </div>

        <div className="flex items-center gap-4">
          {user ? (
            <>
              <Link href="/upload">
                <Button size="sm" className="hidden sm:flex shadow-md">
                  <PenTool className="h-4 w-4 mr-2" /> Publish
                </Button>
              </Link>
              
              <Link href="/collab">
                 <Button variant="ghost" size="icon" className="relative">
                   <Bell className="h-5 w-5" />
                 </Button>
              </Link>

              <DropdownMenu>
                <DropdownMenuTrigger className="focus:outline-none">
                  <Avatar className="h-9 w-9 border-2 border-primary/10 cursor-pointer hover:border-primary transition">
                    <AvatarImage src={user.picture} />
                    <AvatarFallback className="bg-primary/10 text-primary">{user.name[0]}</AvatarFallback>
                  </Avatar>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  <DropdownMenuItem onClick={logout} className="text-destructive focus:text-destructive cursor-pointer">
                    <LogOut className="h-4 w-4 mr-2" /> Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            <Button onClick={() => window.location.href = 'http://localhost:8000/auth/login/google'}>
              Sign In with Google
            </Button>
          )}
        </div>
      </div>
    </nav>
  );
}