
import React, { useState, useEffect, useCallback } from 'react';
import { SearchHeader } from './components/SearchHeader';
import { BookCard } from './components/BookCard';
import { BookPreviewModal } from './components/BookPreviewModal';
import { SkeletonCard } from './components/SkeletonLoader';
import { searchBooks } from './services/googleBooks';
import { GoogleBook, ImportPayload, VocabularyWord, StudyNote, UserBook } from './types';
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
import { saveWord } from './services/vocabularyService';
import { saveQuote } from './services/quotesService';
import { getUserLibrary } from './services/userBooksService';
import { Library, Search, Sparkles, Quote, Users, Brain, Sun, Moon, Layers, MessageSquare } from 'lucide-react';

type View = 'importer' | 'quotes' | 'feed' | 'library' | 'my_shelf' | 'book_detail' | 'book_review' | 'vocabulary' | 'study_mode' | 'correspondence';
type Theme = 'light' | 'dark';

const App: React.FC = () => {
  const [view, setView] = useState<View>('feed');
  const [theme, setTheme] = useState<Theme>(() => {
    return (localStorage.getItem('lumina_theme') as Theme) || 'dark';
  });
  const [results, setResults] = useState<GoogleBook[]>([]);
  const [userLibrary, setUserLibrary] = useState<UserBook[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedBookPreview, setSelectedBookPreview] = useState<GoogleBook | null>(null);
  const [currentBookDetail, setCurrentBookDetail] = useState<GoogleBook | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toasts, setToasts] = useState<{id: number, message: string, type?: 'success' | 'info' | 'emerald'}[]>([]);

  useEffect(() => {
    setUserLibrary(getUserLibrary());
  }, []);

  const [isVocabModalOpen, setIsVocabModalOpen] = useState(false);
  const [vocabInitialBook, setVocabInitialBook] = useState<GoogleBook | null>(null);

  useEffect(() => {
    const body = document.body;
    if (theme === 'light') body.classList.add('light');
    else body.classList.remove('light');
    localStorage.setItem('lumina_theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(prev => prev === 'light' ? 'dark' : 'light');

  const handleSearch = useCallback(async (query: string, type: 'general' | 'isbn') => {
    if (!query.trim()) { setResults([]); return; }
    setLoading(true); setError(null);
    try {
      const data = await searchBooks(query, type);
      setResults(data);
    } catch (err) { setError('Something went wrong.'); }
    finally { setLoading(false); }
  }, []);

  const addToast = (message: string, type: 'success' | 'info' | 'emerald' = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
  };

  const handleImport = (payload: ImportPayload) => {
    addToast(`Successfully imported "${payload.book.volumeInfo.title}"!`);
    setSelectedBookPreview(null);
    setView('my_shelf'); 
  };

  const openBookDetail = (book: GoogleBook) => {
    setCurrentBookDetail(book);
    setSelectedBookPreview(null);
    setView('book_detail');
  };

  const openBookByTitle = async (title: string) => {
    setLoading(true);
    try {
      const books = await searchBooks(title, 'general');
      if (books.length > 0) openBookDetail(books[0]);
      else addToast(`Could not find "${title}"`);
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen transition-colors duration-500 selection:bg-indigo-500/30">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-sky-900/10 blur-[120px] rounded-full dark:bg-sky-900/20" />
        <div className="absolute bottom-[10%] right-[-10%] w-[30%] h-[50%] bg-indigo-900/5 blur-[120px] rounded-full dark:bg-indigo-900/10" />
      </div>

      <nav className={`relative z-[60] main-nav sticky top-0 transition-all duration-500 ${view === 'book_review' || view === 'study_mode' ? 'hidden' : ''}`}>
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer group" onClick={() => setView('feed')}>
            <div className="w-10 h-10 rounded-xl bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/30 group-hover:scale-105 transition-transform">
              <Library size={22} className="text-white" />
            </div>
            <span className="font-black text-2xl tracking-tighter text-slate-900 dark:text-white group-hover:text-indigo-500 transition-colors">VELLUX</span>
          </div>
          
          <div className="flex items-center gap-6 md:gap-10">
            <div className="hidden lg:flex items-center gap-8">
              <NavButton active={view === 'feed'} onClick={() => setView('feed')} label="Feed" />
              <NavButton active={view === 'my_shelf'} onClick={() => setView('my_shelf')} label="My Shelf" icon={<Layers size={12} />} />
              <NavButton active={view === 'library'} onClick={() => setView('library')} label="Vault" />
              <NavButton active={view === 'correspondence'} onClick={() => setView('correspondence')} label="Correspondence" icon={<MessageSquare size={12} />} />
              <NavButton active={view === 'importer'} onClick={() => setView('importer')} label="Discover" />
              <NavButton active={view === 'quotes'} onClick={() => setView('quotes')} label="Quotes" />
              <NavButton active={view === 'vocabulary'} onClick={() => setView('vocabulary')} label="Lexicon" />
            </div>
            
            <div className="flex items-center gap-4">
              <button onClick={toggleTheme} className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-500 dark:text-slate-400 hover:text-indigo-500 dark:hover:text-indigo-400 transition-all shadow-sm">
                {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
              </button>
              <div className="hidden md:flex w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 items-center justify-center text-[10px] font-black text-slate-900 dark:text-white">JS</div>
            </div>
          </div>
        </div>
      </nav>

      <main className="relative z-10 pb-20">
        {view === 'importer' ? (
          <>
            <SearchHeader onSearch={handleSearch} />
            <div className="max-w-7xl mx-auto px-6">
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-x-8 gap-y-12">
                {loading ? Array.from({ length: 10 }).map((_, i) => <SkeletonCard key={i} />) : results.map((book) => <BookCard key={book.id} book={book} onClick={() => setSelectedBookPreview(book)} onOpenDetail={openBookDetail} />)}
              </div>
            </div>
          </>
        ) : view === 'my_shelf' ? (
          <PhysicalShelfView library={userLibrary} onOpenBook={openBookDetail} onNavigateToImporter={() => setView('importer')} />
        ) : view === 'library' ? (
          <LibraryView onOpenBook={openBookDetail} onNavigateToImporter={() => setView('importer')} />
        ) : view === 'quotes' ? (
          <QuotesView onToast={addToast} onOpenBook={openBookByTitle} />
        ) : view === 'feed' ? (
          <FeedView onOpenBook={openBookByTitle} />
        ) : view === 'vocabulary' ? (
          <VocabularyView onToast={addToast} onOpenModal={() => setIsVocabModalOpen(true)} />
        ) : view === 'correspondence' ? (
          <CorrespondenceView />
        ) : view === 'book_detail' && currentBookDetail ? (
          <BookDetailView book={currentBookDetail} onBack={() => setView('my_shelf')} onToast={addToast} onWriteReview={() => setView('book_review')} onAddWord={() => setIsVocabModalOpen(true)} onEnterStudyMode={() => setView('study_mode')} />
        ) : null}
      </main>

      {selectedBookPreview && <BookPreviewModal book={selectedBookPreview} onClose={() => setSelectedBookPreview(null)} onImport={handleImport} onOpenDetail={() => openBookDetail(selectedBookPreview)} />}
      {isVocabModalOpen && <VocabularyModal initialBook={vocabInitialBook} onClose={() => setIsVocabModalOpen(false)} onSave={() => {}} />}

      <div className="fixed bottom-8 right-8 z-[200] flex flex-col gap-3 pointer-events-none">
        {toasts.map(toast => (
          <div key={toast.id} className="pointer-events-auto glass border rounded-xl px-5 py-4 shadow-2xl flex items-center gap-3 animate-in slide-in-from-right-full">
            <Sparkles size={14} className="text-indigo-500" />
            <p className="text-sm font-bold text-slate-900 dark:text-slate-200">{toast.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

const NavButton = ({ active, onClick, label, icon }: { active: boolean, onClick: () => void, label: string, icon?: any }) => (
  <button onClick={onClick} className={`text-[11px] md:text-xs font-black uppercase tracking-[0.2em] transition-all flex items-center gap-2 ${active ? 'text-indigo-500 dark:text-indigo-400' : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'}`}>
    {icon} {label}
  </button>
);

export default App;
