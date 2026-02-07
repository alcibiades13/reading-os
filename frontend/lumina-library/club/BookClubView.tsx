
import React, { useState, useEffect, useMemo } from 'react';
import { BookClub, DiscussionTopic, Message } from '../types';
import { getBookClubs } from '../services/bookClubService';
import { getMessages, sendMessage } from '../services/chatService';
import { 
  Users, Sparkles, Lock, ShieldCheck, ChevronRight, 
  MessageSquare, Hash, TrendingUp, Info, Plus, 
  Send, Paperclip, Quote, Brain, MoreVertical,
  Search, Filter, BookOpen, Clock, Heart, Share2, Globe
} from 'lucide-react';

export const BookClubView: React.FC<{ onOpenBook: (id: string) => void }> = ({ onOpenBook }) => {
  const clubs = useMemo(() => getBookClubs(), []);
  const [activeClubId, setActiveClubId] = useState<string>(clubs[0].id);
  const [activeTopicId, setActiveTopicId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [messageInput, setMessageInput] = useState('');

  const activeClub = useMemo(() => clubs.find(c => c.id === activeClubId)!, [activeClubId, clubs]);
  const activeTopic = useMemo(() => activeClub.topics.find(t => t.id === activeTopicId), [activeTopicId, activeClub]);

  useEffect(() => {
    // Reset topic when club changes
    setActiveTopicId(null);
  }, [activeClubId]);

  useEffect(() => {
    if (activeTopicId) {
      // For demo, we reuse the same chat logic
      setMessages(getMessages('conv-1'));
    }
  }, [activeTopicId]);

  const handleSendMessage = () => {
    if (!messageInput.trim()) return;
    const sent = sendMessage('conv-1', { content: messageInput });
    setMessages(prev => [...prev, sent]);
    setMessageInput('');
  };

  return (
    <div className="h-full flex bg-[#02040a] animate-in fade-in duration-1000">
      
      {/* 1. CLUBS SIDEBAR (Circles) */}
      <aside className="w-20 lg:w-72 border-r border-white/5 flex flex-col glass backdrop-blur-3xl z-40 bg-slate-950/40">
        <div className="p-6 border-b border-white/5 flex items-center justify-between">
          <h2 className="hidden lg:block text-[10px] font-black text-slate-500 uppercase tracking-[0.4em]">Circles</h2>
          <button className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500 hover:text-white transition-all">
            <Plus size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-3 lg:p-4 space-y-3">
          {clubs.map(club => (
            <button 
              key={club.id}
              onClick={() => setActiveClubId(club.id)}
              className={`w-full group relative flex items-center gap-4 p-3 rounded-2xl transition-all ${
                activeClubId === club.id 
                ? 'bg-white/10 shadow-[0_10px_30px_rgba(0,0,0,0.5)]' 
                : 'hover:bg-white/5'
              }`}
            >
              {activeClubId === club.id && (
                <div className="absolute left-0 w-1 h-8 bg-indigo-500 rounded-r-full" />
              )}
              <div 
                className="w-10 h-10 lg:w-12 lg:h-12 rounded-2xl shrink-0 flex items-center justify-center text-white font-black text-xs shadow-lg"
                style={{ background: `linear-gradient(135deg, ${club.accentColor}dd, #000000)` }}
              >
                {club.name.charAt(0)}
              </div>
              <div className="hidden lg:block text-left min-w-0">
                <p className={`text-sm font-bold truncate ${activeClubId === club.id ? 'text-white' : 'text-slate-400'}`}>
                  {club.name}
                </p>
                <div className="flex items-center gap-2 mt-0.5">
                  <Users size={10} className="text-slate-600" />
                  <span className="text-[9px] font-black text-slate-500 uppercase">{club.memberCount} Members</span>
                </div>
              </div>
            </button>
          ))}
        </div>

        <div className="p-6 border-t border-white/5">
           <div className="hidden lg:flex flex-col gap-4">
              <div className="p-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/10">
                 <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-2 flex items-center gap-2">
                    <Sparkles size={12} /> Pro Tip
                 </p>
                 <p className="text-[11px] text-slate-500 leading-relaxed italic">
                    Finish 70% of the book to unlock the Spoiler Discourses.
                 </p>
              </div>
           </div>
        </div>
      </aside>

      {/* 2. CLUB HUB / TOPICS */}
      <main className="flex-1 flex flex-col overflow-hidden">
        
        {/* CLUB HEADER & PROGRESS */}
        <header className="p-10 border-b border-white/5 relative overflow-hidden shrink-0">
           <div className="absolute top-0 right-0 p-20 opacity-10 pointer-events-none">
              <Globe size={300} className="text-indigo-500" />
           </div>

           <div className="relative z-10 flex flex-col lg:flex-row lg:items-end justify-between gap-8">
              <div className="space-y-4">
                 <div className="flex items-center gap-3">
                    <span className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[10px] font-black text-indigo-400 uppercase tracking-widest">
                       {activeClub.isPrivate ? 'Private Circle' : 'Open Salon'}
                    </span>
                    <span className="text-slate-600 text-xs">•</span>
                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Est. 2024</span>
                 </div>
                 <h1 className="text-5xl font-black text-white tracking-tighter">{activeClub.name}</h1>
                 <p className="text-slate-400 max-w-xl text-lg leading-relaxed">{activeClub.description}</p>
              </div>

              {/* Expedition Progress Card */}
              <div className="w-full lg:w-80 glass p-6 rounded-[2.5rem] border-white/10 shadow-2xl flex items-center gap-6">
                 <div className="w-16 h-24 rounded-lg overflow-hidden shadow-xl ring-1 ring-white/10 shrink-0">
                    <img src={activeClub.currentBookCover} className="w-full h-full object-cover" alt="" />
                 </div>
                 <div className="flex-1 min-w-0">
                    <p className="text-[9px] font-black text-indigo-400 uppercase tracking-widest mb-1">Current Expedition</p>
                    <h4 className="text-sm font-bold text-white truncate mb-4">{activeClub.currentBookTitle}</h4>
                    <div className="space-y-2">
                       <div className="flex justify-between text-[10px] font-black uppercase text-slate-500">
                          <span>Group Focus</span>
                          <span className="text-indigo-400">{activeClub.averageProgress}%</span>
                       </div>
                       <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                          <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${activeClub.averageProgress}%` }} />
                       </div>
                    </div>
                 </div>
              </div>
           </div>
        </header>

        {/* 3. TOPIC DISCOURSE AREA */}
        <div className="flex-1 flex overflow-hidden">
           
           {/* LEFT: Topic List */}
           <div className="w-full lg:w-96 border-r border-white/5 flex flex-col bg-slate-950/20">
              <div className="p-6 flex items-center justify-between shrink-0">
                 <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Discourses</h3>
                 <button className="flex items-center gap-2 text-[10px] font-black text-indigo-400 uppercase hover:text-white transition-colors">
                    <Filter size={14} /> Sort By Recent
                 </button>
              </div>

              <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-4">
                 {activeClub.topics.map(topic => (
                   <button 
                     key={topic.id}
                     onClick={() => setActiveTopicId(topic.id)}
                     className={`w-full text-left p-6 rounded-3xl border transition-all relative overflow-hidden group ${
                       activeTopicId === topic.id 
                       ? 'bg-indigo-500/10 border-indigo-500/40 shadow-xl' 
                       : 'bg-white/5 border-white/5 hover:bg-white/[0.08]'
                     }`}
                   >
                     {topic.isLocked && (
                        <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm z-10 flex flex-col items-center justify-center p-4 text-center">
                           <Lock size={20} className="text-slate-500 mb-2" />
                           <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Expedition Restricted</p>
                           <p className="text-[8px] text-slate-600 mt-1">Requires {topic.requiredProgress}% completion</p>
                        </div>
                     )}

                     <div className="relative z-0">
                        <div className="flex items-center justify-between mb-3">
                           <div className={`px-2 py-0.5 rounded-lg text-[8px] font-black uppercase tracking-widest ${
                              topic.category === 'spoilers' ? 'bg-rose-500/20 text-rose-400' :
                              topic.category === 'theories' ? 'bg-amber-500/20 text-amber-400' :
                              'bg-indigo-500/20 text-indigo-400'
                           }`}>
                              {topic.category}
                           </div>
                           <span className="text-[10px] text-slate-600 font-bold">{topic.lastActivity}</span>
                        </div>
                        <h4 className="text-base font-bold text-white mb-2 group-hover:text-indigo-400 transition-colors">{topic.title}</h4>
                        <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed mb-4">{topic.description}</p>
                        <div className="flex items-center gap-4 text-[10px] font-black text-slate-600 uppercase">
                           <span className="flex items-center gap-1.5"><MessageSquare size={12} /> {topic.messageCount} posts</span>
                           <span className="flex items-center gap-1.5"><Users size={12} /> 12 active</span>
                        </div>
                     </div>
                   </button>
                 ))}
              </div>
           </div>

           {/* RIGHT: Topic Discussion / Conversation */}
           <div className="flex-1 flex flex-col bg-slate-950/40 relative">
              {activeTopic ? (
                <>
                  <div className="flex-1 overflow-y-auto p-10 custom-scrollbar space-y-12">
                     <div className="text-center py-10 opacity-30">
                        <div className="h-px w-full bg-gradient-to-r from-transparent via-slate-800 to-transparent mb-4" />
                        <span className="text-[10px] font-black uppercase tracking-[0.5em] text-slate-500">Beginning of Discourse</span>
                     </div>
                     
                     {messages.map(msg => (
                       <DiscussionMessage key={msg.id} msg={msg} />
                     ))}
                     <div className="h-20" />
                  </div>

                  {/* Topic Composer */}
                  <div className="p-8 glass border-t border-white/5 bg-slate-950/80 backdrop-blur-3xl sticky bottom-0">
                     <div className="max-w-4xl mx-auto flex items-end gap-6">
                        <div className="flex-1 relative">
                           <textarea 
                             value={messageInput}
                             onChange={(e) => setMessageInput(e.target.value)}
                             placeholder={`Contribute to "${activeTopic.title}"...`}
                             className="w-full bg-white/5 border border-white/10 rounded-3xl px-8 py-5 text-slate-100 placeholder-slate-600 focus:border-indigo-500 outline-none transition-all min-h-[80px] max-h-40 resize-none font-serif text-lg italic"
                           />
                           <div className="absolute right-6 bottom-5 flex items-center gap-2">
                              <button className="p-2 text-slate-500 hover:text-indigo-400 transition-colors"><Paperclip size={18} /></button>
                              <button className="p-2 text-slate-500 hover:text-emerald-400 transition-colors"><Brain size={18} /></button>
                           </div>
                        </div>
                        <button 
                          onClick={handleSendMessage}
                          className="w-16 h-16 rounded-full bg-indigo-500 text-white flex items-center justify-center shadow-2xl shadow-indigo-500/40 hover:scale-110 active:scale-95 transition-all"
                        >
                           <Send size={24} />
                        </button>
                     </div>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-20 opacity-30">
                   <div className="w-24 h-24 rounded-full border-2 border-dashed border-slate-700 flex items-center justify-center mb-8">
                      <MessageSquare size={48} className="text-slate-600" />
                   </div>
                   <h3 className="text-2xl font-black text-white uppercase tracking-widest mb-4">Select a Discourse</h3>
                   <p className="max-w-xs text-slate-500 font-medium leading-relaxed">Join an ongoing thematic discussion or explore the archives of this Circle.</p>
                </div>
              )}
           </div>

        </div>
      </main>
    </div>
  );
};

const DiscussionMessage: React.FC<{ msg: Message }> = ({ msg }) => (
  <div className="flex gap-6 group">
     <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 border border-indigo-500/20 flex items-center justify-center text-indigo-400 font-black text-sm shrink-0 shadow-lg group-hover:scale-110 transition-transform">
        {msg.senderName.charAt(0)}
     </div>
     <div className="flex-1 space-y-3">
        <div className="flex items-center justify-between">
           <div className="flex items-center gap-3">
              <span className="text-sm font-black text-white">{msg.senderName}</span>
              <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
           </div>
           <button className="p-2 text-slate-700 hover:text-slate-400 transition-colors opacity-0 group-hover:opacity-100"><MoreVertical size={14} /></button>
        </div>
        <div className="text-xl font-serif text-slate-300 leading-relaxed italic">
           "{msg.content}"
        </div>
        
        {/* Attachment rendering (simplified for demo) */}
        {msg.attachments.length > 0 && (
           <div className="p-4 rounded-2xl bg-white/5 border border-white/5 flex items-center gap-4 mt-4 max-w-sm">
              <Quote size={14} className="text-indigo-500" />
              <div className="min-w-0">
                 <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">Shared Insight</p>
                 <p className="text-xs text-slate-400 truncate italic">"{msg.attachments[0].content}"</p>
              </div>
           </div>
        )}
     </div>
  </div>
);
