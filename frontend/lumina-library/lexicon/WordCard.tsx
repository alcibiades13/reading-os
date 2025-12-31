
import React from 'react';
import { VocabularyWord, MasteryLevel } from '../types';
import { Star, Edit3, Trash2, Bookmark, ExternalLink } from 'lucide-react';

interface WordCardProps {
  word: VocabularyWord;
  onEdit: (word: VocabularyWord) => void;
  onDelete: (id: string) => void;
  onUpdateMastery: (id: string, level: MasteryLevel) => void;
}

export const WordCard: React.FC<WordCardProps> = ({ word, onEdit, onDelete, onUpdateMastery }) => {
  const masteryConfig: Record<MasteryLevel, { label: string, color: string }> = {
    new: { label: 'New', color: 'bg-indigo-500' },
    learning: { label: 'Learning', color: 'bg-amber-500' },
    mastered: { label: 'Mastered', color: 'bg-emerald-500' }
  };

  return (
    <div className="group glass bg-slate-900/40 rounded-2xl p-6 border border-slate-800/50 hover:border-emerald-500/30 transition-all duration-300">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-2xl font-serif font-black text-white group-hover:text-emerald-400 transition-colors">
            {word.word}
          </h3>
          <div className="flex items-center gap-2 mt-2">
            <span className={`px-2 py-0.5 rounded text-[8px] font-black uppercase text-white tracking-widest ${masteryConfig[word.mastery].color}`}>
              {masteryConfig[word.mastery].label}
            </span>
            {word.isFavorite && <Star size={12} className="text-amber-400" fill="currentColor" />}
          </div>
        </div>
        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button onClick={() => onEdit(word)} className="p-2 rounded-lg hover:bg-slate-800 text-slate-500 hover:text-white transition-colors">
            <Edit3 size={14} />
          </button>
          <button onClick={() => onDelete(word.id)} className="p-2 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      <p className="text-sm text-slate-400 line-clamp-2 italic mb-4">
        "{word.context || "No context provided."}"
      </p>

      <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500 truncate max-w-[150px]">
          <Bookmark size={12} />
          <span className="truncate">{word.bookTitle || 'Manual'}</span>
        </div>
        <div className="text-[10px] font-black text-slate-600 uppercase tracking-widest">
          {word.reviewCount} Reviews
        </div>
      </div>
    </div>
  );
};
