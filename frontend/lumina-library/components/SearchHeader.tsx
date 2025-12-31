
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

  // Debounced search
  useEffect(() => {
    if (tab === 'advanced') return;
    const timeout = setTimeout(() => {
      onSearch(query, tab === 'isbn' ? 'isbn' : 'general');
    }, 500);
    return () => clearTimeout(timeout);
  }, [query, tab]);

  // Keyboard shortcut
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
    <div className="w-full max-w-7xl mx-auto pt-12 pb-8 px-6">
      <header className="mb-12">
        <h1 className="text-5xl font-black text-white tracking-tight mb-4">
          Discover & <span className="text-sky-500">Import</span>
        </h1>
        <p className="text-slate-400 text-lg max-w-2xl leading-relaxed">
          Search millions of books from Google Books API and build your digital library with our premium discovery engine.
        </p>
      </header>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 bg-slate-900/80 rounded-xl mb-6 w-fit border border-slate-800">
        <TabButton active={tab === 'general'} onClick={() => setTab('general')} icon={<Search size={16} />} label="Quick Search" />
        <TabButton active={tab === 'isbn'} onClick={() => setTab('isbn')} icon={<Hash size={16} />} label="ISBN Lookup" />
        <TabButton active={tab === 'advanced'} onClick={() => {}} icon={<Filter size={16} />} label="Advanced" badge="Coming Soon" />
      </div>

      {/* Search Input */}
      <div className={`relative group transition-all duration-300 ${isFocused ? 'scale-[1.01]' : ''}`}>
        <div className={`absolute inset-0 bg-sky-500/10 blur-xl opacity-0 transition-opacity duration-300 ${isFocused ? 'opacity-100' : ''}`} />
        <div className={`relative flex items-center glass rounded-2xl overflow-hidden px-6 py-5 border-2 transition-all duration-300 ${isFocused ? 'border-sky-500 shadow-2xl' : 'border-slate-800'}`}>
          <Search className={`mr-4 transition-colors duration-300 ${isFocused ? 'text-sky-500' : 'text-slate-500'}`} size={24} />
          <input 
            ref={inputRef}
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={tab === 'isbn' ? "Enter 10 or 13 digit ISBN..." : "Search by title, author, or keywords..."}
            className="flex-1 bg-transparent border-none outline-none text-xl text-white placeholder-slate-600 font-medium"
          />
          <div className="hidden sm:flex items-center gap-1 px-3 py-1 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-500 text-xs font-bold">
            <Command size={12} />
            <span>K</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const TabButton = ({ active, onClick, icon, label, badge }: { active: boolean, onClick: () => void, icon: React.ReactNode, label: string, badge?: string }) => (
  <button 
    onClick={onClick}
    className={`relative flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 ${
      active ? 'bg-slate-800 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'
    }`}
  >
    {icon}
    {label}
    {badge && (
      <span className="text-[9px] bg-amber-500/20 text-amber-500 px-1.5 py-0.5 rounded uppercase tracking-tighter ml-1">
        {badge}
      </span>
    )}
  </button>
);
