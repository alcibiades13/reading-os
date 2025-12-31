
import React, { useState, useEffect, useCallback } from 'react';
import { SearchHeader } from './components/SearchHeader';
import { BookCard } from './components/BookCard';
import { BookPreviewModal } from './components/BookPreviewModal';
import { SkeletonCard } from './components/SkeletonLoader';
import { searchBooks } from './services/googleBooks';
import { GoogleBook, ImportPayload } from './types';
import { QuotesView } from './views/QuotesView';
import { FeedView } from './views/FeedView';
import { BookDetailView } from './views/BookDetailView';
import { BookReviewView } from './views/BookReviewView';
import { Library, Search, Sparkles, Quote, Users } from 'lucide-react';

type View = 'importer' | 'quotes' | 'feed' | 'book_detail' | 'book_review';

const App: React.FC = () => {
  const [view, setView] = useState<View>('feed');
  const [results, setResults] = useState<GoogleBook[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedBookPreview, setSelectedBookPreview] = useState<GoogleBook | null>(null);
  const [currentBookDetail, setCurrentBookDetail] = useState<GoogleBook | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toasts, setToasts] = useState<{id: number, message: string}[]>([]);

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

  const addToast = (message: string) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  };

  const handleImport = (payload: ImportPayload) => {
    addToast(`Successfully imported "${payload.book.volumeInfo.title}" to your library!`);
    setSelectedBookPreview(null);
  };

  const openBookDetail = (book: GoogleBook) => {
    setCurrentBookDetail(book);
    setSelectedBookPreview(null);
    setView('book_detail');
  };

  const openBookReview = (book: GoogleBook) => {
    setCurrentBookDetail(book);
    setView('book_review');
  };

  // Helper za otvaranje detalja na osnovu naslova (iz Feed-a ili Quotes-a)
  const openBookByTitle = async (title: string) => {
    setLoading(true);
    setView('importer'); // Switch to search view while fetching if needed
    try {
      const books = await searchBooks(title, 'general');
      if (books.length > 0) {
        openBookDetail(books[0]);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500/30">
      {/* Background Gradients */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-sky-900/20 blur-[120px] rounded-full" />
        <div className="absolute bottom-[10%] right-[-10%] w-[30%] h-[50%] bg-indigo-900/10 blur-[120px] rounded-full" />
      </div>

      <nav className={`relative z-[60] border-b border-slate-900 bg-slate-950/50 backdrop-blur-md sticky top-0 ${view === 'book_review' ? 'hidden' : ''}`}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => setView('feed')}>
            <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Library size={18} className="text-white" />
            </div>
            <span className="font-black text-xl tracking-tighter text-white">LUMINA</span>
          </div>
          <div className="flex items-center gap-8">
            <button 
              onClick={() => setView('feed')}
              className={`text-sm font-bold transition-all flex items-center gap-2 ${view === 'feed' ? 'text-indigo-400' : 'text-slate-400 hover:text-white'}`}
            >
              Feed
            </button>
            <button 
              onClick={() => setView('importer')}
              className={`text-sm font-bold transition-all ${view === 'importer' ? 'text-indigo-400' : 'text-slate-400 hover:text-white'}`}
            >
              Importer
            </button>
            <button 
              onClick={() => setView('quotes')}
              className={`text-sm font-bold transition-all flex items-center gap-2 ${view === 'quotes' ? 'text-indigo-400' : 'text-slate-400 hover:text-white'}`}
            >
              Quotes
            </button>
            <a href="#" className="text-sm font-bold text-slate-400 hover:text-white transition-colors">My Collection</a>
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-[10px] font-bold">JS</div>
          </div>
        </div>
      </nav>

      <main className="relative z-10 pb-20">
        {view === 'importer' ? (
          <>
            <SearchHeader onSearch={handleSearch} />
            <div className="max-w-7xl mx-auto px-6">
              {error && (
                <div className="mb-8 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-center">
                  {error}
                </div>
              )}

              {!loading && results.length === 0 && !error && (
                <div className="flex flex-col items-center justify-center py-32 text-center opacity-50">
                  <div className="p-6 rounded-full bg-slate-900/50 border border-slate-800 mb-6">
                    <Search size={48} className="text-slate-600" />
                  </div>
                  <h2 className="text-2xl font-bold text-white mb-2">Search millions of books</h2>
                  <p className="max-w-md">Enter a title, author, or ISBN to start exploring. Try searching for "The Midnight Library".</p>
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
        ) : view === 'quotes' ? (
          <QuotesView onToast={addToast} onOpenBook={openBookByTitle} />
        ) : view === 'feed' ? (
          <FeedView onOpenBook={openBookByTitle} />
        ) : view === 'book_detail' && currentBookDetail ? (
          <BookDetailView 
            book={currentBookDetail} 
            onBack={() => setView('importer')} 
            onToast={addToast} 
            onWriteReview={() => setView('book_review')}
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
        ) : null}
      </main>

      {/* Modal Overlay for Preview */}
      {selectedBookPreview && (
        <BookPreviewModal 
          book={selectedBookPreview} 
          onClose={() => setSelectedBookPreview(null)}
          onImport={handleImport}
          onOpenDetail={() => openBookDetail(selectedBookPreview)}
        />
      )}

      {/* Toast Notifications */}
      <div className="fixed bottom-8 right-8 z-[100] flex flex-col gap-3 pointer-events-none">
        {toasts.map(toast => (
          <div 
            key={toast.id}
            className="pointer-events-auto bg-slate-900 border border-slate-800 rounded-xl px-5 py-4 shadow-2xl flex items-center gap-3 animate-in slide-in-from-right-full duration-300"
          >
            <div className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <Sparkles size={14} className="text-emerald-500" />
            </div>
            <p className="text-sm font-medium text-slate-200">{toast.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

const SuggestionChip = ({ label, onClick }: { label: string, onClick: () => void }) => (
  <button 
    onClick={onClick}
    className="px-4 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-400 hover:text-white hover:border-slate-600 transition-all"
  >
    {label}
  </button>
);

export default App;
