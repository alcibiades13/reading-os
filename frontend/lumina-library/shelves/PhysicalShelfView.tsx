
import React, { useState, useMemo } from 'react';
import { UserBook, CustomShelf, ShelfType } from '../types';
import { 
  Trophy, BookOpen, BarChart3, 
  Layers, Plus, Star, Sparkles,
  Library, ChevronRight, Settings, Layout, Trash2
} from 'lucide-react';

interface PhysicalShelfViewProps {
  library: UserBook[];
  onOpenBook: (book: UserBook) => void;
  onNavigateToImporter: () => void;
}

export const PhysicalShelfView: React.FC<PhysicalShelfViewProps> = ({ library, onOpenBook, onNavigateToImporter }) => {
  const [activeGoal, setActiveGoal] = useState({ current: 24, total: 50 });
  
  // State for custom shelves
  const [customShelves, setCustomShelves] = useState<CustomShelf[]>([
    { id: 'all-books', title: 'Complete Library', type: 'mahogany', bookIds: library.map(b => b.id) },
    { id: 'favorites', title: 'Philosophy Gems', type: 'glass', bookIds: library.filter(b => b.libraryData.isFavorite).map(b => b.id) },
    { id: 'sci-fi', title: 'Sci-Fi Expeditions', type: 'oak', bookIds: library.filter(b => b.volumeInfo.categories?.includes('Sci-Fi')).map(b => b.id) }
  ]);

  const stats = useMemo(() => {
    const totalPages = library.reduce((acc, b) => acc + (b.volumeInfo.pageCount || 0), 0);
    const readBooks = library.filter(b => b.libraryData.status === 'read').length;
    return {
      total: library.length,
      totalPages,
      readBooks,
      progress: Math.round((readBooks / (library.length || 1)) * 100),
      favoriteGenre: 'Science Fiction'
    };
  }, [library]);

  const handleAddShelf = () => {
    const newShelf: CustomShelf = {
      id: `shelf-${Date.now()}`,
      title: 'New Collection',
      type: 'minimal',
      bookIds: []
    };
    setCustomShelves([...customShelves, newShelf]);
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 animate-in fade-in duration-1000">
      
      {/* --- PREMIUM DASHBOARD --- */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-24">
        <StatTile 
          icon={<Trophy className="text-amber-400" size={22} />} 
          label="Reading Goal" 
          value={`${activeGoal.current}/${activeGoal.total}`} 
          subValue="Books in 2025"
          progress={(activeGoal.current / activeGoal.total) * 100}
        />
        <StatTile 
          icon={<BookOpen className="text-indigo-400" size={22} />} 
          label="Library Progress" 
          value={`${stats.progress}%`} 
          subValue="Total catalog read"
          progress={stats.progress}
        />
        <StatTile 
          icon={<BarChart3 className="text-emerald-400" size={22} />} 
          label="Total Pages" 
          value={stats.totalPages.toLocaleString()} 
          subValue="Physical pages owned"
        />
        <StatTile 
          icon={<Sparkles className="text-purple-400" size={22} />} 
          label="Top Genre" 
          value={stats.favoriteGenre} 
          subValue="Based on your shelf"
        />
      </div>

      {/* --- HEADER --- */}
      <div className="flex flex-col md:flex-row items-center justify-between mb-16 gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <div className="h-px w-8 bg-indigo-500"></div>
            <span className="text-[10px] font-black uppercase tracking-[0.4em] text-indigo-400">Physical Archive</span>
          </div>
          <h2 className="text-5xl font-black text-white tracking-tighter">My <span className="text-indigo-500">Personal</span> Sanctum</h2>
        </div>
        
        <div className="flex items-center gap-4">
          <button 
            onClick={handleAddShelf}
            className="flex items-center gap-2 px-6 py-4 rounded-2xl bg-white/5 border border-white/10 text-white font-bold text-[10px] uppercase tracking-widest hover:bg-white/10 transition-all"
          >
            <Plus size={16} /> New Collection
          </button>
          <button 
            onClick={onNavigateToImporter}
            className="flex items-center gap-2 px-8 py-4 rounded-2xl bg-indigo-500 text-white font-black text-[10px] uppercase tracking-widest hover:scale-105 active:scale-95 transition-all shadow-2xl shadow-indigo-500/20"
          >
            <Library size={16} /> Add Volume
          </button>
        </div>
      </div>

      {/* --- THE SHELVES --- */}
      <div className="space-y-40 pb-20">
        {customShelves.map(shelf => {
          const shelfBooks = library.filter(b => shelf.bookIds.includes(b.id));
          return (
            <ShelfRow 
              key={shelf.id}
              shelf={shelf}
              books={shelfBooks}
              onOpenBook={onOpenBook}
            />
          );
        })}
      </div>
    </div>
  );
};

const StatTile: React.FC<{ icon: React.ReactNode, label: string, value: string, subValue: string, progress?: number }> = ({ icon, label, value, subValue, progress }) => (
  <div className="p-8 rounded-[2.5rem] glass border-white/5 bg-white/[0.03] relative overflow-hidden group hover:bg-white/[0.05] transition-all duration-500">
    <div className="relative z-10">
      <div className="flex items-center justify-between mb-6">
        <div className="p-3 rounded-2xl bg-white/5 border border-white/10 group-hover:scale-110 transition-transform duration-500">
          {icon}
        </div>
        <span className="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em]">{label}</span>
      </div>
      <p className="text-4xl font-black text-white mb-2 tracking-tighter">{value}</p>
      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{subValue}</p>
      
      {progress !== undefined && (
        <div className="mt-6 w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000 shadow-[0_0_12px_rgba(99,102,241,0.5)]" 
            style={{ width: `${progress}%` }} 
          />
        </div>
      )}
    </div>
  </div>
);

const ShelfRow: React.FC<{ shelf: CustomShelf, books: UserBook[], onOpenBook: (b: UserBook) => void }> = ({ shelf, books, onOpenBook }) => {
  const shelfStyles: Record<ShelfType, string> = {
    mahogany: 'from-amber-900 via-amber-950 to-stone-950 border-white/5 shadow-2xl',
    glass: 'from-indigo-500/20 via-white/10 to-indigo-500/20 border-white/20 shadow-xl backdrop-blur-md',
    oak: 'from-amber-700/40 via-amber-800/50 to-amber-950/40 border-amber-800/10 shadow-lg',
    minimal: 'from-white/5 to-white/[0.02] border-white/10 shadow-md'
  };

  return (
    <div className="relative">
      {/* Shelf Labels */}
      <div className="flex items-center justify-between mb-8 px-4">
        <div className="flex items-center gap-4">
          <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></div>
          <h3 className="text-[12px] font-black text-white uppercase tracking-[0.4em]">{shelf.title}</h3>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-[9px] font-black text-slate-400 uppercase tracking-widest">
            {books.length} VOLUMES
          </span>
          <button className="p-2 text-slate-600 hover:text-white transition-colors">
            <Settings size={14} />
          </button>
        </div>
      </div>

      <div className="relative min-h-[300px] perspective-shelf">
        {/* BOOKS STANDING ON TOP OF THE SHELF */}
        <div className="flex items-end gap-[4px] px-12 absolute bottom-[50px] left-0 right-0 z-20 overflow-visible">
          {books.map(book => (
            <Spine3D key={book.id} book={book} onClick={() => onOpenBook(book)} />
          ))}
        </div>

        {/* 3D SHELF BASE - FIXED PHYSICS */}
        <div className="absolute bottom-0 left-0 right-0 z-10 h-[50px]">
          {/* Top Surface (Where books sit) */}
          <div className={`h-[12px] w-full rounded-t-2xl bg-gradient-to-r ${shelfStyles[shelf.type]} border-t border-x border-white/10 relative z-20 shadow-[0_-5px_15px_rgba(0,0,0,0.5)]`}>
             <div className="absolute inset-0 bg-white/[0.02] rounded-t-2xl" />
          </div>
          {/* Front Edge (Visible face) */}
          <div className={`h-[38px] w-full rounded-b-2xl bg-gradient-to-b from-black/20 to-black/60 border-x border-b border-white/5 relative z-10 flex items-center justify-center`}>
             <div className="w-1/3 h-px bg-white/5"></div>
          </div>
        </div>

        {books.length === 0 && (
           <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20">
             <p className="text-[9px] font-black uppercase tracking-[1em] text-slate-500">Vacant Workspace</p>
           </div>
        )}
      </div>
    </div>
  );
};

const Spine3D: React.FC<{ book: UserBook, onClick: () => void }> = ({ book, onClick }) => {
  const pageCount = book.volumeInfo.pageCount || 250;
  
  const baselinePages = 250;
  const baselineWidth = 45;
  const calculatedWidth = Math.max(20, Math.min(95, (pageCount / baselinePages) * baselineWidth));
  const height = Math.max(190, Math.min(240, 210 + (pageCount / 60)));

  return (
    <div 
      onClick={onClick}
      className="relative group cursor-pointer book-hover-effect flex flex-col items-center"
      style={{ width: `${calculatedWidth}px` }}
    >
      {/* Premium Tooltip */}
      <div className="absolute -top-20 opacity-0 group-hover:opacity-100 transition-all duration-300 pointer-events-none z-50 whitespace-nowrap bg-white text-slate-950 px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest shadow-[0_20px_50px_rgba(0,0,0,0.5)] border border-white/20">
        {book.volumeInfo.title}
        <div className="absolute bottom-[-6px] left-1/2 -translate-x-1/2 w-3 h-3 bg-white rotate-45" />
      </div>

      {/* The 3D Spine Surface - added transition classes to sync with hover lift */}
      <div 
        className={`w-full relative rounded-t-md border-x border-t border-white/10 group-hover:border-indigo-400 shadow-[10px_0_30px_rgba(0,0,0,0.4)] overflow-hidden transition-all duration-500 ${book.libraryData.spineColor || 'bg-slate-800'}`}
        style={{ height: `${height}px` }}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-black/20 via-transparent to-black/20 pointer-events-none" />

        <div className="absolute inset-0 flex items-center justify-center p-3 [writing-mode:vertical-rl] rotate-180 pointer-events-none">
          <span className="text-[10px] font-black text-white/95 uppercase tracking-[0.2em] line-clamp-1 max-h-[80%] drop-shadow-md">
            {book.volumeInfo.title}
          </span>
        </div>

        <div className="absolute top-0 left-0 right-0 h-[3px] bg-white/20 pointer-events-none" />
        <div className="absolute top-6 left-0 right-0 h-[1px] bg-black/30 pointer-events-none" />
        <div className="absolute bottom-6 left-0 right-0 h-[1px] bg-black/30 pointer-events-none" />

        {book.libraryData.status === 'currently_reading' && (
          <div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center pointer-events-none">
             <div className="w-2 h-2 rounded-full bg-indigo-400 shadow-[0_0_15px_#818cf8] animate-pulse" />
          </div>
        )}
      </div>
      
      {/* Contact Shadow on shelf surface */}
      <div className="absolute bottom-0 w-full h-2 bg-black/60 blur-[4px] opacity-40 group-hover:opacity-0 transition-opacity duration-500 pointer-events-none" />
    </div>
  );
};
