
import React, { useState, useEffect, useMemo } from 'react';
import { UserBook, getUserLibrary, getLibraryStats, getReadingChallenges, getCustomLists, ReadingChallenge, CustomList } from '../services/userBooksService';
import { getQuotes } from '../services/quotesService';
import { StarRating } from '../components/StarRating';
import { 
  Library, BookOpen, CheckCircle, Bookmark, Star, 
  TrendingUp, Clock, Filter, Search, Grid, List as ListIcon, 
  ChevronRight, MoreVertical, Plus, Sparkles, Heart, 
  Zap, Calendar, BarChart3, PieChart, Quote, ArrowUpRight,
  BrainCircuit, Timer, Trophy, Lightbulb
} from 'lucide-react';

interface LibraryViewProps {
  onOpenBook: (book: any) => void;
  onNavigateToImporter: () => void;
}

export const LibraryView: React.FC<LibraryViewProps> = ({ onOpenBook, onNavigateToImporter }) => {
  const [library, setLibrary] = useState<UserBook[]>([]);
  const [challenges, setChallenges] = useState<ReadingChallenge[]>([]);
  const [lists, setLists] = useState<CustomList[]>([]);
  const [activeTab, setActiveTab] = useState<'all' | 'reading' | 'finished' | 'wishlist' | 'favorites' | 'lists'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => {
      setLibrary(getUserLibrary());
      setChallenges(getReadingChallenges());
      setLists(getCustomLists());
      setLoading(false);
    }, 600);
  }, []);

  const stats = useMemo(() => getLibraryStats(), [library]);
  const allQuotes = useMemo(() => getQuotes(), []);
  
  const dailyQuote = useMemo(() => {
    const favorites = allQuotes.filter(q => q.isFavorite);
    if (favorites.length === 0) return allQuotes[0];
    return favorites[Math.floor(Math.random() * favorites.length)];
  }, [allQuotes]);

  const filteredLibrary = useMemo(() => {
    return library.filter(book => {
      const matchesSearch = book.volumeInfo.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                           book.volumeInfo.authors?.some(a => a.toLowerCase().includes(searchQuery.toLowerCase()));
      
      const matchesTab = 
        activeTab === 'all' ? true :
        activeTab === 'reading' ? book.libraryData.status === 'currently_reading' :
        activeTab === 'finished' ? book.libraryData.status === 'read' :
        activeTab === 'wishlist' ? book.libraryData.status === 'want_to_read' :
        activeTab === 'favorites' ? book.libraryData.isFavorite : true;

      return matchesSearch && matchesTab;
    });
  }, [library, searchQuery, activeTab]);

  const currentlyReading = useMemo(() => 
    library.filter(b => b.libraryData.status === 'currently_reading')
      .sort((a, b) => new Date(b.libraryData.lastOpened || 0).getTime() - new Date(a.libraryData.lastOpened || 0).getTime()), 
  [library]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-20 flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 border-4 border-slate-800 border-t-indigo-500 rounded-full animate-spin" />
        <p className="text-slate-500 font-bold uppercase tracking-widest text-xs">Accessing Command Center...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 animate-in fade-in duration-1000">
      
      {/* --- HERO SECTION --- */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-16 items-start">
        
        {/* Welcome Briefing */}
        <div className="lg:col-span-7 space-y-8">
          <div className="flex items-center gap-2 text-indigo-400 font-bold text-[10px] uppercase tracking-[0.4em]">
            <BrainCircuit size={14} className="fill-current" />
            Reading OS / V2.5
          </div>
          <h1 className="text-6xl font-black text-white tracking-tighter">
            Hello, <span className="text-indigo-500">Julian</span>.
          </h1>
          <p className="text-slate-400 text-xl leading-relaxed max-w-xl">
            Your personal archive of knowledge and wonder. Revisit your insights, track your growth, and find your next great exploration.
          </p>
          
          <div className="flex flex-wrap items-center gap-4 pt-2">
             <div className="px-5 py-3 rounded-2xl glass border-slate-800 flex items-center gap-4">
                <div className="flex -space-x-2">
                   {library.slice(0, 3).map((b, i) => (
                     <img key={i} src={b.volumeInfo.imageLinks?.thumbnail} className="w-6 h-6 rounded-full border-2 border-slate-950 object-cover" />
                   ))}
                </div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{stats.total} entries in vault</span>
             </div>

             <button 
              onClick={onNavigateToImporter}
              className="px-6 py-3.5 rounded-2xl bg-indigo-500 text-white font-bold shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 active:scale-95 transition-all flex items-center gap-2"
            >
              <Plus size={20} />
              Import New Book
            </button>
          </div>
        </div>

        {/* Wisdom Spotlight (Refined) */}
        <div className="lg:col-span-5">
          {dailyQuote && (
            <div className="relative p-7 rounded-[2rem] glass border-indigo-500/20 bg-gradient-to-br from-indigo-500/10 via-transparent to-purple-500/5 group overflow-hidden shadow-2xl">
               <div className="absolute top-0 right-0 p-6 opacity-[0.03] text-indigo-400 group-hover:scale-110 transition-transform duration-1000">
                  <Quote size={80} />
               </div>
               <div className="relative z-10">
                  <span className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[9px] font-black uppercase text-indigo-400 mb-5 tracking-widest">
                    <Lightbulb size={12} /> Spotlight
                  </span>
                  <p className="text-lg md:text-xl font-serif italic text-slate-200 leading-relaxed mb-5 line-clamp-4">
                    "{dailyQuote.content}"
                  </p>
                  <div>
                    <p className="text-indigo-400 font-bold text-xs">— {dailyQuote.bookAuthor}</p>
                    <p className="text-slate-500 text-[10px] font-medium uppercase tracking-wider">{dailyQuote.bookTitle}</p>
                  </div>
               </div>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        
        {/* --- LEFT COLUMN: CONTENT --- */}
        <div className="lg:col-span-8 space-y-16">
          
          {/* Active Expeditions (2-in-row, Compact) */}
          <section>
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.4em] flex items-center gap-3">
                <BookOpen size={14} className="text-indigo-500" />
                Active Expeditions
              </h2>
              <div className="h-px flex-1 bg-slate-900 mx-6" />
              <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">{currentlyReading.length} currently</span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {currentlyReading.map(book => (
                <ActiveBookHero key={book.id} book={book} onClick={() => onOpenBook(book)} />
              ))}
            </div>
          </section>

          {/* Search & Tabs Section (Centrally Organized) */}
          <section className="space-y-8 pt-6 border-t border-slate-900">
            {/* Full Width Search Bar */}
            <div className="relative group w-full">
              <div className="absolute inset-0 bg-indigo-500/5 blur-2xl opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none" />
              <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-slate-600 group-focus-within:text-indigo-500 transition-colors" size={24} />
              <input 
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Query your personal archive by title, author, or keyword..."
                className="bg-slate-900/40 border border-slate-800 rounded-3xl pl-16 pr-8 py-6 text-lg text-white placeholder-slate-600 focus:border-indigo-500/40 focus:bg-slate-900 outline-none transition-all w-full shadow-lg"
              />
            </div>

            {/* Tabs Row */}
            <div className="flex flex-wrap items-center gap-1.5 p-1.5 bg-slate-900/80 rounded-2xl border border-slate-800 w-fit">
              <TabButton active={activeTab === 'all'} onClick={() => setActiveTab('all')} label="All Vault" />
              <TabButton active={activeTab === 'finished'} onClick={() => setActiveTab('finished')} label="Finished" />
              <TabButton active={activeTab === 'favorites'} onClick={() => setActiveTab('favorites')} label="Favorites" icon={<Heart size={12} />} />
              <TabButton active={activeTab === 'lists'} onClick={() => setActiveTab('lists')} label="Collections" />
            </div>

            {/* Library Grid */}
            {activeTab === 'lists' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {lists.map(list => (
                  <ListCard key={list.id} list={list} />
                ))}
              </div>
            ) : filteredLibrary.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-x-6 gap-y-10">
                {filteredLibrary.map(book => (
                  <LibraryGridItem key={book.id} book={book} onClick={() => onOpenBook(book)} />
                ))}
              </div>
            ) : (
              <div className="py-20 text-center glass border-slate-800 rounded-[2.5rem]">
                <p className="text-slate-600 font-bold uppercase tracking-widest text-xs">No entries found in archive</p>
              </div>
            )}
          </section>
        </div>

        {/* --- RIGHT COLUMN: SIDEBAR ANALYTICS --- */}
        <div className="lg:col-span-4 space-y-8">
          
          {/* Mastery Goal */}
          <div className="p-8 rounded-[2rem] glass border-slate-800 bg-slate-900/20 group">
            <h3 className="text-slate-500 font-black uppercase tracking-[0.3em] text-[10px] mb-6">2025 Journey</h3>
            <div className="flex items-baseline gap-2 mb-4">
              <span className="text-4xl font-black text-white tracking-tighter">{stats.finishedThisYear + 14}</span>
              <span className="text-slate-600 font-bold text-lg">/ 50 books</span>
            </div>
            <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden mb-4">
              <div className="h-full bg-indigo-500 rounded-full w-[28%]" />
            </div>
            <p className="text-[10px] font-bold text-slate-500 flex items-center gap-2">
              <TrendingUp size={12} className="text-emerald-400" /> On track for 2025
            </p>
          </div>

          {/* Library DNA */}
          <div className="p-8 rounded-[2rem] glass border-slate-800 bg-slate-900/40">
            <h3 className="text-slate-500 font-black uppercase tracking-[0.3em] text-[10px] mb-6">Library DNA</h3>
            <div className="space-y-4">
              <GenreProgress label="Sci-Fi" percent={45} color="bg-sky-400" />
              <GenreProgress label="Non-Fiction" percent={30} color="bg-indigo-400" />
              <GenreProgress label="Philosophy" percent={15} color="bg-emerald-400" />
            </div>
            <button className="mt-6 text-[9px] font-black uppercase text-indigo-400 hover:text-white transition-colors flex items-center gap-2">
               Full Analysis <ArrowUpRight size={12} />
            </button>
          </div>

          {/* Consistency Heatmap */}
          <div className="p-8 rounded-[2rem] glass border-slate-800 bg-slate-900/40">
            <h3 className="text-slate-500 font-black uppercase tracking-[0.3em] text-[10px] mb-6">Consistency</h3>
            <div className="grid grid-cols-7 gap-1.5 mb-5">
              {Array.from({length: 28}).map((_, i) => (
                <div key={i} className={`aspect-square rounded-[2px] ${i > 20 ? 'bg-indigo-500' : i > 10 ? 'bg-indigo-500/30' : 'bg-slate-800'}`} />
              ))}
            </div>
            <div className="flex justify-between items-center">
               <div>
                  <span className="text-xl font-black text-white block">12 Days</span>
                  <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Active Streak</span>
               </div>
               <div className="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                  <Zap size={14} className="fill-current" />
               </div>
            </div>
          </div>

          {/* Mini Challenges */}
          <section className="space-y-4 pt-4">
            <h2 className="text-[9px] font-black text-slate-600 uppercase tracking-[0.4em]">Current Challenges</h2>
            {challenges.slice(0, 1).map(challenge => (
              <div key={challenge.id} className="p-6 rounded-2xl glass border-slate-800 bg-slate-900/10 group hover:border-indigo-500/20 transition-all">
                <div className="flex justify-between mb-3">
                  <span className="text-white text-xs font-bold">{challenge.title}</span>
                  <span className="text-indigo-400 text-xs font-black">{challenge.current}/{challenge.goal}</span>
                </div>
                <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-indigo-500" style={{ width: `${(challenge.current / challenge.goal) * 100}%` }} />
                </div>
              </div>
            ))}
          </section>
        </div>
      </div>
    </div>
  );
};

// --- SUB-COMPONENTS ---

const ActiveBookHero = ({ book, onClick }: { book: UserBook, onClick: () => void }) => {
  const progress = Math.round((book.libraryData.currentPage / (book.volumeInfo.pageCount || 100)) * 100);
  
  return (
    <div 
      onClick={onClick}
      className="group relative p-5 rounded-2xl glass border-slate-800 hover:border-indigo-500/40 transition-all cursor-pointer bg-slate-900/40 overflow-hidden flex items-center gap-5 shadow-xl"
    >
      <div className="shrink-0 w-20 aspect-[2/3] rounded-lg overflow-hidden shadow-2xl ring-1 ring-white/10 group-hover:scale-105 transition-transform duration-500">
        <img src={book.volumeInfo.imageLinks?.thumbnail} alt={book.volumeInfo.title} className="w-full h-full object-cover" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="mb-3">
          <div className="flex items-center gap-2 mb-1">
             <span className="text-[8px] font-black text-indigo-400 uppercase tracking-widest px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20">Decoding</span>
          </div>
          <h3 className="text-lg font-black text-white line-clamp-1 leading-tight group-hover:text-indigo-400 transition-colors">
            {book.volumeInfo.title}
          </h3>
          <p className="text-slate-500 text-[10px] font-bold truncate">by {book.volumeInfo.authors?.[0]}</p>
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-lg font-black text-white tracking-tighter">{progress}%</span>
            <span className="text-[8px] text-slate-500 font-black uppercase tracking-widest">Progress</span>
          </div>
          <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden shadow-inner">
            <div 
              className="h-full bg-indigo-500 rounded-full transition-all duration-1000"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

const LibraryGridItem = ({ book, onClick }: { book: UserBook, onClick: () => void }) => {
  const coverUrl = book.volumeInfo.imageLinks?.thumbnail || `https://via.placeholder.com/300x450/1E293B/64748B?text=${encodeURIComponent(book.volumeInfo.title)}`;
  
  return (
    <div onClick={onClick} className="group cursor-pointer space-y-4">
      <div className="relative aspect-[2/3] rounded-[1.5rem] overflow-hidden shadow-lg ring-1 ring-white/10 border border-slate-800/50 group-hover:ring-indigo-500/40 transition-all duration-500">
        <img src={coverUrl} alt={book.volumeInfo.title} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" />
        <div className="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 transition-all duration-500 flex flex-col items-center justify-center p-4">
          <span className="text-[9px] font-black text-white uppercase tracking-[0.2em] px-4 py-2 rounded-full bg-indigo-500 shadow-xl transform translate-y-4 group-hover:translate-y-0 transition-transform">
            View Entry
          </span>
        </div>
        {book.libraryData.status === 'currently_reading' && (
          <div className="absolute bottom-3 left-3 right-3 h-1 bg-white/10 rounded-full overflow-hidden backdrop-blur-md">
             <div 
               className="h-full bg-indigo-400" 
               style={{ width: `${Math.round((book.libraryData.currentPage / (book.volumeInfo.pageCount || 100)) * 100)}%` }} 
             />
          </div>
        )}
        <div className={`absolute top-4 right-4 p-2 rounded-xl backdrop-blur-xl border border-white/5 ${
          book.libraryData.status === 'read' ? 'bg-emerald-500/20 text-emerald-400' :
          book.libraryData.status === 'currently_reading' ? 'bg-indigo-500/20 text-indigo-400' :
          'bg-slate-800/40 text-slate-400'
        }`}>
          {book.libraryData.status === 'read' ? <CheckCircle size={14} /> : 
           book.libraryData.status === 'currently_reading' ? <BookOpen size={14} /> : 
           <Bookmark size={14} />}
        </div>
      </div>
      <div className="px-1">
        <h4 className="text-xs font-black text-slate-100 line-clamp-1 group-hover:text-indigo-400 transition-colors">{book.volumeInfo.title}</h4>
        <p className="text-[9px] text-slate-500 font-black uppercase tracking-widest mt-1 truncate">{book.volumeInfo.authors?.[0]}</p>
      </div>
    </div>
  );
};

const TabButton = ({ active, onClick, label, icon }: { active: boolean, onClick: () => void, label: string, icon?: any }) => (
  <button 
    onClick={onClick}
    className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-[10px] font-black transition-all uppercase tracking-widest ${
      active ? 'bg-indigo-500 text-white shadow-md' : 'text-slate-500 hover:text-slate-300'
    }`}
  >
    {icon}
    {label}
  </button>
);

const GenreProgress = ({ label, percent, color }: { label: string, percent: number, color: string }) => (
  <div className="space-y-2">
    <div className="flex justify-between text-[9px] font-black uppercase tracking-widest">
      <span className="text-slate-400">{label}</span>
      <span className="text-slate-500">{percent}%</span>
    </div>
    <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
      <div className={`h-full ${color} rounded-full`} style={{ width: `${percent}%` }} />
    </div>
  </div>
);

const ListCard = ({ list }: { list: CustomList }) => (
  <div className="p-8 rounded-[2rem] glass border-slate-800 bg-slate-900/30 group hover:border-indigo-500/30 transition-all cursor-pointer shadow-xl">
    <div className="flex items-center justify-between mb-6">
      <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 group-hover:scale-110 transition-transform">
        <Sparkles size={24} />
      </div>
      <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{list.bookIds.length} Books</span>
    </div>
    <h4 className="text-xl font-black text-white mb-2">{list.title}</h4>
    <p className="text-[11px] text-slate-500 line-clamp-2 leading-relaxed font-medium">{list.description}</p>
  </div>
);
