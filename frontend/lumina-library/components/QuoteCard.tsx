
import React, { useState } from 'react';
import { Quote } from '../types';
import { Star, Edit3, Trash2, Share2, Copy, Bookmark, MoreHorizontal } from 'lucide-react';

interface QuoteCardProps {
  quote: Quote;
  onEdit: (quote: Quote) => void;
  onDelete: (id: string) => void;
  onToggleFavorite: (id: string) => void;
  onTagClick: (tag: string) => void;
}

export const QuoteCard: React.FC<QuoteCardProps> = ({ quote, onEdit, onDelete, onToggleFavorite, onTagClick }) => {
  const [showNotes, setShowNotes] = useState(false);
  
  const handleCopy = () => {
    navigator.clipboard.writeText(`"${quote.content}" — ${quote.bookTitle} by ${quote.bookAuthor}`);
    // Assume parent handles the toast
  };

  return (
    <div className="group relative glass bg-slate-900/40 rounded-3xl p-8 border border-slate-800/50 hover:border-indigo-500/50 transition-all duration-500 hover:shadow-2xl hover:shadow-indigo-500/5">
      
      {/* Quote Mark */}
      <div className="absolute -top-4 -left-2 text-7xl text-indigo-500/10 font-serif pointer-events-none select-none">“</div>
      
      <div className="relative space-y-6">
        {/* Quote Content */}
        <p className="text-xl md:text-2xl font-medium text-slate-100 leading-relaxed italic font-serif">
          {quote.content}
        </p>

        {/* Book Info */}
        <div className="flex items-start gap-4 pt-4 border-t border-slate-800/50">
          {quote.bookCover ? (
            <img src={quote.bookCover} alt={quote.bookTitle} className="w-12 h-18 rounded-lg shadow-lg object-cover" />
          ) : (
            <div className="w-12 h-18 bg-slate-800 rounded-lg flex items-center justify-center">
              <Bookmark className="text-slate-600" size={20} />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <h4 className="text-white font-bold truncate text-lg">{quote.bookTitle}</h4>
            <p className="text-indigo-400 font-medium truncate">{quote.bookAuthor}</p>
            <div className="flex gap-3 mt-1 text-xs text-slate-500 font-bold uppercase tracking-wider">
              {quote.pageNumber && <span>Page {quote.pageNumber}</span>}
              {quote.chapter && <span className="truncate max-w-[150px]">{quote.chapter}</span>}
            </div>
          </div>
        </div>

        {/* Tags */}
        {quote.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {quote.tags.map((tag, i) => (
              <button 
                key={i} 
                onClick={() => onTagClick(tag)}
                className="px-3 py-1 rounded-full bg-slate-800/50 border border-slate-700 text-xs font-semibold text-slate-400 hover:text-indigo-400 hover:border-indigo-500/30 transition-all"
              >
                #{tag}
              </button>
            ))}
          </div>
        )}

        {/* Notes Toggle */}
        {quote.notes && (
          <div className="pt-2">
            <button 
              onClick={() => setShowNotes(!showNotes)}
              className="text-xs font-bold text-slate-500 flex items-center gap-1.5 hover:text-slate-300 transition-colors"
            >
              <MoreHorizontal size={14} />
              {showNotes ? 'Hide personal notes' : 'Read personal notes'}
            </button>
            {showNotes && (
              <p className="mt-3 p-4 rounded-xl bg-slate-950/50 border border-slate-800 text-slate-400 text-sm leading-relaxed animate-in slide-in-from-top-2">
                {quote.notes}
              </p>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-4">
          <div className="flex items-center gap-1">
            <button 
              onClick={() => onToggleFavorite(quote.id)}
              className={`p-2 rounded-full transition-all ${quote.isFavorite ? 'text-amber-400 bg-amber-400/10' : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800'}`}
            >
              <Star size={20} fill={quote.isFavorite ? 'currentColor' : 'none'} />
            </button>
            <button 
              onClick={handleCopy}
              className="p-2 rounded-full text-slate-500 hover:text-indigo-400 hover:bg-slate-800 transition-all"
            >
              <Copy size={20} />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button 
              onClick={() => onEdit(quote)}
              className="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white hover:bg-slate-800 transition-all flex items-center gap-2"
            >
              <Edit3 size={14} /> Edit
            </button>
            <button 
              onClick={() => onDelete(quote.id)}
              className="px-4 py-2 rounded-xl text-xs font-bold text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-all flex items-center gap-2"
            >
              <Trash2 size={14} /> Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
