
import React, { useState, useEffect, useMemo } from 'react';
import { QuoteCard } from '../components/QuoteCard';
import { QuoteModal } from '../components/QuoteModal';
import { getQuotes, saveQuote, deleteQuote, toggleFavorite } from '../services/quotesService';
import { Quote } from '../types';
import { Search, Plus, Filter, Type, Sparkles, BookOpen, Star, LayoutGrid, List } from 'lucide-react';

interface QuotesViewProps {
  onToast: (msg: string) => void;
  onOpenBook?: (title: string) => void;
}

export const QuotesView: React.FC<QuotesViewProps> = ({ onToast, onOpenBook }) => {
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [isFavoriteOnly, setIsFavoriteOnly] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingQuote, setEditingQuote] = useState<Quote | null>(null);

  useEffect(() => {
    setQuotes(getQuotes());
  }, []);

  const stats = useMemo(() => {
    return {
      total: quotes.length,
      favorites: quotes.filter(q => q.isFavorite).length,
      books: new Set(quotes.map(q => q.bookTitle)).size
    };
  }, [quotes]);

  const filteredQuotes = useMemo(() => {
    return quotes.filter(q => {
      const matchesSearch = 
        q.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        q.bookTitle.toLowerCase().includes(searchQuery.toLowerCase()) ||
        q.bookAuthor.toLowerCase().includes(searchQuery.toLowerCase()) ||
        q.notes?.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesTag = !activeTag || q.tags.includes(activeTag);
      const matchesFavorite = !isFavoriteOnly || q.isFavorite;

      return matchesSearch && matchesTag && matchesFavorite;
    });
  }, [quotes, searchQuery, activeTag, isFavoriteOnly]);

  const handleSave = (payload: any) => {
    const updated = saveQuote(payload);
    setQuotes(getQuotes());
    setIsModalOpen(false);
    setEditingQuote(null);
    onToast(payload.id ? 'Insight updated successfully' : 'New insight added to library');
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to remove this insight?')) {
      deleteQuote(id);
      setQuotes(getQuotes());
      onToast('Insight removed from library');
    }
  };

  const handleToggleFavorite = (id: string) => {
    toggleFavorite(id);
    setQuotes(getQuotes());
  };

  return (
    <div className="animate-in fade-in duration-700">
      {/* Page Header */}
      <div className="max-w-7xl mx-auto pt-12 pb-8 px-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-12">
          <header>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                <Type className="text-indigo-400" size={24} />
              </div>
              <span className="text-sm font-bold text-indigo-400 uppercase tracking-[0.3em]">Insights & Quotes</span>
            </div>
            <h1 className="text-5xl font-black text-white tracking-tight mb-4">
              The <span className="text-indigo-500">Collected</span> Mind
            </h1>
            <p className="text-slate-400 text-lg max-w-2xl leading-relaxed">
              Your digital commonplace book. Revisit the ideas that shaped your perspective and preserve the beauty of language.
            </p>
          </header>

          <button 
            onClick={() => setIsModalOpen(true)}
            className="group flex items-center gap-3 px-8 py-5 rounded-2xl bg-indigo-500 text-white font-bold shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 active:scale-95 transition-all"
          >
            <Plus size={24} className="group-hover:rotate-90 transition-transform duration-300" />
            Add New Insight
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6 mb-12">
          <StatCard icon={<Sparkles size={20} />} label="Total Insights" value={stats.total} color="indigo" />
          <StatCard icon={<Star size={20} />} label="Favorite Gems" value={stats.favorites} color="amber" />
          <StatCard icon={<BookOpen size={20} />} label="Sources Quoted" value={stats.books} color="sky" />
        </div>

        {/* Filter Bar */}
        <div className="space-y-6">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative group">
              <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-indigo-500 transition-colors" size={20} />
              <input 
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search across content, books, or authors..."
                className="w-full bg-slate-900/50 border-2 border-slate-800 rounded-2xl px-14 py-4 text-white focus:border-indigo-500 transition-all outline-none"
              />
            </div>
            
            <div className="flex gap-4">
              <button 
                onClick={() => setIsFavoriteOnly(!isFavoriteOnly)}
                className={`flex items-center gap-3 px-6 py-4 rounded-2xl border-2 transition-all ${
                  isFavoriteOnly ? 'border-amber-500 bg-amber-500/10 text-amber-400' : 'border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <Star size={18} fill={isFavoriteOnly ? 'currentColor' : 'none'} />
                <span className="font-bold">Favorites</span>
              </button>
              
              <div className="flex items-center gap-1 p-1 bg-slate-900/50 rounded-2xl border border-slate-800">
                <ViewButton active={true} icon={<LayoutGrid size={18} />} />
                <ViewButton active={false} icon={<List size={18} />} />
              </div>
            </div>
          </div>

          {activeTag && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-widest mr-2">Filtered by:</span>
              <button 
                onClick={() => setActiveTag(null)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/20 border border-indigo-500/40 text-indigo-400 text-sm font-bold"
              >
                #{activeTag}
                <Plus className="rotate-45" size={14} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-7xl mx-auto px-6 pb-20">
        {filteredQuotes.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-40 text-center animate-in fade-in duration-500">
            <div className="w-20 h-20 rounded-full bg-slate-900/50 border border-slate-800 flex items-center justify-center mb-6">
              <Sparkles size={32} className="text-slate-700" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-2">No insights found</h3>
            <p className="text-slate-500 max-w-sm">
              Adjust your filters or capture your first quote to start building your collection.
            </p>
            {(searchQuery || activeTag || isFavoriteOnly) && (
              <button 
                onClick={() => { setSearchQuery(''); setActiveTag(null); setIsFavoriteOnly(false); }}
                className="mt-6 text-indigo-400 font-bold hover:text-indigo-300 transition-colors"
              >
                Clear all filters
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {filteredQuotes.map(quote => (
              <QuoteCard 
                key={quote.id}
                quote={quote}
                onEdit={(q) => { setEditingQuote(q); setIsModalOpen(true); }}
                onDelete={handleDelete}
                onToggleFavorite={handleToggleFavorite}
                onTagClick={setActiveTag}
                onOpenBook={onOpenBook}
              />
            ))}
          </div>
        )}
      </div>

      {/* Modals */}
      {(isModalOpen || editingQuote) && (
        <QuoteModal 
          quote={editingQuote}
          onClose={() => { setIsModalOpen(false); setEditingQuote(null); }}
          onSave={handleSave}
        />
      )}
    </div>
  );
};

const StatCard = ({ icon, label, value, color }: { icon: any, label: string, value: number, color: 'indigo' | 'amber' | 'sky' }) => {
  const colors = {
    indigo: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20 shadow-indigo-500/5',
    amber: 'text-amber-400 bg-amber-500/10 border-amber-500/20 shadow-amber-500/5',
    sky: 'text-sky-400 bg-sky-500/10 border-sky-500/20 shadow-sky-500/5',
  };

  return (
    <div className={`p-6 rounded-3xl border-2 transition-all duration-500 hover:scale-[1.02] shadow-xl ${colors[color]}`}>
      <div className="flex items-center gap-3 mb-4 opacity-70">
        {icon}
        <span className="text-xs font-bold uppercase tracking-widest">{label}</span>
      </div>
      <p className="text-4xl font-black text-white">{value}</p>
    </div>
  );
};

const ViewButton = ({ active, icon }: { active: boolean, icon: any }) => (
  <button className={`p-3 rounded-xl transition-all ${active ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400'}`}>
    {icon}
  </button>
);
