
import React, { useState, useEffect, useRef } from 'react';
import { Search, Command, Filter, Hash } from 'lucide-react';

interface SearchHeaderProps {
  onSearch: (query: string, type: 'general' | 'isbn') => void;
}

export const SearchHeader: React.FC<SearchHeaderProps> = ({ onSearch }) => {
  const [query, setQuery] = useState('');
  const [tab, setTab] = useState<'general' | 'isbn' | 'advanced'>('general');
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (tab === 'advanced' || !query) return;
    const timeout = setTimeout(() => {
      onSearch(query, tab === 'isbn' ? 'isbn' : 'general');
    }, 500);
    return () => clearTimeout(timeout);
  }, [query, tab]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="w-full mb-12">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-black text-white tracking-tight mb-2">
            Discover <span className="text-indigo-500">Volume</span>
          </h1>
          <p className="text-slate-500 text-sm font-medium">Search millions of titles across the Google Books API</p>
        </div>
        
        <div className="flex items-center gap-1 p-1 bg-white/5 rounded-xl border border-white/5">
          <TabButton active={tab === 'general'} onClick={() => setTab('general')} icon={<Search size={14} />} label="Search" />
          <TabButton active={tab === 'isbn'} onClick={() => setTab('isbn')} icon={<Hash size={14} />} label="ISBN" />
          <TabButton active={tab === 'advanced'} onClick={() => {}} icon={<Filter size={14} />} label="Advanced" badge="Soon" />
        </div>
      </div>

      <div className={`relative group transition-all duration-300 ${isFocused ? 'scale-[1.005]' : ''}`}>
        <div className={`absolute inset-0 bg-indigo-500/10 blur-2xl opacity-0 transition-opacity duration-300 ${isFocused ? 'opacity-100' : ''}`} />
        <div className={`relative flex items-center glass rounded-3xl overflow-hidden px-8 py-6 border-2 transition-all duration-300 ${isFocused ? 'border-indigo-500 shadow-2xl bg-slate-900/60' : 'border-white/5 bg-slate-900/40'}`}>
          <Search className={`mr-4 transition-colors duration-300 ${isFocused ? 'text-indigo-500' : 'text-slate-500'}`} size={24} />
          <input 
            ref={inputRef}
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={tab === 'isbn' ? "Enter 10 or 13 digit ISBN..." : "Find your next intellectual obsession..."}
            className="flex-1 bg-transparent border-none outline-none text-2xl text-white placeholder-slate-700 font-serif italic"
          />
        </div>
      </div>
    </div>
  );
};

const TabButton = ({ active, onClick, icon, label, badge }: { active: boolean, onClick: () => void, icon: React.ReactNode, label: string, badge?: string }) => (
  <button 
    onClick={onClick}
    className={`relative flex items-center gap-2 px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all duration-200 ${
      active ? 'bg-indigo-500 text-white shadow-md' : 'text-slate-500 hover:text-white'
    }`}
  >
    {icon}
    {label}
    {badge && (
      <span className="text-[8px] bg-white/10 text-slate-400 px-1.5 py-0.5 rounded ml-1">
        {badge}
      </span>
    )}
  </button>
);
