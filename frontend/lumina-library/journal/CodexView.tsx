
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { JournalEntry, Manuscript, Chapter, Mood } from '../types';
import { getJournalEntries, saveJournalEntry, getManuscripts, saveManuscript } from '../services/codexService';
import { 
  PenTool, Feather, Calendar, History, BookType, Sparkles, 
  ChevronRight, MoreVertical, Plus, Maximize2, Minimize2,
  Lock, Unlock, Clock, Save, Trash2, Brain, Hash, Heart,
  BarChart2, FileText, Settings, Archive, Star
} from 'lucide-react';

export const CodexView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'journal' | 'manuscript'>('journal');
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [manuscripts, setManuscripts] = useState<Manuscript[]>([]);
  
  const [selectedEntry, setSelectedEntry] = useState<JournalEntry | null>(null);
  const [selectedManuscript, setSelectedManuscript] = useState<Manuscript | null>(null);
  const [activeChapterIndex, setActiveChapterIndex] = useState(0);
  
  const [isFocusMode, setIsFocusMode] = useState(false);
  const editorRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setEntries(getJournalEntries());
    setManuscripts(getManuscripts());
  }, []);

  const handleNewEntry = () => {
    const entry = saveJournalEntry({ title: 'New Reflection', content: '', mood: 'contemplative' });
    setEntries(getJournalEntries());
    setSelectedEntry(entry);
  };

  const handleSaveEntry = () => {
    if (selectedEntry) {
      saveJournalEntry(selectedEntry);
      setEntries(getJournalEntries());
    }
  };

  const currentChapter = selectedManuscript?.chapters[activeChapterIndex];

  return (
    <div className={`h-full flex bg-[#02040a] transition-all duration-1000 ${isFocusMode ? 'p-0' : ''}`}>
      
      {/* 1. CODEX NAVIGATION (Left Sidebar) */}
      {!isFocusMode && (
        <aside className="w-80 border-r border-white/5 flex flex-col glass backdrop-blur-3xl z-40">
          <div className="p-8 border-b border-white/5">
             <div className="flex items-center gap-3 mb-8">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                   <PenTool size={20} className="text-indigo-400" />
                </div>
                <h2 className="text-xl font-black text-white uppercase tracking-tighter">The Codex</h2>
             </div>

             <div className="flex gap-1 p-1 bg-white/5 rounded-xl border border-white/5">
                <button 
                  onClick={() => setActiveTab('journal')}
                  className={`flex-1 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'journal' ? 'bg-indigo-500 text-white' : 'text-slate-500 hover:text-white'}`}
                >
                  Journal
                </button>
                <button 
                  onClick={() => setActiveTab('manuscript')}
                  className={`flex-1 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'manuscript' ? 'bg-indigo-500 text-white' : 'text-slate-500 hover:text-white'}`}
                >
                  Studio
                </button>
             </div>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-4">
             {activeTab === 'journal' ? (
               <>
                  <button 
                    onClick={handleNewEntry}
                    className="w-full py-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/10 text-indigo-400 text-[10px] font-black uppercase tracking-widest hover:bg-indigo-500 hover:text-white transition-all flex items-center justify-center gap-2 mb-4"
                  >
                    <Plus size={16} /> New Reflection
                  </button>
                  {entries.map(entry => (
                    <button 
                      key={entry.id}
                      onClick={() => { setSelectedEntry(entry); setSelectedManuscript(null); }}
                      className={`w-full text-left p-4 rounded-2xl border transition-all relative overflow-hidden group ${selectedEntry?.id === entry.id ? 'bg-indigo-500/10 border-indigo-500/30' : 'bg-white/5 border-white/5 hover:bg-white/10'}`}
                    >
                      <div className="flex items-center justify-between mb-2">
                         <span className="text-[10px] font-bold text-slate-500">{new Date(entry.date).toLocaleDateString()}</span>
                         <MoodOrb mood={entry.mood} size="sm" />
                      </div>
                      <h4 className="text-sm font-bold text-white truncate group-hover:text-indigo-400 transition-colors">{entry.title}</h4>
                      <p className="text-[10px] text-slate-500 line-clamp-1 mt-1 italic">{entry.content.substring(0, 40)}...</p>
                    </button>
                  ))}
               </>
             ) : (
               <>
                  {manuscripts.map(ms => (
                    <div key={ms.id} className="space-y-4">
                       <button 
                        onClick={() => { setSelectedManuscript(ms); setSelectedEntry(null); }}
                        className={`w-full text-left p-6 rounded-3xl border transition-all ${selectedManuscript?.id === ms.id ? 'bg-indigo-500/10 border-indigo-500/30' : 'bg-white/5 border-white/5 hover:bg-white/10'}`}
                       >
                          <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-1">{ms.genre}</p>
                          <h4 className="text-base font-black text-white mb-2">{ms.title}</h4>
                          <div className="flex items-center justify-between text-[10px] font-bold text-slate-500">
                             <span>{Math.round((ms.currentWordCount / ms.targetWordCount) * 100)}% Complete</span>
                             <span>{ms.currentWordCount} words</span>
                          </div>
                       </button>
                       {selectedManuscript?.id === ms.id && (
                         <div className="pl-4 space-y-2 border-l border-white/5 ml-2 mt-4">
                            {ms.chapters.map((ch, idx) => (
                              <button 
                                key={ch.id}
                                onClick={() => setActiveChapterIndex(idx)}
                                className={`w-full text-left px-4 py-2 rounded-xl text-xs font-bold transition-all ${activeChapterIndex === idx ? 'text-indigo-400 bg-white/5' : 'text-slate-500 hover:text-slate-300'}`}
                              >
                                {idx + 1}. {ch.title}
                              </button>
                            ))}
                            <button className="w-full text-left px-4 py-2 rounded-xl text-[10px] font-black text-slate-600 uppercase hover:text-indigo-400 flex items-center gap-2">
                               <Plus size={12} /> Add Chapter
                            </button>
                         </div>
                       )}
                    </div>
                  ))}
               </>
             )}
          </div>
        </aside>
      )}

      {/* 2. WRITING SURFACE (Center) */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        
        {/* Toolbar (Auto-fades in Focus Mode) */}
        {!isFocusMode && (
          <header className="p-8 border-b border-white/5 glass backdrop-blur-2xl flex items-center justify-between z-10">
            <div className="flex items-center gap-6">
               <div>
                  <h3 className="text-xl font-black text-white tracking-tighter">
                    {selectedEntry ? 'Daily Reflection' : selectedManuscript ? selectedManuscript.title : 'Codex Studio'}
                  </h3>
                  <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mt-1">
                    {selectedEntry ? `Current Mood: ${selectedEntry.mood}` : selectedManuscript ? `Editing Chapter ${activeChapterIndex + 1}` : 'Ready to write'}
                  </p>
               </div>
            </div>

            <div className="flex items-center gap-4">
               <button 
                onClick={() => setIsFocusMode(true)}
                className="p-3 rounded-2xl bg-white/5 text-slate-400 hover:text-white transition-all flex items-center gap-2 text-[10px] font-black uppercase tracking-widest"
               >
                 <Maximize2 size={16} /> Focus
               </button>
               <button 
                onClick={selectedEntry ? handleSaveEntry : () => {}}
                className="px-6 py-3 rounded-2xl bg-indigo-500 text-white font-black text-[10px] uppercase tracking-widest shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 transition-all flex items-center gap-2"
               >
                 <Save size={16} /> Save Changes
               </button>
            </div>
          </header>
        )}

        {/* EDITOR AREA */}
        <div className={`flex-1 overflow-y-auto custom-scrollbar relative p-10 lg:p-20 flex justify-center transition-all duration-1000 ${isFocusMode ? 'bg-[#010206]' : ''}`}>
           {isFocusMode && (
             <button 
              onClick={() => setIsFocusMode(false)}
              className="absolute top-10 right-10 p-4 rounded-full bg-white/5 text-slate-700 hover:text-white transition-all z-50 group"
             >
                <Minimize2 size={24} />
                <span className="absolute top-full mt-2 left-1/2 -translate-x-1/2 text-[10px] font-black uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity">Exit Focus</span>
             </button>
           )}

           <div className="w-full max-w-4xl space-y-12">
              {selectedEntry ? (
                <div className="animate-in fade-in slide-in-from-bottom-10 duration-1000">
                   <div className="flex items-center justify-between mb-12">
                      <input 
                        value={selectedEntry.title}
                        onChange={(e) => setSelectedEntry({...selectedEntry, title: e.target.value})}
                        className="bg-transparent border-none text-5xl font-black text-white outline-none w-full tracking-tighter placeholder-slate-800"
                        placeholder="Reflection Title..."
                      />
                      <MoodSelector active={selectedEntry.mood} onChange={(m) => setSelectedEntry({...selectedEntry, mood: m})} />
                   </div>
                   <textarea 
                     ref={editorRef}
                     value={selectedEntry.content}
                     onChange={(e) => setSelectedEntry({...selectedEntry, content: e.target.value})}
                     className="w-full bg-transparent border-none outline-none text-2xl md:text-3xl font-serif italic text-slate-300 leading-relaxed placeholder-slate-900 min-h-[60vh] resize-none"
                     placeholder="Breathe and let your thoughts flow onto the digital parchment..."
                   />
                </div>
              ) : selectedManuscript ? (
                <div className="animate-in fade-in slide-in-from-bottom-10 duration-1000">
                   <p className="text-indigo-500 font-black text-xs uppercase tracking-[0.5em] mb-4">Chapter {activeChapterIndex + 1}</p>
                   <input 
                     value={currentChapter?.title}
                     className="bg-transparent border-none text-6xl font-black text-white outline-none w-full tracking-tighter mb-12"
                     placeholder="Chapter Title"
                   />
                   <textarea 
                     className="w-full bg-transparent border-none outline-none text-2xl text-slate-300 leading-loose placeholder-slate-900 min-h-[70vh] resize-none font-serif"
                     placeholder="Continue the legacy..."
                     value={currentChapter?.content}
                   />
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center py-40 opacity-30 animate-pulse">
                   <Feather size={80} className="text-slate-500 mb-8" />
                   <h3 className="text-4xl font-black text-white uppercase tracking-[0.2em] mb-4">The Chamber of Silence</h3>
                   <p className="max-w-md mx-auto text-slate-500 text-lg">Every great work begins with the first drop of ink. Select an entry or start a new creation.</p>
                </div>
              )}
           </div>
        </div>

        {/* Writing Stats / Status Bar */}
        {!isFocusMode && (selectedEntry || selectedManuscript) && (
          <footer className="p-6 border-t border-white/5 glass backdrop-blur-3xl flex items-center justify-between px-10">
             <div className="flex items-center gap-8">
                <div className="flex items-center gap-2">
                   <FileText size={14} className="text-slate-500" />
                   <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                     {selectedEntry ? `${selectedEntry.content.split(/\s+/).filter(Boolean).length} words` : `${currentChapter?.wordCount || 0} words in chapter`}
                   </span>
                </div>
                <div className="flex items-center gap-2">
                   <Clock size={14} className="text-slate-500" />
                   <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Last edited 2m ago</span>
                </div>
             </div>

             <div className="flex items-center gap-4">
                <button className="p-2 text-slate-600 hover:text-rose-500 transition-all"><Trash2 size={18} /></button>
                <button className="p-2 text-slate-600 hover:text-white transition-all"><History size={18} /></button>
             </div>
          </footer>
        )}
      </main>
    </div>
  );
};

const MoodOrb = ({ mood, size = 'md' }: { mood: Mood, size?: 'sm' | 'md' | 'lg' }) => {
  const colors: Record<Mood, string> = {
    contemplative: 'bg-indigo-500',
    inspired: 'bg-amber-500',
    melancholic: 'bg-slate-500',
    energetic: 'bg-rose-500',
    serene: 'bg-emerald-500'
  };
  const sizes = { sm: 'w-2 h-2', md: 'w-4 h-4', lg: 'w-8 h-8' };
  return (
    <div className={`${sizes[size]} rounded-full ${colors[mood]} shadow-[0_0_15px_rgba(255,255,255,0.2)] animate-pulse`} />
  );
};

const MoodSelector = ({ active, onChange }: { active: Mood, onChange: (m: Mood) => void }) => {
  const moods: Mood[] = ['contemplative', 'inspired', 'melancholic', 'energetic', 'serene'];
  return (
    <div className="flex gap-3 p-2 rounded-2xl bg-white/5 border border-white/5">
       {moods.map(m => (
         <button 
          key={m}
          onClick={() => onChange(m)}
          className={`w-6 h-6 rounded-full transition-all hover:scale-125 ${active === m ? 'ring-2 ring-white ring-offset-4 ring-offset-[#02040a]' : 'opacity-40'}`}
          title={m}
         >
           <MoodOrb mood={m} size="sm" />
         </button>
       ))}
    </div>
  );
};
