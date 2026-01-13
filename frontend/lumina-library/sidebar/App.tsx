
import React, { useState, useEffect, useCallback } from 'react';
import { SearchHeader } from './components/SearchHeader';
import { BookCard } from './components/BookCard';
import { BookPreviewModal } from './components/BookPreviewModal';
import { SkeletonCard } from './components/SkeletonLoader';
import { searchBooks } from './services/googleBooks';
import { GoogleBook, ImportPayload, UserBook } from './types';
import { QuotesView } from './views/QuotesView';
import { FeedView } from './views/FeedView';
import { LibraryView } from './views/LibraryView';
import { PhysicalShelfView } from './views/PhysicalShelfView';
import { BookDetailView } from './views/BookDetailView';
import { BookReviewView } from './views/BookReviewView';
import { VocabularyView } from './views/VocabularyView';
import { StudyView } from './views/StudyView';
import { CorrespondenceView } from './views/CorrespondenceView';
import { VocabularyModal } from './components/VocabularyModal';
import { getUserLibrary } from './services/userBooksService';
import { 
  Library, Search, Sparkles, Quote, Users, Brain, 
  Sun, Moon, Layers, MessageSquare, Compass, 
  Trophy, Settings, Bell, ChevronDown, LogOut, User
} from 'lucide-react';

type View = 'importer' | 'quotes' | 'feed' | 'library' | 'my_shelf' | 'book_detail' | 'book_review' | 'vocabulary' | 'study_mode' | 'correspondence' | 'challenges';
type Theme = 'light' | 'dark';

const App: React.FC = () => {
  const [view, setView] = useState<View>('feed');
  const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem('lumina_theme') as Theme) || 'dark');
  const [results, setResults] = useState<GoogleBook[]>([]);
  const [userLibrary, setUserLibrary] = useState<UserBook[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedBookPreview, setSelectedBookPreview] = useState<GoogleBook | null>(null);
  const [currentBookDetail, setCurrentBookDetail] = useState<GoogleBook | null>(null);
  const [toasts, setToasts] = useState<{id: number, message: string}[]>([]);
  const [isVocabModalOpen, setIsVocabModalOpen] = useState(false);

  useEffect(() => {
    setUserLibrary(getUserLibrary());
  }, []);

  useEffect(() => {
    const body = document.body;
    if (theme === 'light') {
      body.classList.add('light');
    } else {
      body.classList.remove('light');
    }
    localStorage.setItem('lumina_theme', theme);
  }, [theme]);

  const handleSearch = useCallback(async (query: string, type: 'general' | 'isbn') => {
    if (!query.trim()) { setResults([]); return; }
    setLoading(true);
    try {
      const data = await searchBooks(query, type);
      setResults(data);
      setView('importer');
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, []);

  const addToast = (message: string) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
  };

  return (
    <div className="flex min-h-screen transition-colors duration-500 overflow-hidden bg-[var(--color-bg)]">
      {/* --- SIDEBAR --- */}
      <aside className="w-72 hidden lg:flex flex-col glass border-r border-[var(--color-border)] z-50 sticky top-0 h-screen bg-[var(--color-surface)] backdrop-blur-3xl">
        <div className="p-8">
          <div className="flex items-center gap-3 mb-12 cursor-pointer group" onClick={() => setView('feed')}>
            <div className="w-10 h-10 rounded-xl bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/40 group-hover:scale-105 transition-transform">
              <Library size={22} className="text-white" />
            </div>
            <span className="font-black text-2xl tracking-tighter text-[var(--color-text-primary)]">VELLUX</span>
          </div>

          <nav className="space-y-1">
            <NavGroup label="Main">
              <SidebarItem active={view === 'feed'} onClick={() => setView('feed')} icon={<Users size={18} />} label="Activity Feed" />
              <SidebarItem active={view === 'importer'} onClick={() => setView('importer')} icon={<Compass size={18} />} label="Discover" />
              <SidebarItem active={view === 'library'} onClick={() => setView('library')} label="Vault" icon={<Library size={18} />} />
              <SidebarItem active={view === 'my_shelf'} onClick={() => setView('my_shelf')} label="Physical Shelf" icon={<Layers size={18} />} />
            </NavGroup>

            <NavGroup label="Commonplace">
              <SidebarItem active={view === 'quotes'} onClick={() => setView('quotes')} label="Quotes" icon={<Quote size={18} />} />
              <SidebarItem active={view === 'vocabulary'} onClick={() => setView('vocabulary')} label="Lexicon" icon={<Brain size={18} />} />
              <SidebarItem active={view === 'correspondence'} onClick={() => setView('correspondence')} label="Messages" icon={<MessageSquare size={18} />} badge="2" />
            </NavGroup>

            <NavGroup label="Systems">
              <SidebarItem active={view === 'challenges'} onClick={() => setView('challenges')} label="Challenges" icon={<Trophy size={18} />} />
            </NavGroup>
          </nav>
        </div>

        <div className="mt-auto p-6 border-t border-[var(--color-border)]">
          <button className="w-full flex items-center gap-4 p-3 rounded-2xl hover:bg-[var(--color-border)] transition-all group">
            <div className="w-10 h-10 rounded-xl bg-slate-800 border border-white/10 flex items-center justify-center text-[10px] font-black text-white group-hover:border-indigo-500 transition-colors">JS</div>
            <div className="text-left">
              <p className="text-xs font-bold text-[var(--color-text-primary)]">Julian Thorne</p>
              <p className="text-[10px] text-[var(--color-text-secondary)] font-bold uppercase tracking-widest">Premium Member</p>
            </div>
            <Settings size={14} className="ml-auto text-[var(--color-text-secondary)]" />
          </button>
        </div>
      </aside>

      {/* --- MAIN CONTENT AREA --- */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* --- REFINED TOP HEADER --- */}
        <header className="h-20 border-b border-[var(--color-border)] flex items-center justify-between px-8 bg-[var(--color-surface)] backdrop-blur-xl z-40">
          <div className="flex-1 max-w-2xl relative group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-text-secondary)] group-focus-within:text-indigo-500 transition-colors" size={18} />
            <input 
              type="text" 
              placeholder="Search across the entire library..." 
              onKeyDown={(e) => e.key === 'Enter' && handleSearch((e.target as HTMLInputElement).value, 'general')}
              className="w-full bg-white/5 border border-[var(--color-border)] rounded-2xl pl-12 pr-4 py-2.5 text-sm text-[var(--color-text-primary)] outline-none focus:border-indigo-500 transition-all placeholder-slate-600"
            />
            <div className="absolute right-4 top-1/2 -translate-y-1/2 hidden md:flex items-center gap-1 px-2 py-0.5 rounded-lg bg-white/5 border border-[var(--color-border)] text-[9px] font-black text-[var(--color-text-secondary)] uppercase tracking-widest">
              Cmd + K
            </div>
          </div>

          <div className="flex items-center gap-6 ml-8">
            <div className="flex items-center gap-1 p-1 bg-white/5 rounded-xl border border-[var(--color-border)]">
              <button onClick={() => setTheme('light')} className={`p-2 rounded-lg transition-all ${theme === 'light' ? 'bg-indigo-500 text-white shadow-lg' : 'text-[var(--color-text-secondary)] hover:text-indigo-500'}`}>
                <Sun size={18} />
              </button>
              <button onClick={() => setTheme('dark')} className={`p-2 rounded-lg transition-all ${theme === 'dark' ? 'bg-indigo-500 text-white shadow-lg' : 'text-[var(--color-text-secondary)] hover:text-indigo-500'}`}>
                <Moon size={18} />
              </button>
            </div>
            
            <button className="relative p-2.5 text-[var(--color-text-secondary)] hover:text-indigo-500 transition-colors">
              <Bell size={20} />
              <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-indigo-500 border-2 border-[var(--color-bg)]" />
            </button>

            <div className="h-8 w-px bg-[var(--color-border)]" />

            <div className="flex items-center gap-3 cursor-pointer group">
              <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 p-0.5">
                <div className="w-full h-full rounded-full bg-slate-900 flex items-center justify-center text-[10px] font-black text-white">JS</div>
              </div>
              <ChevronDown size={16} className="text-[var(--color-text-secondary)] group-hover:text-indigo-500 transition-colors" />
            </div>
          </div>
        </header>

        {/* --- VIEW CONTENT --- */}
        <main className="flex-1 overflow-y-auto custom-scrollbar bg-[var(--color-bg)]">
          {view === 'importer' ? (
            <div className="p-8">
              <SearchHeader onSearch={handleSearch} />
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-x-6 gap-y-10">
                {loading ? Array.from({ length: 12 }).map((_, i) => <SkeletonCard key={i} />) : results.map((book) => <BookCard key={book.id} book={book} onClick={() => setSelectedBookPreview(book)} onOpenDetail={(b) => { setCurrentBookDetail(b); setView('book_detail'); }} />)}
              </div>
            </div>
          ) : view === 'my_shelf' ? (
            <PhysicalShelfView library={userLibrary} onOpenBook={(b) => { setCurrentBookDetail(b); setView('book_detail'); }} onNavigateToImporter={() => setView('importer')} />
          ) : view === 'library' ? (
            <LibraryView onOpenBook={(b) => { setCurrentBookDetail(b); setView('book_detail'); }} onNavigateToImporter={() => setView('importer')} />
          ) : view === 'quotes' ? (
            <QuotesView onToast={addToast} onOpenBook={(t) => console.log(t)} />
          ) : view === 'feed' ? (
            <FeedView onOpenBook={(t) => console.log(t)} />
          ) : view === 'vocabulary' ? (
            <VocabularyView onToast={addToast} onOpenModal={() => setIsVocabModalOpen(true)} />
          ) : view === 'correspondence' ? (
            <CorrespondenceView />
          ) : view === 'book_detail' && currentBookDetail ? (
            <BookDetailView book={currentBookDetail} onBack={() => setView('my_shelf')} onToast={addToast} onWriteReview={() => setView('book_review')} onAddWord={() => setIsVocabModalOpen(true)} onEnterStudyMode={() => setView('study_mode')} />
          ) : (
            <div className="flex items-center justify-center h-full opacity-20 flex-col gap-4">
              <Sparkles size={64} className="text-[var(--color-text-primary)]" />
              <p className="font-black uppercase tracking-[1em] text-xs text-[var(--color-text-primary)]">Awaiting Entry</p>
            </div>
          )}
        </main>
      </div>

      {selectedBookPreview && <BookPreviewModal book={selectedBookPreview} onClose={() => setSelectedBookPreview(null)} onImport={(p) => { addToast(`Imported ${p.book.volumeInfo.title}`); setView('my_shelf'); setSelectedBookPreview(null); }} onOpenDetail={() => { setCurrentBookDetail(selectedBookPreview); setView('book_detail'); setSelectedBookPreview(null); }} />}
      {isVocabModalOpen && <VocabularyModal onClose={() => setIsVocabModalOpen(false)} onSave={() => {}} />}

      <div className="fixed bottom-8 right-8 z-[200] flex flex-col gap-3 pointer-events-none">
        {toasts.map(toast => (
          <div key={toast.id} className="pointer-events-auto glass border border-[var(--color-border)] rounded-xl px-5 py-4 shadow-2xl flex items-center gap-3 animate-in slide-in-from-right-full">
            <Sparkles size={14} className="text-indigo-500" />
            <p className="text-sm font-bold text-[var(--color-text-primary)]">{toast.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

const NavGroup = ({ label, children }: { label: string, children: React.ReactNode }) => (
  <div className="py-4">
    <h3 className="px-4 text-[10px] font-black text-[var(--color-text-secondary)] uppercase tracking-[0.2em] mb-3">{label}</h3>
    <div className="space-y-1">{children}</div>
  </div>
);

const SidebarItem = ({ active, onClick, label, icon, badge }: { active: boolean, onClick: () => void, label: string, icon: any, badge?: string }) => (
  <button 
    onClick={onClick} 
    className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-300 group ${
      active 
      ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20 font-bold' 
      : 'text-[var(--color-text-secondary)] hover:text-indigo-500 hover:bg-[var(--color-border)]'
    }`}
  >
    <div className={`${active ? 'text-white' : 'text-[var(--color-text-secondary)] group-hover:text-indigo-400'} transition-colors`}>
      {icon}
    </div>
    <span className="text-sm tracking-tight">{label}</span>
    {badge && (
      <span className={`ml-auto px-2 py-0.5 rounded-lg text-[9px] font-black ${active ? 'bg-white text-indigo-500' : 'bg-indigo-500 text-white'}`}>
        {badge}
      </span>
    )}
  </button>
);

export default App;
