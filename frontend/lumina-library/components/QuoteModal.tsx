
import React, { useState, useEffect } from 'react';
import { Quote, GoogleBook } from '../types';
import { X, Save, Bookmark, Hash, Type, AlignLeft, Star, Globe, Lock, Search } from 'lucide-react';

interface QuoteModalProps {
  quote?: Quote | null;
  onClose: () => void;
  onSave: (quote: any) => void;
}

export const QuoteModal: React.FC<QuoteModalProps> = ({ quote, onClose, onSave }) => {
  const [content, setContent] = useState(quote?.content || '');
  const [notes, setNotes] = useState(quote?.notes || '');
  const [bookTitle, setBookTitle] = useState(quote?.bookTitle || '');
  const [bookAuthor, setBookAuthor] = useState(quote?.bookAuthor || '');
  const [pageNumber, setPageNumber] = useState<number | undefined>(quote?.pageNumber);
  const [chapter, setChapter] = useState(quote?.chapter || '');
  const [isFavorite, setIsFavorite] = useState(quote?.isFavorite || false);
  const [isPublic, setIsPublic] = useState(quote?.isPublic || false);
  const [tagsInput, setTagsInput] = useState(quote?.tags.join(', ') || '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim() || !bookTitle.trim()) return;

    onSave({
      id: quote?.id,
      content,
      notes,
      bookTitle,
      bookAuthor,
      bookId: quote?.bookId || 'manual',
      pageNumber,
      chapter,
      isFavorite,
      isPublic,
      tags: tagsInput.split(',').map(t => t.trim()).filter(t => t !== ''),
      bookCover: quote?.bookCover
    });
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/90 backdrop-blur-md animate-in fade-in duration-300">
      <div className="relative w-full max-w-3xl glass rounded-3xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-300">
        
        <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-900/50">
          <h2 className="text-xl font-bold text-white flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Type size={18} className="text-white" />
            </div>
            {quote ? 'Edit Quote' : 'Capture New Insight'}
          </h2>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-slate-800 text-slate-400 transition-colors">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-8 custom-scrollbar space-y-8">
          {/* Quote Content */}
          <div className="space-y-3">
            <label className="text-sm font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
              <AlignLeft size={14} /> The Quote
            </label>
            <textarea
              required
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste the brilliant words here..."
              className="w-full h-40 bg-slate-800/30 border-2 border-slate-700 rounded-2xl p-4 text-lg text-slate-100 placeholder-slate-600 focus:border-indigo-500 focus:ring-0 transition-all outline-none resize-none"
            />
          </div>

          {/* Book Info Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <label className="text-sm font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
                <Bookmark size={14} /> Book Title
              </label>
              <input
                required
                type="text"
                value={bookTitle}
                onChange={(e) => setBookTitle(e.target.value)}
                placeholder="Which masterpiece is this from?"
                className="w-full bg-slate-800/30 border-2 border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:border-indigo-500 transition-all outline-none"
              />
            </div>
            <div className="space-y-3">
              <label className="text-sm font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
                <Hash size={14} /> Author
              </label>
              <input
                type="text"
                value={bookAuthor}
                onChange={(e) => setBookAuthor(e.target.value)}
                placeholder="The creative mind..."
                className="w-full bg-slate-800/30 border-2 border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:border-indigo-500 transition-all outline-none"
              />
            </div>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            <div className="space-y-3">
              <label className="text-sm font-bold text-slate-500 uppercase tracking-widest">Page</label>
              <input
                type="number"
                value={pageNumber || ''}
                onChange={(e) => setPageNumber(parseInt(e.target.value) || undefined)}
                placeholder="e.g. 142"
                className="w-full bg-slate-800/30 border-2 border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:border-indigo-500 transition-all outline-none"
              />
            </div>
            <div className="space-y-3">
              <label className="text-sm font-bold text-slate-500 uppercase tracking-widest">Chapter</label>
              <input
                type="text"
                value={chapter}
                onChange={(e) => setChapter(e.target.value)}
                placeholder="e.g. Chapter IV"
                className="w-full bg-slate-800/30 border-2 border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:border-indigo-500 transition-all outline-none"
              />
            </div>
            <div className="space-y-3 md:col-span-1 col-span-2">
              <label className="text-sm font-bold text-slate-500 uppercase tracking-widest">Tags</label>
              <input
                type="text"
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
                placeholder="philosophy, life, love"
                className="w-full bg-slate-800/30 border-2 border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:border-indigo-500 transition-all outline-none"
              />
            </div>
          </div>

          {/* Personal Notes */}
          <div className="space-y-3">
            <label className="text-sm font-bold text-slate-500 uppercase tracking-widest">Personal Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Why did this resonate with you?"
              className="w-full h-24 bg-slate-800/30 border-2 border-slate-700 rounded-xl p-4 text-slate-200 placeholder-slate-600 focus:border-indigo-500 transition-all outline-none resize-none"
            />
          </div>

          {/* Toggles */}
          <div className="flex flex-wrap gap-6 pt-4">
            <button
              type="button"
              onClick={() => setIsFavorite(!isFavorite)}
              className={`flex items-center gap-3 px-6 py-3 rounded-xl border-2 transition-all ${
                isFavorite ? 'border-amber-500 bg-amber-500/10 text-amber-400' : 'border-slate-700 text-slate-500'
              }`}
            >
              <Star size={18} fill={isFavorite ? 'currentColor' : 'none'} />
              <span className="font-bold">Favorite</span>
            </button>
            <button
              type="button"
              onClick={() => setIsPublic(!isPublic)}
              className={`flex items-center gap-3 px-6 py-3 rounded-xl border-2 transition-all ${
                isPublic ? 'border-sky-500 bg-sky-500/10 text-sky-400' : 'border-slate-700 text-slate-500'
              }`}
            >
              {isPublic ? <Globe size={18} /> : <Lock size={18} />}
              <span className="font-bold">{isPublic ? 'Public' : 'Private'}</span>
            </button>
          </div>
        </form>

        <div className="p-8 border-t border-slate-800 bg-slate-900/50 flex gap-4">
          <button onClick={onClose} type="button" className="flex-1 px-6 py-4 rounded-xl border border-slate-700 text-slate-300 font-bold hover:bg-slate-800 transition-all">
            Discard
          </button>
          <button 
            onClick={handleSubmit} 
            type="button" 
            className="flex-[2] px-6 py-4 rounded-xl bg-indigo-500 text-white font-bold flex items-center justify-center gap-3 shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 active:scale-[0.98] transition-all"
          >
            <Save size={20} />
            {quote ? 'Update Quote' : 'Save to Library'}
          </button>
        </div>
      </div>
    </div>
  );
};
