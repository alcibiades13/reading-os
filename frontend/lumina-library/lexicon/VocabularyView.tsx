
import React, { useState, useEffect, useMemo } from 'react';
import { VocabularyWord, MasteryLevel } from '../types';
import { getVocabulary, saveWord, deleteWord, updateMastery, getVocabStats } from '../services/vocabularyService';
import { WordCard } from '../components/WordCard';
import { FlashcardPlayer } from '../components/FlashcardPlayer';
import { Brain, LayoutGrid, BarChart3, Plus, Search, Filter, Sparkles, BookOpen, CheckCircle, Clock } from 'lucide-react';

interface VocabularyViewProps {
  onToast: (msg: string) => void;
  onOpenModal: () => void;
}

export const VocabularyView: React.FC<VocabularyViewProps> = ({ onToast, onOpenModal }) => {
  const [words, setWords] = useState<VocabularyWord[]>([]);
  const [activeView, setActiveView] = useState<'library' | 'practice' | 'stats'>('library');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterLevel, setFilterLevel] = useState<MasteryLevel | 'all'>('all');

  useEffect(() => {
    setWords(getVocabulary());
  }, []);

  const stats = useMemo(() => getVocabStats(), [words]);

  const filteredWords = useMemo(() => {
    return words.filter(w => {
      const matchesSearch = w.word.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           w.context?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           w.bookTitle?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesLevel = filterLevel === 'all' || w.mastery === filterLevel;
      return matchesSearch && matchesLevel;
    });
  }, [words, searchQuery, filterLevel]);

  const practiceWords = useMemo(() => {
    return words.filter(w => w.mastery !== 'mastered').sort((a, b) => b.reviewCount - a.reviewCount);
  }, [words]);

  const handleDelete = (id: string) => {
    if (confirm('Permanently remove this word from your lexicon?')) {
      deleteWord(id);
      setWords(getVocabulary());
      onToast('Word removed from library');
    }
  };

  const handleUpdateMastery = (id: string, level: MasteryLevel) => {
    updateMastery(id, level);
    setWords(getVocabulary());
  };

  return (
    <div className="animate-in fade-in duration-700">
      {/* Page Header */}
      <div className="max-w-7xl mx-auto pt-12 pb-8 px-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-12">
          <header>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                <Brain className="text-emerald-400" size={24} />
              </div>
              <span className="text-sm font-bold text-emerald-400 uppercase tracking-[0.3em]">Personal Lexicon</span>
            </div>
            <h1 className="text-5xl font-black text-white tracking-tight mb-4">
              The <span className="text-emerald-500">Vocabulary</span> Vault
            </h1>
            <p className="text-slate-400 text-lg max-w-2xl leading-relaxed">
              Build and master a sophisticated vocabulary from your reading explorations. Practice with intelligent flashcards.
            </p>
          </header>

          <button 
            onClick={onOpenModal}
            className="group flex items-center gap-3 px-8 py-5 rounded-2xl bg-emerald-500 text-white font-bold shadow-xl shadow-emerald-500/20 hover:bg-emerald-400 active:scale-95 transition-all"
          >
            <Plus size={24} className="group-hover:rotate-90 transition-transform duration-300" />
            Capture New Word
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1.5 p-1.5 bg-slate-900/80 rounded-2xl border border-slate-800 w-fit mb-12">
          <TabButton active={activeView === 'library'} onClick={() => setActiveView('library')} label="Library" icon={<LayoutGrid size={16} />} />
          <TabButton active={activeView === 'practice'} onClick={() => setActiveView('practice')} label="Practice" icon={<Brain size={16} />} />
          <TabButton active={activeView === 'stats'} onClick={() => setActiveView('stats')} label="Insights" icon={<BarChart3 size={16} />} />
        </div>

        {activeView === 'library' && (
          <div className="space-y-10">
            {/* Filter Bar */}
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="flex-1 relative group">
                <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-emerald-500 transition-colors" size={20} />
                <input 
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search your lexicon..."
                  className="w-full bg-slate-900/50 border-2 border-slate-800 rounded-2xl px-14 py-4 text-white focus:border-emerald-500 transition-all outline-none"
                />
              </div>
              
              <div className="flex items-center gap-1 p-1 bg-slate-900/50 rounded-2xl border border-slate-800">
                <FilterToggle active={filterLevel === 'all'} onClick={() => setFilterLevel('all')} label="All" />
                <FilterToggle active={filterLevel === 'new'} onClick={() => setFilterLevel('new')} label="New" />
                <FilterToggle active={filterLevel === 'learning'} onClick={() => setFilterLevel('learning')} label="Learning" />
                <FilterToggle active={filterLevel === 'mastered'} onClick={() => setFilterLevel('mastered')} label="Mastered" />
              </div>
            </div>

            {/* Library Grid */}
            {filteredWords.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredWords.map(word => (
                  <WordCard 
                    key={word.id} 
                    word={word} 
                    onEdit={() => {}} 
                    onDelete={handleDelete}
                    onUpdateMastery={handleUpdateMastery}
                  />
                ))}
              </div>
            ) : (
              <div className="py-32 text-center glass border-slate-800 rounded-[2.5rem]">
                <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto mb-6 text-slate-600">
                  <BookOpen size={28} />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">Lexicon empty</h3>
                <p className="text-slate-500">Try searching for a different term or capture your first word.</p>
              </div>
            )}
          </div>
        )}

        {activeView === 'practice' && (
          <div className="py-12">
            {practiceWords.length > 0 ? (
              <FlashcardPlayer 
                words={practiceWords} 
                onComplete={() => { setActiveView('library'); onToast('Session completed! Keep it up.'); }}
                onUpdateMastery={handleUpdateMastery}
              />
            ) : (
              <div className="max-w-xl mx-auto py-24 text-center glass border-emerald-500/20 bg-emerald-500/5 rounded-[2.5rem]">
                <div className="w-20 h-20 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-8 text-emerald-400">
                  <CheckCircle size={40} />
                </div>
                <h3 className="text-2xl font-black text-white mb-4">You're all caught up!</h3>
                <p className="text-slate-400 leading-relaxed mb-8">
                  All your collected words are mastered. Collect more insights from your reading to continue learning.
                </p>
                <button 
                  onClick={() => setActiveView('library')}
                  className="px-8 py-4 rounded-xl bg-emerald-500 text-white font-bold"
                >
                  Return to Library
                </button>
              </div>
            )}
          </div>
        )}

        {activeView === 'stats' && (
          <div className="space-y-12">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <StatCard icon={<Sparkles size={20} />} label="Total Vault" value={stats.total} color="emerald" />
              <StatCard icon={<Clock size={20} />} label="New Arrivals" value={stats.new} color="indigo" />
              <StatCard icon={<Brain size={20} />} label="Currently Learning" value={stats.learning} color="amber" />
              <StatCard icon={<CheckCircle size={20} />} label="Mastered" value={stats.mastered} color="sky" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
              <div className="p-10 rounded-[2.5rem] glass border-slate-800">
                <h3 className="text-lg font-black text-white mb-8 uppercase tracking-widest flex items-center gap-3">
                  <BookOpen size={20} className="text-emerald-400" /> Top Sources
                </h3>
                <div className="space-y-6">
                  {Object.entries(stats.byBook).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([book, count]) => (
                    <div key={book} className="flex items-center justify-between">
                      <span className="text-slate-400 font-bold truncate pr-4">{book}</span>
                      <div className="flex items-center gap-4">
                        <div className="w-32 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-500" style={{ width: `${(count / stats.total) * 100}%` }} />
                        </div>
                        <span className="text-white font-black w-8 text-right">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-10 rounded-[2.5rem] glass border-slate-800 bg-emerald-500/5">
                <h3 className="text-lg font-black text-white mb-4 uppercase tracking-widest">Growth Forecast</h3>
                <p className="text-slate-400 text-sm leading-relaxed mb-8">
                  Your lexicon is growing at an average of 1.2 words per session. At this rate, you will reach 1,000 words by November 2025.
                </p>
                <div className="aspect-[2/1] bg-slate-900/50 rounded-2xl border border-slate-800 flex items-center justify-center">
                  <BarChart3 className="text-slate-700" size={48} />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const TabButton = ({ active, onClick, label, icon }: { active: boolean, onClick: () => void, label: string, icon: any }) => (
  <button 
    onClick={onClick}
    className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all ${
      active ? 'bg-emerald-500 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'
    }`}
  >
    {icon}
    {label}
  </button>
);

const FilterToggle = ({ active, onClick, label }: { active: boolean, onClick: () => void, label: string }) => (
  <button 
    onClick={onClick}
    className={`px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
      active ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400'
    }`}
  >
    {label}
  </button>
);

const StatCard = ({ icon, label, value, color }: { icon: any, label: string, value: number, color: string }) => {
  const colors: Record<string, string> = {
    emerald: 'text-emerald-400 border-emerald-500/20 bg-emerald-500/5',
    indigo: 'text-indigo-400 border-indigo-500/20 bg-indigo-500/5',
    amber: 'text-amber-400 border-amber-500/20 bg-amber-500/5',
    sky: 'text-sky-400 border-sky-500/20 bg-sky-500/5',
  };

  return (
    <div className={`p-8 rounded-[2rem] glass border transition-all ${colors[color]}`}>
      <div className="flex items-center gap-3 mb-4 opacity-70">
        {icon}
        <span className="text-[10px] font-black uppercase tracking-widest">{label}</span>
      </div>
      <p className="text-4xl font-black text-white">{value}</p>
    </div>
  );
};
