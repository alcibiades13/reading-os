
import React, { useState, useEffect, useMemo } from 'react';
import { GoogleBook, LibraryStatus, Quote, StudyNote } from '../types';
import { StarRating } from '../components/StarRating';
import { QuoteCard } from '../components/QuoteCard';
import { QuoteModal } from '../components/QuoteModal';
import { StudyNoteCard } from '../components/StudyNoteCard';
import { getQuotes, saveQuote, deleteQuote, toggleFavorite } from '../services/quotesService';
import { getVocabulary } from '../services/vocabularyService';
import { getStudyNotes, deleteStudyNote } from '../services/studyService';
import { 
  X, BookOpen, Calendar, Globe, Hash, Building2, 
  Bookmark, PlayCircle, CheckCircle, Heart, Share2, 
  Plus, ChevronRight, MessageSquare, Users, Sparkles,
  ArrowLeft, Star, Edit3, Brain, Quote as QuoteIcon,
  Maximize2, LayoutGrid
} from 'lucide-react';

interface BookDetailViewProps {
  book: GoogleBook;
  onBack: () => void;
  onToast: (msg: string) => void;
  onWriteReview?: () => void;
  onAddWord?: () => void;
  onEnterStudyMode?: () => void;
}

export const BookDetailView: React.FC<BookDetailViewProps> = ({ 
  book, onBack, onToast, onWriteReview, onAddWord, onEnterStudyMode 
}) => {
  // User Personal State
  const [isInLibrary, setIsInLibrary] = useState(false);
  const [status, setStatus] = useState<LibraryStatus>(null);
  const [personalRating, setPersonalRating] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [isFavorite, setIsFavorite] = useState(false);
  const [showFullDesc, setShowFullDesc] = useState(false);
  const [activeSubTab, setActiveSubTab] = useState<'quotes' | 'study'>('quotes');

  // Content State
  const [bookQuotes, setBookQuotes] = useState<Quote[]>([]);
  const [studyNotes, setStudyNotes] = useState<StudyNote[]>([]);
  const [vocabCount, setVocabCount] = useState(0);
  const [isQuoteModalOpen, setIsQuoteModalOpen] = useState(false);

  const { volumeInfo } = book;
  const totalPages = volumeInfo.pageCount || 100;
  const progressPercent = Math.min(100, Math.round((currentPage / totalPages) * 100));

  useEffect(() => {
    const allQuotes = getQuotes();
    setBookQuotes(allQuotes.filter(q => q.bookTitle === volumeInfo.title));
    
    setStudyNotes(getStudyNotes(book.id));

    const allVocab = getVocabulary();
    setVocabCount(allVocab.filter(v => v.bookTitle === volumeInfo.title).length);

    if (book.id === 'placeholder-id') { 
      setIsInLibrary(true);
      setStatus('currently_reading');
      setPersonalRating(8.5);
      setCurrentPage(120);
    }
    
    window.scrollTo(0, 0);
  }, [book.id, volumeInfo.title]);

  const handleStatusChange = (newStatus: LibraryStatus) => {
    setStatus(newStatus);
    setIsInLibrary(true);
    onToast(`Status changed: ${newStatus?.replace('_', ' ')}`);
  };

  const handleSaveQuote = (payload: any) => {
    saveQuote({
      ...payload,
      bookTitle: volumeInfo.title,
      bookAuthor: volumeInfo.authors?.[0] || 'Unknown',
      bookCover: volumeInfo.imageLinks?.thumbnail
    });
    setBookQuotes(getQuotes().filter(q => q.bookTitle === volumeInfo.title));
    setIsQuoteModalOpen(false);
    onToast('Insight preserved!');
  };

  const coverUrl = volumeInfo.imageLinks?.large || volumeInfo.imageLinks?.thumbnail?.replace('http:', 'https:') || 
    `https://via.placeholder.com/600x900/1E293B/64748B?text=${encodeURIComponent(volumeInfo.title)}`;

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* Back Button */}
      <button 
        onClick={onBack}
        className="flex items-center gap-2 text-slate-400 hover:text-indigo-400 mb-10 transition-colors font-bold group"
      >
        <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
        Return to results
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        
        {/* Left Column - Cover & Main Info */}
        <div className="lg:col-span-4 space-y-8">
          <div className="relative aspect-[2/3] w-full rounded-3xl overflow-hidden shadow-2xl ring-1 ring-white/10 group">
            <img src={coverUrl} alt={volumeInfo.title} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 to-transparent" />
            
            <button 
              onClick={() => setIsFavorite(!isFavorite)}
              className={`absolute top-6 right-6 p-4 rounded-full glass transition-all ${isFavorite ? 'text-rose-500 bg-rose-500/10 border-rose-500/30' : 'text-white hover:text-rose-400'}`}
            >
              <Heart size={24} fill={isFavorite ? 'currentColor' : 'none'} />
            </button>
          </div>

          {/* Quick Meta Grid */}
          <div className="grid grid-cols-2 gap-4">
            <MetaBox icon={<BookOpen size={18} />} label="Pages" value={volumeInfo.pageCount?.toString() || '---'} />
            <MetaBox icon={<Globe size={18} />} label="Language" value={volumeInfo.language?.toUpperCase() || '---'} />
            <MetaBox icon={<Brain size={18} className="text-emerald-400" />} label="Lexicon" value={`${vocabCount} words`} />
            <MetaBox icon={<QuoteIcon size={18} className="text-indigo-400" />} label="Insights" value={`${bookQuotes.length + studyNotes.length} ideas`} />
          </div>

          {/* Actions */}
          <div className="space-y-3">
             <button 
                onClick={onEnterStudyMode}
                className="w-full py-4 rounded-2xl bg-slate-900 border border-slate-800 text-indigo-400 font-black text-xs uppercase tracking-widest flex items-center justify-center gap-3 hover:bg-slate-800 transition-all group"
             >
                <Maximize2 size={16} className="group-hover:scale-110 transition-transform" />
                Enter Study Mode
             </button>
             <button 
                onClick={onAddWord}
                className="w-full py-4 rounded-2xl border border-emerald-500/30 bg-emerald-500/5 text-emerald-400 font-black text-xs uppercase tracking-widest hover:bg-emerald-500/10 transition-all flex items-center justify-center gap-3"
              >
                <Brain size={16} />
                Capture Word
              </button>
          </div>
        </div>

        {/* Right Column - Interaction & Content */}
        <div className="lg:col-span-8 space-y-12">
          
          {/* Header Info */}
          <section>
            <div className="flex flex-wrap gap-2 mb-6">
              {volumeInfo.categories?.map((cat, i) => (
                <span key={i} className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-bold">
                  {cat}
                </span>
              ))}
            </div>
            <h1 className="text-5xl font-black text-white leading-tight mb-4">{volumeInfo.title}</h1>
            <p className="text-2xl text-slate-400 font-medium">
              by <span className="text-indigo-400 hover:underline cursor-pointer">{volumeInfo.authors?.join(', ')}</span>
            </p>
            
            <div className="flex items-center gap-4 mt-6">
              <StarRating rating={volumeInfo.averageRating || 0} size={24} />
              <span className="text-slate-500 text-sm">({volumeInfo.ratingsCount || 0} Google ratings)</span>
            </div>
          </section>

          {/* My Reading - Interaction Hub */}
          <section className="p-8 rounded-3xl glass border-indigo-500/20 bg-indigo-500/5 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-10">
              <Sparkles size={120} className="text-indigo-500" />
            </div>

            <div className="relative z-10 space-y-8">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div>
                  <h2 className="text-xl font-bold text-white mb-1">My Progress</h2>
                  <p className="text-slate-400 text-sm">Command center for this title</p>
                </div>
                
                <div className="flex items-center gap-3">
                  {!isInLibrary ? (
                    <button 
                      onClick={() => handleStatusChange('want_to_read')}
                      className="px-8 py-4 rounded-xl bg-indigo-500 text-white font-bold shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 transition-all flex items-center gap-3"
                    >
                      <Plus size={20} />
                      Import to Library
                    </button>
                  ) : (
                    <div className="flex items-center gap-3">
                      <div className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider ${
                        status === 'read' ? 'bg-emerald-500/10 text-emerald-400' :
                        status === 'currently_reading' ? 'bg-sky-500/10 text-sky-400' :
                        'bg-slate-800 text-slate-400'
                      }`}>
                        {status?.replace('_', ' ')}
                      </div>
                      <select 
                        onChange={(e) => handleStatusChange(e.target.value as LibraryStatus)}
                        className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs font-bold text-slate-300 outline-none focus:border-indigo-500"
                        value={status || ''}
                      >
                        <option value="want_to_read">Plan to read</option>
                        <option value="currently_reading">Currently reading</option>
                        <option value="read">Finished</option>
                      </select>
                    </div>
                  )}
                </div>
              </div>

              {isInLibrary && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8 border-t border-slate-800/50">
                  {/* Rating & Review */}
                  <div className="space-y-6">
                    <div>
                      <label className="text-xs font-bold text-slate-500 uppercase tracking-widest block mb-4">My Rating</label>
                      <StarRating 
                        rating={personalRating} 
                        editable={true} 
                        onChange={setPersonalRating} 
                        size={28} 
                      />
                    </div>
                    <button 
                      onClick={onWriteReview}
                      className="w-full py-6 rounded-2xl glass border-slate-800 hover:border-indigo-500/50 hover:bg-indigo-500/5 transition-all flex flex-col items-center justify-center gap-2 group"
                    >
                      <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 group-hover:border-indigo-500/30 group-hover:text-indigo-400 transition-all">
                        <Edit3 size={24} />
                      </div>
                      <span className="text-sm font-bold text-slate-300 group-hover:text-white transition-colors">Write Reflection</span>
                    </button>
                  </div>

                  {/* Progress Tracking */}
                  <div className="space-y-6">
                    {status === 'currently_reading' && (
                      <div className="p-6 rounded-2xl bg-slate-950/50 border border-slate-800">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-widest block mb-4">Reading Progress</label>
                        <div className="flex items-end justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <input 
                              type="number" 
                              value={currentPage}
                              onChange={(e) => setCurrentPage(parseInt(e.target.value) || 0)}
                              className="w-16 bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-center font-bold text-indigo-400 outline-none"
                            />
                            <span className="text-slate-500 text-sm">/ {totalPages} pp</span>
                          </div>
                          <span className="text-indigo-400 font-black text-xl">{progressPercent}%</span>
                        </div>
                        <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-indigo-500 rounded-full shadow-[0_0_10px_rgba(99,102,241,0.5)] transition-all duration-1000"
                            style={{ width: `${progressPercent}%` }}
                          />
                        </div>
                      </div>
                    )}
                    
                    <button className="w-full py-4 rounded-xl border border-slate-700 text-slate-300 font-bold hover:bg-slate-800 transition-all flex items-center justify-center gap-3">
                       <Share2 size={18} />
                       Share Progress
                    </button>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* COMMONPLACE SECTION: Quotes & Study Notes */}
          <section className="space-y-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-slate-900 pb-4">
              <div className="flex items-center gap-2 p-1.5 bg-slate-900/50 rounded-2xl border border-slate-800 w-fit">
                <button 
                  onClick={() => setActiveSubTab('quotes')}
                  className={`flex items-center gap-2 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${activeSubTab === 'quotes' ? 'bg-indigo-500 text-white' : 'text-slate-500 hover:text-slate-300'}`}
                >
                  <QuoteIcon size={14} /> Main Quotes
                </button>
                <button 
                  onClick={() => setActiveSubTab('study')}
                  className={`flex items-center gap-2 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${activeSubTab === 'study' ? 'bg-emerald-500 text-white' : 'text-slate-500 hover:text-slate-300'}`}
                >
                  <Brain size={14} /> Study Archive
                </button>
              </div>

              {activeSubTab === 'quotes' ? (
                <button 
                  onClick={() => setIsQuoteModalOpen(true)}
                  className="flex items-center gap-2 text-indigo-400 font-bold text-xs uppercase tracking-widest hover:text-indigo-300"
                >
                  <Plus size={16} /> Capture Quote
                </button>
              ) : (
                <button 
                  onClick={onEnterStudyMode}
                  className="flex items-center gap-2 text-emerald-400 font-bold text-xs uppercase tracking-widest hover:text-emerald-300"
                >
                  <Maximize2 size={16} /> Open Study Mode
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 gap-6 animate-in fade-in slide-in-from-top-4 duration-500">
              {activeSubTab === 'quotes' ? (
                bookQuotes.length > 0 ? (
                  bookQuotes.map(quote => (
                    <QuoteCard 
                      key={quote.id}
                      quote={quote}
                      onEdit={() => {}}
                      onDelete={() => {}}
                      onToggleFavorite={() => toggleFavorite(quote.id)}
                      onTagClick={() => {}}
                    />
                  ))
                ) : (
                  <EmptyState icon={<QuoteIcon size={24} />} label="No quotes captured yet" />
                )
              ) : (
                studyNotes.length > 0 ? (
                  studyNotes.map(note => (
                    <StudyNoteCard 
                      key={note.id}
                      note={note}
                      onEdit={() => {}}
                      onDelete={(id) => { deleteStudyNote(id); setStudyNotes(getStudyNotes(book.id)); }}
                      onPromote={() => {}}
                    />
                  ))
                ) : (
                  <EmptyState icon={<Brain size={24} />} label="Study archive is empty" />
                )
              )}
            </div>
          </section>

          {/* Description */}
          <section className="space-y-4">
            <h2 className="text-sm font-bold text-slate-500 uppercase tracking-[0.2em]">About this Book</h2>
            <div className={`text-slate-300 leading-relaxed space-y-4 relative ${!showFullDesc ? 'max-h-48 overflow-hidden' : ''}`}>
              <div 
                dangerouslySetInnerHTML={{ __html: volumeInfo.description || 'Description not available.' }}
              />
              {!showFullDesc && volumeInfo.description && (
                <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-slate-950 to-transparent" />
              )}
            </div>
            {volumeInfo.description && volumeInfo.description.length > 300 && (
              <button 
                onClick={() => setShowFullDesc(!showFullDesc)}
                className="text-indigo-400 font-bold text-sm hover:text-indigo-300 transition-colors"
              >
                {showFullDesc ? 'Show less' : 'Read more'}
              </button>
            )}
          </section>
        </div>
      </div>

      {/* Quote Modal */}
      {isQuoteModalOpen && (
        <QuoteModal 
          quote={{
            id: '',
            bookId: book.id,
            bookTitle: volumeInfo.title,
            bookAuthor: volumeInfo.authors?.[0] || 'Unknown',
            content: '',
            isPublic: false,
            isFavorite: false,
            tags: [],
            createdAt: '',
            updatedAt: ''
          }}
          onClose={() => setIsQuoteModalOpen(false)}
          onSave={handleSaveQuote}
        />
      )}
    </div>
  );
};

const MetaBox = ({ icon, label, value }: { icon: any, label: string, value: string }) => (
  <div className="p-4 rounded-2xl glass border-slate-800/50">
    <div className="flex items-center gap-2 text-slate-500 mb-1">
      {icon}
      <span className="text-[10px] font-bold uppercase tracking-widest">{label}</span>
    </div>
    <p className="text-slate-100 font-bold truncate">{value}</p>
  </div>
);

const EmptyState = ({ icon, label }: { icon: any, label: string }) => (
  <div className="p-16 rounded-[2.5rem] border-2 border-dashed border-slate-900 flex flex-col items-center justify-center text-center">
    <div className="w-12 h-12 rounded-full bg-slate-900 flex items-center justify-center mb-4 text-slate-700">
      {icon}
    </div>
    <p className="text-slate-500 text-sm font-bold uppercase tracking-widest">{label}</p>
  </div>
);
