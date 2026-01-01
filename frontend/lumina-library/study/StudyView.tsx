
import React, { useState, useEffect, useMemo } from 'react';
import { GoogleBook, StudyNote, StudyNoteType } from '../types';
import { getStudyNotes, saveStudyNote, deleteStudyNote, getReferences } from '../services/studyService';
import { StudyNoteCard } from '../components/StudyNoteCard';
import { 
  ArrowLeft, Brain, Search, Filter, Plus, BookOpen, 
  ChevronRight, Hash, Quote as QuoteIcon, MessageSquare, 
  HelpCircle, Lightbulb, LayoutGrid, List, MoreVertical,
  Maximize2, Minimize2, Download
} from 'lucide-react';

interface StudyViewProps {
  book: GoogleBook;
  onBack: () => void;
  onToast: (msg: string) => void;
  onPromoteToQuote: (note: StudyNote) => void;
}

export const StudyView: React.FC<StudyViewProps> = ({ book, onBack, onToast, onPromoteToQuote }) => {
  const [notes, setNotes] = useState<StudyNote[]>([]);
  const [selectedRef, setSelectedRef] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeType, setActiveType] = useState<StudyNoteType | 'all'>('all');
  const [showQuickAdd, setShowQuickAdd] = useState(false);
  const [newNoteContent, setNewNoteContent] = useState('');
  const [newNoteRef, setNewNoteRef] = useState('');
  const [newNoteType, setNewNoteType] = useState<StudyNoteType>('note');

  useEffect(() => {
    setNotes(getStudyNotes(book.id));
    window.scrollTo(0, 0);
  }, [book.id]);

  const references = useMemo(() => getReferences(book.id), [notes]);

  const filteredNotes = useMemo(() => {
    return notes.filter(n => {
      const matchesRef = !selectedRef || n.reference === selectedRef;
      const matchesType = activeType === 'all' || n.type === activeType;
      const matchesSearch = n.content.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesRef && matchesType && matchesSearch;
    });
  }, [notes, selectedRef, activeType, searchQuery]);

  const handleSave = () => {
    if (!newNoteContent.trim()) return;
    saveStudyNote({
      bookId: book.id,
      content: newNoteContent,
      reference: newNoteRef || 'General',
      type: newNoteType
    });
    setNotes(getStudyNotes(book.id));
    setNewNoteContent('');
    onToast('Note captured');
  };

  const handleDelete = (id: string) => {
    if (confirm('Delete study note?')) {
      deleteStudyNote(id);
      setNotes(getStudyNotes(book.id));
      onToast('Note removed');
    }
  };

  return (
    <div className="fixed inset-0 z-[100] bg-slate-950 flex flex-col animate-in fade-in duration-500">
      {/* Header */}
      <header className="h-20 border-b border-slate-900 flex items-center justify-between px-8 glass sticky top-0 z-20">
        <div className="flex items-center gap-6">
          <button onClick={onBack} className="p-2 rounded-full hover:bg-slate-800 text-slate-400 transition-colors">
            <ArrowLeft size={24} />
          </button>
          <div className="h-8 w-px bg-slate-800" />
          <div className="flex items-center gap-3">
             <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                <Brain className="text-indigo-400" size={20} />
             </div>
             <div>
                <h1 className="text-sm font-black text-white uppercase tracking-widest">{book.volumeInfo.title}</h1>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">Study Mode Active</p>
             </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
           <div className="relative group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600 group-focus-within:text-indigo-400 transition-colors" size={16} />
              <input 
                type="text" 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search notes..." 
                className="bg-slate-900/50 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
              />
           </div>
           <button className="p-2.5 rounded-xl border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-900 transition-all">
              <Download size={18} />
           </button>
        </div>
      </header>

      {/* Main Workspace */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Sidebar: References List */}
        <aside className="w-72 border-r border-slate-900 flex flex-col bg-slate-950">
          <div className="p-6">
            <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4">References</h3>
            <button 
              onClick={() => setSelectedRef(null)}
              className={`w-full text-left px-4 py-3 rounded-xl text-xs font-bold transition-all mb-2 ${!selectedRef ? 'bg-indigo-500 text-white' : 'text-slate-400 hover:bg-slate-900'}`}
            >
              All References ({notes.length})
            </button>
            <div className="space-y-1 overflow-y-auto max-h-[calc(100vh-250px)] custom-scrollbar">
              {references.map(ref => (
                <button 
                  key={ref}
                  onClick={() => setSelectedRef(ref)}
                  className={`w-full text-left px-4 py-3 rounded-xl text-xs font-bold transition-all flex justify-between items-center ${selectedRef === ref ? 'bg-slate-800 text-white' : 'text-slate-500 hover:bg-slate-900'}`}
                >
                  <span className="truncate">{ref}</span>
                  <span className="text-[8px] bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                    {notes.filter(n => n.reference === ref).length}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Notes Surface */}
        <main className="flex-1 overflow-y-auto custom-scrollbar bg-slate-950/20 p-12">
           <div className="max-w-4xl mx-auto space-y-12">
              
              {/* Type Filtering */}
              <div className="flex items-center gap-2 pb-6 border-b border-slate-900">
                 <TypeToggle active={activeType === 'all'} onClick={() => setActiveType('all')} icon={<LayoutGrid size={14} />} label="All" />
                 <TypeToggle active={activeType === 'quote'} onClick={() => setActiveType('quote')} icon={<QuoteIcon size={14} />} label="Quotes" />
                 <TypeToggle active={activeType === 'insight'} onClick={() => setActiveType('insight')} icon={<Lightbulb size={14} />} label="Insights" />
                 <TypeToggle active={activeType === 'question'} onClick={() => setActiveType('question')} icon={<HelpCircle size={14} />} label="Questions" />
                 <TypeToggle active={activeType === 'note'} onClick={() => setActiveType('note')} icon={<MessageSquare size={14} />} label="Notes" />
              </div>

              {/* Grid of Notes */}
              {filteredNotes.length > 0 ? (
                <div className="grid grid-cols-1 gap-6">
                  {filteredNotes.map(note => (
                    <StudyNoteCard 
                      key={note.id} 
                      note={note} 
                      onEdit={() => {}} 
                      onDelete={handleDelete} 
                      onPromote={onPromoteToQuote}
                    />
                  ))}
                </div>
              ) : (
                <div className="py-40 text-center">
                   <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto mb-6 text-slate-700">
                      <BookOpen size={28} />
                   </div>
                   <h3 className="text-xl font-bold text-white mb-2">No notes here yet</h3>
                   <p className="text-slate-500 text-sm">Start your study session using the capture bar below.</p>
                </div>
              )}
           </div>
        </main>
      </div>

      {/* Quick Add Footer */}
      <footer className="p-6 bg-slate-900/50 border-t border-slate-900 glass">
         <div className="max-w-4xl mx-auto flex items-end gap-4">
            <div className="flex-1 space-y-4">
               <div className="flex items-center gap-4">
                  <div className="flex items-center gap-1 p-1 bg-slate-950 rounded-xl border border-slate-800">
                     <TypeSelect active={newNoteType === 'note'} onClick={() => setNewNoteType('note')} icon={<MessageSquare size={12} />} label="Note" />
                     <TypeSelect active={newNoteType === 'quote'} onClick={() => setNewNoteType('quote')} icon={<QuoteIcon size={12} />} label="Quote" />
                     <TypeSelect active={newNoteType === 'insight'} onClick={() => setNewNoteType('insight')} icon={<Lightbulb size={12} />} label="Insight" />
                     <TypeSelect active={newNoteType === 'question'} onClick={() => setNewNoteType('question')} icon={<HelpCircle size={12} />} label="Query" />
                  </div>
                  <input 
                    type="text" 
                    placeholder="Reference (e.g. John 3:16)" 
                    value={newNoteRef}
                    onChange={(e) => setNewNoteRef(e.target.value)}
                    className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white outline-none focus:border-indigo-500 transition-all"
                  />
               </div>
               <textarea 
                 value={newNoteContent}
                 onChange={(e) => setNewNoteContent(e.target.value)}
                 onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSave(); }}
                 placeholder="What are you learning? (Cmd+Enter to save)" 
                 className="w-full bg-slate-950 border border-slate-800 rounded-2xl px-6 py-4 text-sm text-white outline-none focus:border-indigo-500 transition-all min-h-[100px] resize-none"
               />
            </div>
            <button 
              onClick={handleSave}
              className="px-8 py-4 rounded-2xl bg-indigo-500 text-white font-bold text-sm shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 active:scale-95 transition-all flex items-center gap-2 mb-1"
            >
               Capture
               <Plus size={20} />
            </button>
         </div>
      </footer>
    </div>
  );
};

const TypeToggle = ({ active, onClick, icon, label }: { active: boolean, onClick: () => void, icon: any, label: string }) => (
  <button 
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${active ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300'}`}
  >
    {icon}
    {label}
  </button>
);

const TypeSelect = ({ active, onClick, icon, label }: { active: boolean, onClick: () => void, icon: any, label: string }) => (
  <button 
    onClick={onClick}
    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all ${active ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400'}`}
  >
    {icon}
    {label}
  </button>
);
