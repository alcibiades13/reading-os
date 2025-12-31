
import React, { useState } from 'react';
import { GoogleBook, LibraryStatus, ImportPayload } from '../types';
import { 
  X, Star, BookOpen, Calendar, Globe, Hash, Building2, 
  Bookmark, PlayCircle, CheckCircle, Lightbulb, Library, Check, ExternalLink
} from 'lucide-react';

interface BookPreviewModalProps {
  book: GoogleBook;
  onClose: () => void;
  onImport: (payload: ImportPayload) => void;
  onOpenDetail?: () => void; // Nova opcija
}

export const BookPreviewModal: React.FC<BookPreviewModalProps> = ({ book, onClose, onImport, onOpenDetail }) => {
  const [status, setStatus] = useState<LibraryStatus>(null);
  const [rating, setRating] = useState<number | null>(null);
  const [isImporting, setIsImporting] = useState(false);

  const { volumeInfo } = book;
  const coverUrl = volumeInfo.imageLinks?.large || volumeInfo.imageLinks?.thumbnail?.replace('http:', 'https:') || 
    `https://via.placeholder.com/600x900/1E293B/64748B?text=${encodeURIComponent(volumeInfo.title)}`;

  const handleStatusToggle = (newStatus: LibraryStatus) => {
    setStatus(current => current === newStatus ? null : newStatus);
    if (newStatus !== 'read') setRating(null);
  };

  const handleImport = async () => {
    setIsImporting(true);
    const payload: ImportPayload = {
      book,
      addToLibrary: status !== null,
      libraryData: {
        status,
        rating
      }
    };
    
    // Simulate API call
    await new Promise(r => setTimeout(r, 1200));
    onImport(payload);
    setIsImporting(false);
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-6 bg-slate-950/90 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="relative w-full max-w-5xl h-[90vh] glass rounded-3xl overflow-hidden shadow-2xl flex flex-col md:flex-row animate-in zoom-in-95 duration-300">
        
        {/* Close Button */}
        <button 
          onClick={onClose}
          className="absolute top-6 right-6 z-20 p-2 rounded-full bg-slate-900/50 hover:bg-slate-800 text-slate-300 transition-colors"
        >
          <X size={20} />
        </button>

        {/* Left Column - Cover & Quick Stats */}
        <div className="w-full md:w-[40%] bg-slate-900/50 p-8 flex flex-col items-center overflow-y-auto custom-scrollbar border-r border-slate-700/30">
          <div className="relative w-full max-w-[280px] aspect-[2/3] rounded-2xl overflow-hidden shadow-2xl ring-1 ring-white/10 group cursor-pointer" onClick={onOpenDetail}>
            <img src={coverUrl} alt={volumeInfo.title} className="w-full h-full object-cover" />
            <div className="absolute inset-0 shadow-[inset_0_0_80px_rgba(0,0,0,0.4)]" />
            <div className="absolute inset-0 bg-indigo-500/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <ExternalLink size={32} className="text-white" />
            </div>
          </div>

          <div className="w-full mt-8 space-y-4">
            <button 
              onClick={onOpenDetail}
              className="w-full flex items-center justify-center gap-2 text-indigo-400 font-bold text-sm hover:underline py-2"
            >
              Vidi punu stranicu <ExternalLink size={14} />
            </button>

            <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
              <Star className="text-amber-400" size={20} fill="currentColor" />
              <div>
                <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Average Rating</p>
                <p className="text-slate-100 font-semibold">{volumeInfo.averageRating ? `${volumeInfo.averageRating}/5` : 'N/A'}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <StatItem icon={<BookOpen size={16} />} label="Pages" value={volumeInfo.pageCount?.toString() || 'N/A'} />
              <StatItem icon={<Globe size={16} />} label="Language" value={volumeInfo.language?.toUpperCase() || 'N/A'} />
            </div>
          </div>
        </div>

        {/* Right Column - Details & Actions */}
        <div className="w-full md:w-[60%] flex flex-col h-full bg-slate-900/20">
          <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
            <header className="mb-8">
              <h1 className="text-3xl md:text-4xl font-bold text-white leading-tight">{volumeInfo.title}</h1>
              <p className="text-xl text-indigo-400/80 mt-2 font-medium">{volumeInfo.authors?.join(', ')}</p>
            </header>

            <section className="mb-8">
              <h2 className="text-sm font-bold text-slate-500 uppercase tracking-[0.2em] mb-4">Description</h2>
              <div 
                className="text-slate-300 leading-relaxed text-sm line-clamp-6"
                dangerouslySetInnerHTML={{ __html: volumeInfo.description || 'No description available for this title.' }}
              />
              <button onClick={onOpenDetail} className="text-indigo-400 text-xs font-bold mt-2 hover:underline">Saznaj više...</button>
            </section>

            {/* Import Logic */}
            <section className="p-6 rounded-2xl bg-slate-800/40 border border-slate-700/50">
              <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                Dodaj u biblioteku?
              </h3>
              
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <ActionCard 
                  selected={status === 'want_to_read'}
                  onClick={() => handleStatusToggle('want_to_read')}
                  icon={<Bookmark size={20} />}
                  label="Planiram"
                />
                <ActionCard 
                  selected={status === 'currently_reading'}
                  onClick={() => handleStatusToggle('currently_reading')}
                  icon={<PlayCircle size={20} />}
                  label="Čitam"
                />
                <ActionCard 
                  selected={status === 'read'}
                  onClick={() => handleStatusToggle('read')}
                  icon={<CheckCircle size={20} />}
                  label="Pročitano"
                />
              </div>

              <div className="mt-6 flex items-start gap-3 text-slate-500 bg-slate-900/40 p-3 rounded-xl">
                <Lightbulb size={16} className="shrink-0 mt-0.5" />
                <p className="text-xs italic leading-relaxed">
                  Izaberi status da dodaš knjigu u svoju privatnu arhivu.
                </p>
              </div>
            </section>
          </div>

          {/* Footer Actions */}
          <div className="p-8 border-t border-slate-700/30 bg-slate-900/50 flex flex-col sm:flex-row gap-4">
            <button 
              onClick={onClose}
              className="flex-1 px-6 py-4 rounded-xl border border-slate-700 text-slate-300 font-semibold hover:bg-slate-800 transition-colors"
            >
              Otkaži
            </button>
            <button 
              disabled={isImporting}
              onClick={handleImport}
              className={`flex-[2] px-6 py-4 rounded-xl bg-indigo-500 text-white font-bold flex items-center justify-center gap-3 shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isImporting ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Uvoz...
                </>
              ) : (
                <>
                  <Library size={20} />
                  Sačuvaj u biblioteku
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const StatItem = ({ icon, label, value }: { icon: React.ReactNode, label: string, value: string }) => (
  <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
    <div className="flex items-center gap-2 text-slate-500 mb-1">
      {icon}
      <span className="text-[10px] font-bold uppercase tracking-wider">{label}</span>
    </div>
    <p className="text-slate-200 font-semibold truncate text-sm">{value}</p>
  </div>
);

const ActionCard = ({ selected, onClick, icon, label }: { selected: boolean, onClick: () => void, icon: React.ReactNode, label: string }) => (
  <button 
    onClick={onClick}
    className={`p-4 rounded-xl flex items-center gap-3 border-2 transition-all duration-300 ${
      selected 
      ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400 shadow-[0_0_20px_rgba(99,102,241,0.1)]' 
      : 'border-slate-700 bg-slate-800/20 text-slate-400 hover:border-slate-500'
    }`}
  >
    <span className={`transition-transform duration-300 ${selected ? 'scale-110' : ''}`}>{icon}</span>
    <span className="text-sm font-semibold">{label}</span>
    {selected && <Check size={16} className="ml-auto" />}
  </button>
);
