
import React from 'react';
import { StudyNote, StudyNoteType } from '../types';
import { 
  MessageSquare, HelpCircle, Lightbulb, Quote as QuoteIcon, 
  Trash2, Edit3, ArrowUpRight, Clock, Hash 
} from 'lucide-react';

interface StudyNoteCardProps {
  note: StudyNote;
  onEdit: (note: StudyNote) => void;
  onDelete: (id: string) => void;
  onPromote: (note: StudyNote) => void;
}

export const StudyNoteCard: React.FC<StudyNoteCardProps> = ({ note, onEdit, onDelete, onPromote }) => {
  const typeConfig: Record<StudyNoteType, { icon: any, color: string, label: string }> = {
    quote: { icon: <QuoteIcon size={14} />, color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20', label: 'Quote' },
    note: { icon: <MessageSquare size={14} />, color: 'text-slate-400 bg-slate-500/10 border-slate-500/20', label: 'Note' },
    question: { icon: <HelpCircle size={14} />, color: 'text-amber-400 bg-amber-500/10 border-amber-500/20', label: 'Question' },
    insight: { icon: <Lightbulb size={14} />, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20', label: 'Insight' }
  };

  const config = typeConfig[note.type];

  return (
    <div className="group glass bg-slate-900/40 rounded-2xl border border-slate-800/50 p-6 hover:border-slate-700 transition-all duration-300">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border ${config.color}`}>
            {config.icon}
            {config.label}
          </div>
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1">
            <Hash size={10} /> {note.reference}
          </span>
        </div>
        
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {note.type === 'quote' && (
            <button 
              onClick={() => onPromote(note)}
              title="Promote to Main Quote"
              className="p-2 rounded-lg hover:bg-indigo-500/10 text-slate-500 hover:text-indigo-400 transition-colors"
            >
              <ArrowUpRight size={14} />
            </button>
          )}
          <button onClick={() => onEdit(note)} className="p-2 rounded-lg hover:bg-slate-800 text-slate-500 hover:text-white transition-colors">
            <Edit3 size={14} />
          </button>
          <button onClick={() => onDelete(note.id)} className="p-2 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      <div className="font-serif text-lg text-slate-200 leading-relaxed mb-6 whitespace-pre-wrap">
        {note.content}
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {note.tags.map(tag => (
          <span key={tag} className="text-[10px] font-bold text-slate-500 hover:text-indigo-400 cursor-pointer transition-colors">#{tag}</span>
        ))}
      </div>

      <div className="pt-4 border-t border-slate-800/50 flex items-center justify-between text-[10px] text-slate-600 font-bold uppercase tracking-widest">
        <div className="flex items-center gap-1.5">
          <Clock size={12} />
          {new Date(note.createdAt).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
};
