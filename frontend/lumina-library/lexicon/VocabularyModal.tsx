
import React, { useState, useEffect, useRef } from 'react';
import { GoogleBook, VocabularyWord } from '../types';
import { X, Save, Type, Book, AlignLeft, Hash, Star, Globe, Lock, Plus } from 'lucide-react';

interface VocabularyModalProps {
  word?: VocabularyWord | null;
  initialBook?: GoogleBook | null;
  onClose: () => void;
  onSave: (word: Partial<VocabularyWord>, addAnother: boolean) => void;
}

export const VocabularyModal: React.FC<VocabularyModalProps> = ({ word, initialBook, onClose, onSave }) => {
  const [wordText, setWordText] = useState(word?.word || '');
  const [definition, setDefinition] = useState(word?.definition || '');
  const [context, setContext] = useState(word?.context || '');
  const [bookTitle, setBookTitle] = useState(word?.bookTitle || initialBook?.volumeInfo.title || '');
  const [bookAuthor, setBookAuthor] = useState(word?.bookAuthor || initialBook?.volumeInfo.authors?.[0] || '');
  const [pageNumber, setPageNumber] = useState<number | undefined>(word?.pageNumber);
  const [isFavorite, setIsFavorite] = useState(word?.isFavorite || false);
  const [isPublic, setIsPublic] = useState<boolean>(word?.isPublic ?? true);
  const [tagsInput, setTagsInput] = useState(word?.tags.join(', ') || '');

  const wordRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    wordRef.current?.focus();
  }, []);

  const handleSubmit = (addAnother: boolean = false) => {
    if (!wordText.trim()) return;

    onSave({
      id: word?.id,
      word: wordText,
      definition,
      context,
      bookTitle,
      bookAuthor,
      bookId: word?.bookId || initialBook?.id,
      pageNumber,
      isFavorite,
      isPublic,
      tags: tagsInput.split(',').map(t => t.trim()).filter(t => t !== '')
    }, addAnother);

    if (addAnother) {
      setWordText('');
      setDefinition('');
      setContext('');
      setTagsInput('');
      wordRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit(false);
    }
    if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-slate-950/90 backdrop-blur-md animate-in fade-in duration-300" onKeyDown={handleKeyDown}>
      <div className="relative w-full max-w-2xl glass rounded-[2.5rem] overflow-hidden shadow-2xl flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-300">
        
        <div className="flex items-center justify-between p-8 border-b border-slate-800 bg-slate-900/50">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shadow-lg shadow-emerald-500/5">
              <Type size={24} className="text-emerald-400" />
            </div>
            <div>
              <h2 className="text-xl font-black text-white">{word ? 'Edit Word' : 'Capture Vocabulary'}</h2>
              <p className="text-[10px] uppercase font-black tracking-widest text-slate-500">Add to your lexicon</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2.5 rounded-full hover:bg-slate-800 text-slate-400 transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-10 custom-scrollbar space-y-10">
          {/* Main Word */}
          <div className="space-y-4">
            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
              <Type size={14} className="text-emerald-400" /> The Word
            </label>
            <input
              ref={wordRef}
              required
              type="text"
              value={wordText}
              onChange={(e) => setWordText(e.target.value)}
              placeholder="e.g. Mellifluous"
              className="w-full bg-slate-800/20 border-2 border-slate-800 rounded-2xl px-6 py-4 text-3xl font-serif text-white placeholder-slate-700 focus:border-emerald-500/50 transition-all outline-none"
            />
          </div>

          {/* Context & Definition */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
                <AlignLeft size={14} /> Context / Sentence
              </label>
              <textarea
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="Where did you find it?"
                className="w-full h-28 bg-slate-800/20 border-2 border-slate-800 rounded-2xl p-4 text-sm text-slate-300 placeholder-slate-700 focus:border-emerald-500/50 transition-all outline-none resize-none"
              />
            </div>
            <div className="space-y-4">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
                <Plus size={14} /> Your Definition
              </label>
              <textarea
                value={definition}
                onChange={(e) => setDefinition(e.target.value)}
                placeholder="What does it mean to you?"
                className="w-full h-28 bg-slate-800/20 border-2 border-slate-800 rounded-2xl p-4 text-sm text-slate-300 placeholder-slate-700 focus:border-emerald-500/50 transition-all outline-none resize-none"
              />
            </div>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
                <Book size={14} /> Source Book
              </label>
              <input
                type="text"
                value={bookTitle}
                onChange={(e) => setBookTitle(e.target.value)}
                placeholder="Title..."
                className="w-full bg-slate-800/20 border-2 border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 focus:border-emerald-500/50 transition-all outline-none"
              />
            </div>
            <div className="space-y-4">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
                <Hash size={14} /> Page
              </label>
              <input
                type="number"
                value={pageNumber || ''}
                onChange={(e) => setPageNumber(parseInt(e.target.value) || undefined)}
                placeholder="Page number..."
                className="w-full bg-slate-800/20 border-2 border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 focus:border-emerald-500/50 transition-all outline-none"
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-4">
            <button
              type="button"
              onClick={() => setIsFavorite(!isFavorite)}
              className={`flex items-center gap-3 px-6 py-3 rounded-xl border-2 transition-all ${
                isFavorite ? 'border-emerald-500 bg-emerald-500/10 text-emerald-400' : 'border-slate-800 text-slate-600'
              }`}
            >
              <Star size={18} fill={isFavorite ? 'currentColor' : 'none'} />
              <span className="text-xs font-black uppercase tracking-widest">Favorite</span>
            </button>
            <button
              type="button"
              onClick={() => setIsPublic(!isPublic)}
              className={`flex items-center gap-3 px-6 py-3 rounded-xl border-2 transition-all ${
                isPublic ? 'border-sky-500 bg-sky-500/10 text-sky-400' : 'border-slate-800 text-slate-600'
              }`}
            >
              {isPublic ? <Globe size={18} /> : <Lock size={18} />}
              <span className="text-xs font-black uppercase tracking-widest">{isPublic ? 'Public' : 'Private'}</span>
            </button>
          </div>
        </div>

        <div className="p-8 border-t border-slate-800 bg-slate-900/50 flex flex-wrap gap-4">
          <button 
            onClick={() => handleSubmit(true)}
            type="button" 
            className="px-6 py-4 rounded-2xl border border-slate-700 text-slate-300 font-black text-xs uppercase tracking-widest hover:bg-slate-800 transition-all"
          >
            Save & Add Another
          </button>
          <div className="flex-1 min-w-0" />
          <button 
            onClick={() => handleSubmit(false)} 
            type="button" 
            className="flex items-center gap-3 px-10 py-4 rounded-2xl bg-emerald-500 text-white font-black text-xs uppercase tracking-widest shadow-xl shadow-emerald-500/20 hover:bg-emerald-400 active:scale-95 transition-all"
          >
            <Save size={20} />
            Capture Entry
          </button>
        </div>
      </div>
    </div>
  );
};
