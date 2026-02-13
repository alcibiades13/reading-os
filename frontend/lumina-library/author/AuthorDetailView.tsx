
import React, { useState, useEffect } from 'react';
import { Author, GoogleBook } from '../types';
import { getAuthorDetails, getBooksByAuthor } from '../services/authorService';
import { BookCard } from '../components/BookCard';
import { SkeletonCard } from '../components/SkeletonLoader';
import { 
  ArrowLeft, Globe, Star, Users, BookOpen, 
  Sparkles, Heart, Share2, Quote, ExternalLink,
  MapPin, Calendar, Twitter, Linkedin, Github,
  ChevronRight
} from 'lucide-react';

interface AuthorDetailViewProps {
  authorName: string;
  onBack: () => void;
  onOpenBook: (book: GoogleBook) => void;
  onOpenAuthor: (name: string) => void;
}

export const AuthorDetailView: React.FC<AuthorDetailViewProps> = ({ 
  authorName, onBack, onOpenBook, onOpenAuthor 
}) => {
  const [author, setAuthor] = useState<Author | null>(null);
  const [books, setBooks] = useState<GoogleBook[]>([]);
  const [loading, setLoading] = useState(true);
  const [isFollowing, setIsFollowing] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [details, bibliography] = await Promise.all([
          getAuthorDetails(authorName),
          getBooksByAuthor(authorName)
        ]);
        setAuthor(details);
        setBooks(bibliography);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    window.scrollTo(0, 0);
  }, [authorName]);

  if (loading || !author) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-20 flex flex-col items-center justify-center">
        <div className="w-12 h-12 border-4 border-slate-800 border-t-indigo-500 rounded-full animate-spin mb-4" />
        <p className="text-slate-500 font-black uppercase tracking-widest text-[9px]">Fetching Chronicles...</p>
      </div>
    );
  }

  return (
    <div className="animate-in fade-in duration-1000 bg-[#02040a]">
      {/* 1. COMPACT HERO SECTION */}
      <section className="relative min-h-[45vh] flex flex-col justify-end p-8 lg:p-16 overflow-hidden border-b border-white/5">
        <div className="absolute inset-0 opacity-10 pointer-events-none">
           <div className="absolute top-[-10%] left-[-5%] w-[40%] h-[40%] bg-indigo-500/15 blur-[120px] rounded-full" />
        </div>

        <button 
          onClick={onBack}
          className="absolute top-8 left-8 z-50 flex items-center gap-2 text-slate-500 hover:text-white transition-all font-black text-[9px] uppercase tracking-widest group"
        >
          <ArrowLeft size={14} className="group-hover:-translate-x-1 transition-transform" />
          Library
        </button>

        <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-10 items-end">
          <div className="lg:col-span-9 space-y-6">
             <div className="flex flex-wrap gap-2">
                {author.tags.map(tag => (
                  <span key={tag} className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[8px] font-black text-indigo-400 uppercase tracking-widest">
                    {tag}
                  </span>
                ))}
             </div>
             <h1 className="text-5xl lg:text-7xl font-black text-white tracking-tighter leading-tight">
                {author.name}
             </h1>
             
             <div className="flex flex-wrap items-center gap-8">
                <AuthorStat label="Volumes" value={books.length.toString()} />
                <AuthorStat label="Reach" value="Global" />
                
                <div className="h-8 w-px bg-white/10 mx-1 hidden lg:block" />

                <div className="flex items-center gap-3">
                   <button 
                     onClick={() => setIsFollowing(!isFollowing)}
                     className={`px-6 py-3 rounded-xl font-black text-[9px] uppercase tracking-widest transition-all ${
                       isFollowing ? 'bg-white/10 text-white border border-white/20' : 'bg-indigo-500 text-white shadow-xl shadow-indigo-500/20 hover:scale-105'
                     }`}
                   >
                     {isFollowing ? 'Following' : 'Follow Author'}
                   </button>
                   <button className="p-3 rounded-xl bg-white/5 text-slate-400 hover:text-white transition-all border border-white/5"><Share2 size={16}/></button>
                </div>
             </div>
          </div>

          <div className="lg:col-span-3 flex justify-end">
             <div className="relative w-48 h-60 lg:w-56 lg:h-72 rounded-[2rem] overflow-hidden shadow-2xl ring-1 ring-white/10 group">
                <img src={author.portraitUrl} alt={author.name} className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-1000" />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 to-transparent" />
             </div>
          </div>
        </div>
      </section>

      {/* 2. BIOGRAPHY & SIDEBAR */}
      <section className="p-8 lg:p-16 grid grid-cols-1 lg:grid-cols-12 gap-16">
        <div className="lg:col-span-8 space-y-10">
           <div className="flex items-center gap-4">
              <div className="w-8 h-px bg-indigo-500" />
              <h2 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.4em]">The Profile</h2>
           </div>
           
           <div className="space-y-8">
              <p className="text-2xl lg:text-3xl font-serif italic text-slate-300 leading-relaxed max-w-4xl">
                 {author.biography}
              </p>
              <div className="flex gap-4 pt-4">
                 <SocialIcon icon={<Twitter size={18}/>} />
                 <SocialIcon icon={<Linkedin size={18}/>} />
                 <SocialIcon icon={<Globe size={18}/>} />
              </div>
           </div>

           <div className="relative p-10 rounded-[2rem] bg-indigo-500/5 border border-indigo-500/10 overflow-hidden">
              <Quote size={60} className="absolute top-[-10px] left-[-10px] text-indigo-500/5" />
              <p className="relative z-10 text-xl font-serif italic text-indigo-300/80 leading-relaxed">
                 "Words are the only jewels which can be worn on the soul, forever radiant and eternally profound."
              </p>
           </div>
        </div>

        <div className="lg:col-span-4 space-y-10">
           <div className="p-8 rounded-[2rem] bg-slate-950/40 border border-white/5 glass">
              <h3 className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-6">Similar Minds</h3>
              <div className="space-y-3">
                 {author.similarAuthors.map(sim => (
                    <button 
                      key={sim}
                      onClick={() => onOpenAuthor(sim)}
                      className="w-full group flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-transparent hover:border-indigo-500/20 hover:bg-white/[0.08] transition-all"
                    >
                       <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center font-black text-[10px] text-indigo-400 border border-white/5">
                             {sim.charAt(0)}
                          </div>
                          <span className="text-xs font-bold text-slate-400 group-hover:text-white transition-colors">{sim}</span>
                       </div>
                       <ChevronRight size={14} className="text-slate-600 group-hover:text-indigo-400 transition-all" />
                    </button>
                 ))}
              </div>
           </div>
        </div>
      </section>

      {/* 3. BIBLIOGRAPHY */}
      <section className="p-8 lg:p-16 border-t border-white/5">
        <div className="flex items-center justify-between mb-12">
           <div className="flex items-center gap-4">
              <div className="w-8 h-px bg-indigo-500" />
              <h2 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.4em]">Masterworks</h2>
           </div>
           <span className="text-[9px] font-black text-slate-600 uppercase tracking-widest">{books.length} TITLES</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-x-6 gap-y-10">
           {books.map(book => (
             <BookCard 
               key={book.id} 
               book={book} 
               onClick={() => onOpenBook(book)} 
               onOpenDetail={(b) => onOpenBook(b)}
             />
           ))}
        </div>
      </section>
    </div>
  );
};

const AuthorStat = ({ label, value }: { label: string, value: string }) => (
  <div>
    <p className="text-[8px] font-black text-slate-600 uppercase tracking-[0.2em] mb-0.5">{label}</p>
    <p className="text-lg font-black text-white tracking-tight">{value}</p>
  </div>
);

const SocialIcon = ({ icon }: { icon: any }) => (
  <button className="p-2.5 rounded-xl bg-white/5 border border-white/5 text-slate-500 hover:text-indigo-400 hover:border-indigo-500/30 transition-all">
    {icon}
  </button>
);
