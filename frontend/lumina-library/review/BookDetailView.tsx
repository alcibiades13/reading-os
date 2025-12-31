
import React, { useState, useEffect, useMemo } from 'react';
import { GoogleBook, LibraryStatus, Quote } from '../types';
import { StarRating } from '../components/StarRating';
import { QuoteCard } from '../components/QuoteCard';
import { QuoteModal } from '../components/QuoteModal';
import { getQuotes, saveQuote, deleteQuote, toggleFavorite } from '../services/quotesService';
import { 
  X, BookOpen, Calendar, Globe, Hash, Building2, 
  Bookmark, PlayCircle, CheckCircle, Heart, Share2, 
  Plus, ChevronRight, MessageSquare, Users, Sparkles,
  ArrowLeft, Star, Edit3
} from 'lucide-react';

interface BookDetailViewProps {
  book: GoogleBook;
  onBack: () => void;
  onToast: (msg: string) => void;
  onWriteReview?: () => void;
}

export const BookDetailView: React.FC<BookDetailViewProps> = ({ book, onBack, onToast, onWriteReview }) => {
  // User Personal State
  const [isInLibrary, setIsInLibrary] = useState(false);
  const [status, setStatus] = useState<LibraryStatus>(null);
  const [personalRating, setPersonalRating] = useState(0);
  const [review, setReview] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [isFavorite, setIsFavorite] = useState(false);
  const [showFullDesc, setShowFullDesc] = useState(false);

  // Quotes State
  const [bookQuotes, setBookQuotes] = useState<Quote[]>([]);
  const [isQuoteModalOpen, setIsQuoteModalOpen] = useState(false);

  const { volumeInfo } = book;
  const totalPages = volumeInfo.pageCount || 100;
  const progressPercent = Math.min(100, Math.round((currentPage / totalPages) * 100));

  useEffect(() => {
    // Simulacija dohvatanja citata za ovu knjigu
    const allQuotes = getQuotes();
    setBookQuotes(allQuotes.filter(q => q.bookTitle === volumeInfo.title));
    
    // Inicijalizacija personalnih podataka (u realnoj aplikaciji ovo ide sa API-ja)
    if (book.id === 'placeholder-id') { // Primer
      setIsInLibrary(true);
      setStatus('currently_reading');
      setPersonalRating(8.5);
      setCurrentPage(120);
    }
    
    window.scrollTo(0, 0);
  }, [book, volumeInfo.title]);

  const handleStatusChange = (newStatus: LibraryStatus) => {
    setStatus(newStatus);
    setIsInLibrary(true);
    onToast(`Status promenjen: ${newStatus?.replace('_', ' ')}`);
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
    onToast('Citat uspešno sačuvan!');
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
        Povratak na rezultate
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
            <MetaBox icon={<BookOpen size={18} />} label="Strana" value={volumeInfo.pageCount?.toString() || '---'} />
            <MetaBox icon={<Globe size={18} />} label="Jezik" value={volumeInfo.language?.toUpperCase() || '---'} />
            <MetaBox icon={<Calendar size={18} />} label="Izdanje" value={volumeInfo.publishedDate?.split('-')[0] || '---'} />
            <MetaBox icon={<Hash size={18} />} label="Format" value="Meki povez" />
          </div>

          {/* Publisher Info */}
          <div className="p-6 rounded-2xl glass border-slate-800/50 space-y-4">
            <div className="flex items-center gap-3 text-slate-400">
              <Building2 size={18} />
              <span className="text-xs font-bold uppercase tracking-widest">Izdavač</span>
            </div>
            <p className="text-slate-100 font-semibold">{volumeInfo.publisher || 'Nepoznat izdavač'}</p>
            <div className="pt-4 border-t border-slate-800/50">
              <span className="text-[10px] text-slate-500 font-bold uppercase block mb-1">ISBN-13</span>
              <code className="text-xs text-indigo-400">{volumeInfo.industryIdentifiers?.[0]?.identifier || 'N/A'}</code>
            </div>
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
              od <span className="text-indigo-400 hover:underline cursor-pointer">{volumeInfo.authors?.join(', ')}</span>
            </p>
            
            <div className="flex items-center gap-4 mt-6">
              <StarRating rating={volumeInfo.averageRating || 0} size={24} />
              <span className="text-slate-500 text-sm">({volumeInfo.ratingsCount || 0} ocena na Google Books)</span>
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
                  <h2 className="text-xl font-bold text-white mb-1">Moje Čitanje</h2>
                  <p className="text-slate-400 text-sm">Upravljaj svojim napretkom i utiscima</p>
                </div>
                
                <div className="flex items-center gap-3">
                  {!isInLibrary ? (
                    <button 
                      onClick={() => handleStatusChange('want_to_read')}
                      className="px-8 py-4 rounded-xl bg-indigo-500 text-white font-bold shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 transition-all flex items-center gap-3"
                    >
                      <Plus size={20} />
                      Dodaj u Biblioteku
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
                        <option value="want_to_read">Želim da čitam</option>
                        <option value="currently_reading">Trenutno čitam</option>
                        <option value="read">Pročitano</option>
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
                      <label className="text-xs font-bold text-slate-500 uppercase tracking-widest block mb-4">Moja Ocena</label>
                      <StarRating 
                        rating={personalRating} 
                        editable={true} 
                        onChange={setPersonalRating} 
                        size={28} 
                      />
                      <p className="text-[10px] text-slate-500 mt-2">Jedan klik za celu, dvostruki klik za pola zvezdice</p>
                    </div>
                    <div>
                      <label className="text-xs font-bold text-slate-500 uppercase tracking-widest block mb-3">Moj Review</label>
                      <button 
                        onClick={onWriteReview}
                        className="w-full py-6 rounded-2xl glass border-slate-800 hover:border-indigo-500/50 hover:bg-indigo-500/5 transition-all flex flex-col items-center justify-center gap-2 group"
                      >
                        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 group-hover:border-indigo-500/30 group-hover:text-indigo-400 transition-all">
                          <Edit3 size={24} />
                        </div>
                        <span className="text-sm font-bold text-slate-300 group-hover:text-white transition-colors">Piši Detaljan Review</span>
                        <span className="text-[10px] uppercase font-black tracking-widest text-slate-600">Otvori Art-Editor</span>
                      </button>
                    </div>
                  </div>

                  {/* Progress Tracking */}
                  <div className="space-y-6">
                    {status === 'currently_reading' && (
                      <div className="p-6 rounded-2xl bg-slate-950/50 border border-slate-800">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-widest block mb-4">Napredak Čitanja</label>
                        <div className="flex items-end justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <input 
                              type="number" 
                              value={currentPage}
                              onChange={(e) => setCurrentPage(parseInt(e.target.value) || 0)}
                              className="w-16 bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-center font-bold text-indigo-400 outline-none"
                            />
                            <span className="text-slate-500 text-sm">/ {totalPages} strana</span>
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
                    
                    <div className="space-y-4">
                       <button className="w-full py-4 rounded-xl border border-slate-700 text-slate-300 font-bold hover:bg-slate-800 transition-all flex items-center justify-center gap-3">
                         <Share2 size={18} />
                         Podeli napredak
                       </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Description */}
          <section className="space-y-4">
            <h2 className="text-sm font-bold text-slate-500 uppercase tracking-[0.2em]">O Knjizi</h2>
            <div className={`text-slate-300 leading-relaxed space-y-4 relative ${!showFullDesc ? 'max-h-48 overflow-hidden' : ''}`}>
              <div 
                dangerouslySetInnerHTML={{ __html: volumeInfo.description || 'Opis nije dostupan.' }}
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
                {showFullDesc ? 'Prikaži manje' : 'Pročitaj više'}
              </button>
            )}
          </section>

          {/* Quotes Section */}
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-500 uppercase tracking-[0.2em]">Moji Citati</h2>
              <button 
                onClick={() => setIsQuoteModalOpen(true)}
                className="flex items-center gap-2 text-indigo-400 font-bold text-sm hover:text-indigo-300 transition-colors"
              >
                <Plus size={16} /> Dodaj Citat
              </button>
            </div>

            {bookQuotes.length > 0 ? (
              <div className="grid grid-cols-1 gap-6">
                {bookQuotes.slice(0, 3).map(quote => (
                  <QuoteCard 
                    key={quote.id}
                    quote={quote}
                    onEdit={() => {}}
                    onDelete={() => {}}
                    onToggleFavorite={() => toggleFavorite(quote.id)}
                    onTagClick={() => {}}
                  />
                ))}
                {bookQuotes.length > 3 && (
                  <button className="w-full py-4 rounded-2xl bg-slate-900 border border-slate-800 text-slate-400 font-bold hover:text-white hover:bg-slate-800 transition-all">
                    Vidi svih {bookQuotes.length} citata iz ove knjige
                  </button>
                )}
              </div>
            ) : (
              <div className="p-12 rounded-3xl border-2 border-dashed border-slate-800 flex flex-col items-center text-center">
                <div className="w-12 h-12 rounded-full bg-slate-900 flex items-center justify-center mb-4 text-slate-600">
                  <Bookmark size={24} />
                </div>
                <p className="text-slate-500 text-sm italic">Još uvek nisi sačuvao nijedan citat iz ove knjige.</p>
              </div>
            )}
          </section>

          {/* Social - Community */}
          <section className="space-y-6 pt-12 border-t border-slate-900">
            <h2 className="text-sm font-bold text-slate-500 uppercase tracking-[0.2em] flex items-center gap-3">
              <Users size={16} /> Aktivnost Zajednice
            </h2>
            
            <div className="flex flex-col gap-4">
              <FriendActivity user="Ana Kostić" status="Pročitano" rating={9.0} review="Ovo je knjiga koja menja pogled na svet!" />
              <FriendActivity user="Marko Jovanović" status="Čita trenutno" rating={0} review="Tek sam počeo, ali obećava..." />
              
              <div className="p-6 rounded-2xl bg-slate-900/30 border border-slate-800/50 flex items-center justify-between">
                <p className="text-slate-400 text-sm">Budi prvi od svojih prijatelja koji će preporučiti ovu knjigu!</p>
                <button className="text-indigo-400 font-bold text-sm hover:underline">Pozovi prijatelje</button>
              </div>
            </div>
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

const FriendActivity = ({ user, status, rating, review }: { user: string, status: string, rating: number, review: string }) => (
  <div className="flex gap-4 p-4 rounded-2xl hover:bg-slate-900/50 transition-colors border border-transparent hover:border-slate-800">
    <div className="w-10 h-10 rounded-full bg-slate-800 flex-shrink-0 border border-slate-700 flex items-center justify-center font-bold text-slate-400 text-xs">
      {user.split(' ').map(n => n[0]).join('')}
    </div>
    <div className="flex-1 min-w-0">
      <div className="flex items-center justify-between mb-1">
        <span className="font-bold text-white text-sm">{user}</span>
        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-500 font-bold uppercase">{status}</span>
      </div>
      {rating > 0 && (
        <div className="flex items-center gap-1 mb-2">
          <Star size={10} className="text-amber-400 fill-current" />
          <span className="text-[10px] font-bold text-amber-400">{rating.toFixed(1)}</span>
        </div>
      )}
      <p className="text-xs text-slate-400 line-clamp-2 italic">"{review}"</p>
    </div>
  </div>
);
