
import React, { useState, useEffect, useCallback } from 'react';
import { SearchHeader } from './components/SearchHeader';
import { BookCard } from './components/BookCard';
import { BookPreviewModal } from './components/BookPreviewModal';
import { SkeletonCard } from './components/SkeletonLoader';
import { searchBooks } from './services/googleBooks';
import { GoogleBook, ImportPayload, VocabularyWord, StudyNote } from './types';
import { QuotesView } from './views/QuotesView';
import { FeedView } from './views/FeedView';
import { LibraryView } from './views/LibraryView';
import { BookDetailView } from './views/BookDetailView';
import { BookReviewView } from './views/BookReviewView';
import { VocabularyView } from './views/VocabularyView';
import { StudyView } from './views/StudyView';
import { VocabularyModal } from './components/VocabularyModal';
import { saveWord } from './services/vocabularyService';
import { saveQuote } from './services/quotesService';
import { Library, Search, Sparkles, Quote, Users, Brain, Sun, Moon } from 'lucide-react';

type View = 'importer' | 'quotes' | 'feed' | 'library' | 'book_detail' | 'book_review' | 'vocabulary' | 'study_mode';
type Theme = 'light' | 'dark';

const App: React.FC = () => {
  const [view, setView] = useState<View>('feed');
  const [theme, setTheme] = useState<Theme>(() => {
    return (localStorage.getItem('lumina_theme') as Theme) || 'dark';
  });
  const [results, setResults] = useState<GoogleBook[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedBookPreview, setSelectedBookPreview] = useState<GoogleBook | null>(null);
  const [currentBookDetail, setCurrentBookDetail] = useState<GoogleBook | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toasts, setToasts] = useState<{id: number, message: string, type?: 'success' | 'info' | 'emerald'}[]>([]);

  // Vocabulary Global Modal
  const [isVocabModalOpen, setIsVocabModalOpen] = useState(false);
  const [vocabInitialBook, setVocabInitialBook] = useState<GoogleBook | null>(null);

  // Sync theme with body class
  useEffect(() => {
    const body = document.body;
    if (theme === 'light') {
      body.classList.add('light');
    } else {
      body.classList.remove('light');
    }
    localStorage.setItem('lumina_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  const handleSearch = useCallback(async (query: string, type: 'general' | 'isbn') => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const data = await searchBooks(query, type);
      setResults(data);
    } catch (err) {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  const addToast = (message: string, type: 'success' | 'info' | 'emerald' = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  };

  const handleImport = (payload: ImportPayload) => {
    addToast(`Successfully imported "${payload.book.volumeInfo.title}" to your library!`);
    setSelectedBookPreview(null);
    setView('library'); 
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
      if (books.length > 0) {
        openBookDetail(books[0]);
      } else {
        addToast(`Could not find full details for "${title}"`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleOpenVocabModal = (book?: GoogleBook) => {
    setVocabInitialBook(book || null);
    setIsVocabModalOpen(true);
  };

  const handleSaveVocab = (payload: Partial<VocabularyWord>, addAnother: boolean) => {
    saveWord(payload);
    addToast(`Added "${payload.word}" to lexicon`, 'emerald');
    if (!addAnother) {
      setIsVocabModalOpen(false);
      setVocabInitialBook(null);
    }
  };

  const handlePromoteToQuote = (note: StudyNote) => {
    if (!currentBookDetail) return;
    
    saveQuote({
      bookId: currentBookDetail.id,
      bookTitle: currentBookDetail.volumeInfo.title,
      bookAuthor: currentBookDetail.volumeInfo.authors?.[0] || 'Unknown',
      bookCover: currentBookDetail.volumeInfo.imageLinks?.thumbnail,
      content: note.content,
      chapter: note.reference,
      isPublic: true,
      isFavorite: false,
      tags: note.tags,
    });
    
    addToast('Insight promoted to main library', 'info');
  };

  return (
    <div className="min-h-screen transition-colors duration-500 selection:bg-indigo-500/30">
      {/* Background Gradients */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-sky-900/10 blur-[120px] rounded-full dark:bg-sky-900/20" />
        <div className="absolute bottom-[10%] right-[-10%] w-[30%] h-[50%] bg-indigo-900/5 blur-[120px] rounded-full dark:bg-indigo-900/10" />
      </div>

      <nav className={`relative z-[60] border-b border-slate-900/10 dark:border-slate-900 bg-white/50 dark:bg-slate-950/50 backdrop-blur-md sticky top-0 transition-colors duration-500 ${view === 'book_review' || view === 'study_mode' ? 'hidden' : ''}`}>
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => setView('feed')}>
            <div className="w-10 h-10 rounded-xl bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Library size={22} className="text-white" />
            </div>
            <span className="font-black text-2xl tracking-tighter text-slate-900 dark:text-white">LUMINA</span>
          </div>
          
          <div className="flex items-center gap-6 md:gap-10">
            <div className="hidden lg:flex items-center gap-8">
              <NavButton active={view === 'feed'} onClick={() => setView('feed')} label="Feed" />
              <NavButton active={view === 'library'} onClick={() => setView('library')} label="Library" />
              <NavButton active={view === 'importer'} onClick={() => setView('importer')} label="Discover" />
              <NavButton active={view === 'quotes'} onClick={() => setView('quotes')} label="Quotes" />
              <NavButton active={view === 'vocabulary'} onClick={() => setView('vocabulary')} label="Lexicon" icon={<Brain size={12} />} />
            </div>
            
            <div className="flex items-center gap-4">
              {/* Theme Toggle Button */}
              <button 
                onClick={toggleTheme}
                className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-500 dark:text-slate-400 hover:text-indigo-500 dark:hover:text-indigo-400 transition-all shadow-sm hover:shadow-md"
                aria-label="Toggle Theme"
              >
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
              {error && (
                <div className="mb-8 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 dark:text-red-400 text-center">
                  {error}
                </div>
              )}

              {!loading && results.length === 0 && !error && (
                <div className="flex flex-col items-center justify-center py-32 text-center opacity-50">
                  <div className="p-8 rounded-full bg-slate-100 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 mb-6">
                    <Search size={48} className="text-slate-400 dark:text-slate-600" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Search millions of books</h2>
                  <p className="max-w-md text-slate-500 dark:text-slate-400">Enter a title, author, or ISBN to start exploring. Try searching for "The Midnight Library".</p>
                </div>
              )}

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-x-8 gap-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
                {loading ? (
                  Array.from({ length: 10 }).map((_, i) => <SkeletonCard key={i} />)
                ) : (
                  results.map((book) => (
                    <BookCard 
                      key={book.id} 
                      book={book} 
                      onClick={() => setSelectedBookPreview(book)} 
                      onOpenDetail={openBookDetail}
                    />
                  ))
                )}
              </div>
            </div>
          </>
        ) : view === 'library' ? (
          <LibraryView onOpenBook={openBookDetail} onNavigateToImporter={() => setView('importer')} />
        ) : view === 'quotes' ? (
          <QuotesView onToast={(msg) => addToast(msg)} onOpenBook={openBookByTitle} />
        ) : view === 'feed' ? (
          <FeedView onOpenBook={openBookByTitle} />
        ) : view === 'vocabulary' ? (
          <VocabularyView onToast={(msg) => addToast(msg, 'emerald')} onOpenModal={() => handleOpenVocabModal()} />
        ) : view === 'book_detail' && currentBookDetail ? (
          <BookDetailView 
            book={currentBookDetail} 
            onBack={() => setView('library')} 
            onToast={(msg) => addToast(msg)} 
            onWriteReview={() => setView('book_review')}
            onAddWord={() => handleOpenVocabModal(currentBookDetail)}
            onEnterStudyMode={() => setView('study_mode')}
          />
        ) : view === 'book_review' && currentBookDetail ? (
          <BookReviewView 
            book={currentBookDetail}
            onBack={() => setView('book_detail')}
            onSave={(content, isPublic) => {
              addToast(`Review for "${currentBookDetail.volumeInfo.title}" published!`);
              setView('book_detail');
            }}
          />
        ) : view === 'study_mode' && currentBookDetail ? (
          <StudyView 
            book={currentBookDetail}
            onBack={() => setView('book_detail')}
            onToast={(msg) => addToast(msg, 'info')}
            onPromoteToQuote={handlePromoteToQuote}
          />
        ) : null}
      </main>

      {/* Global Modals */}
      {selectedBookPreview && (
        <BookPreviewModal 
          book={selectedBookPreview} 
          onClose={() => setSelectedBookPreview(null)}
          onImport={handleImport}
          onOpenDetail={() => openBookDetail(selectedBookPreview)}
        />
      )}

      {isVocabModalOpen && (
        <VocabularyModal 
          initialBook={vocabInitialBook}
          onClose={() => setIsVocabModalOpen(false)}
          onSave={handleSaveVocab}
        />
      )}

      {/* Toast Notifications */}
      <div className="fixed bottom-8 right-8 z-[200] flex flex-col gap-3 pointer-events-none">
        {toasts.map(toast => (
          <div 
            key={toast.id}
            className={`pointer-events-auto glass border rounded-xl px-5 py-4 shadow-2xl flex items-center gap-3 animate-in slide-in-from-right-full duration-300 ${
              toast.type === 'emerald' ? 'border-emerald-500/30 bg-emerald-500/10' : 
              toast.type === 'info' ? 'border-indigo-500/30 bg-indigo-500/10' :
              'border-slate-200 dark:border-slate-800'
            }`}
          >
            <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
              toast.type === 'emerald' ? 'bg-emerald-500/20' : 'bg-indigo-500/20'
            }`}>
              <Sparkles size={14} className={toast.type === 'emerald' ? 'text-emerald-500' : 'text-indigo-500 dark:text-indigo-400'} />
            </div>
            <p className="text-sm font-bold text-slate-900 dark:text-slate-200">{toast.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

const NavButton = ({ active, onClick, label, icon }: { active: boolean, onClick: () => void, label: string, icon?: any }) => (
  <button 
    onClick={onClick}
    className={`text-[11px] md:text-xs font-black uppercase tracking-[0.2em] transition-all flex items-center gap-2 ${active ? 'text-indigo-500 dark:text-indigo-400' : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'}`}
  >
    {icon}
    {label}
  </button>
);

export default App;
