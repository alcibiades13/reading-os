
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Conversation, Message, MessageAttachment, UserBook, Quote } from '../types';
import { getConversations, getMessages, sendMessage } from '../services/chatService';
import { getUserLibrary } from '../services/userBooksService';
import { getQuotes } from '../services/quotesService';
import { 
  MessageSquare, Search, Plus, Filter, Star, 
  Send, Paperclip, Book, Quote as QuoteIcon, 
  Brain, Maximize2, X, ChevronRight, MoreHorizontal,
  Bookmark, Inbox, Archive, Users, Layout, Clock, ExternalLink
} from 'lucide-react';

export const CorrespondenceView: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Composer state
  const [messageText, setMessageText] = useState('');
  const [isImportant, setIsImportant] = useState(false);
  const [attachments, setAttachments] = useState<MessageAttachment[]>([]);
  const [showPicker, setShowPicker] = useState<'none' | 'book' | 'quote'>('none');
  const [isExpanded, setIsExpanded] = useState(false);

  // Library data for picker
  const library = useMemo(() => getUserLibrary(), []);
  const quotes = useMemo(() => getQuotes(), []);

  useEffect(() => {
    setConversations(getConversations());
  }, []);

  useEffect(() => {
    if (activeConvId) {
      setMessages(getMessages(activeConvId));
    }
  }, [activeConvId]);

  const activeConv = useMemo(() => 
    conversations.find(c => c.id === activeConvId), 
  [conversations, activeConvId]);

  const handleSend = () => {
    if (!messageText.trim() && attachments.length === 0) return;
    if (!activeConvId) return;

    const sent = sendMessage(activeConvId, {
      content: messageText,
      attachments,
      isImportant
    });

    setMessages([...messages, sent]);
    setMessageText('');
    setAttachments([]);
    setIsImportant(false);
  };

  const addAttachment = (type: 'book' | 'quote', item: any) => {
    const attachment: MessageAttachment = type === 'book' ? {
      type: 'book',
      id: item.id,
      title: item.volumeInfo.title,
      subtitle: item.volumeInfo.authors?.[0],
      image: item.volumeInfo.imageLinks?.thumbnail
    } : {
      type: 'quote',
      id: item.id,
      title: 'Shared Quote',
      content: item.content,
      subtitle: item.bookTitle
    };

    setAttachments([...attachments, attachment]);
    setShowPicker('none');
  };

  return (
    <div className="fixed inset-0 top-20 bg-slate-950 flex animate-in fade-in duration-700">
      
      {/* --- INBOX SIDEBAR --- */}
      <aside className="w-80 border-r border-white/5 flex flex-col bg-slate-900/20 backdrop-blur-xl">
        <div className="p-6 border-b border-white/5">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-sm font-black text-white uppercase tracking-[0.3em]">Correspondents</h2>
            <button className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500 hover:text-white transition-all">
              <Plus size={18} />
            </button>
          </div>
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600 group-focus-within:text-indigo-500 transition-colors" size={14} />
            <input 
              type="text" 
              placeholder="Find intellectual peers..."
              className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {conversations.map(conv => (
            <ConversationItem 
              key={conv.id} 
              conv={conv} 
              isActive={activeConvId === conv.id}
              onClick={() => setActiveConvId(conv.id)}
            />
          ))}
        </div>
      </aside>

      {/* --- THREAD AREA --- */}
      <main className="flex-1 flex flex-col bg-slate-950/40 relative">
        {activeConv ? (
          <>
            {/* Thread Header */}
            <header className="h-16 border-b border-white/5 px-8 flex items-center justify-between glass sticky top-0 z-20">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center text-[10px] font-black text-white ring-2 ring-indigo-500/20">
                    {activeConv.participants.find(p => p.id !== 'me')?.name.charAt(0)}
                  </div>
                  <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-slate-950" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">{activeConv.participants.find(p => p.id !== 'me')?.name}</h3>
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] text-slate-500 font-black uppercase tracking-widest">Active Discussion</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button className="p-2 text-slate-500 hover:text-white transition-colors"><Star size={18} /></button>
                <button className="p-2 text-slate-500 hover:text-white transition-colors"><Search size={18} /></button>
                <button className="p-2 text-slate-500 hover:text-white transition-colors"><MoreHorizontal size={18} /></button>
              </div>
            </header>

            {/* Message Timeline */}
            <div className="flex-1 overflow-y-auto p-12 custom-scrollbar space-y-12">
               {messages.map(msg => (
                 <MessageCard key={msg.id} msg={msg} isMe={msg.senderId === 'me'} />
               ))}
               <div className="h-20" /> {/* Spacer */}
            </div>

            {/* Advanced Composer */}
            <div className={`p-6 border-t border-white/5 glass transition-all duration-500 ${isExpanded ? 'h-[60vh]' : 'h-auto'}`}>
              <div className="max-w-4xl mx-auto space-y-4">
                
                {/* Attachment Preview Bar */}
                {attachments.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {attachments.map((at, idx) => (
                      <div key={idx} className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-[10px] font-bold text-indigo-400">
                        {at.type === 'book' ? <Book size={12} /> : <QuoteIcon size={12} />}
                        <span className="truncate max-w-[120px]">{at.title}</span>
                        <button onClick={() => setAttachments(attachments.filter((_, i) => i !== idx))}><X size={12} /></button>
                      </div>
                    ))}
                  </div>
                )}

                <div className="relative group">
                  <textarea 
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    placeholder="Draft a thoughtful response..."
                    className={`w-full bg-white/5 border-2 border-white/5 rounded-[2rem] px-8 py-6 text-lg font-serif text-slate-200 placeholder-slate-600 focus:border-indigo-500 transition-all outline-none resize-none ${isExpanded ? 'h-full' : 'h-32'}`}
                  />
                  <div className="absolute bottom-4 right-8 flex items-center gap-4">
                    <button 
                      onClick={() => setIsExpanded(!isExpanded)}
                      className="p-2 text-slate-600 hover:text-white transition-colors"
                    >
                      {isExpanded ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between px-4">
                  <div className="flex items-center gap-1 p-1 bg-white/5 rounded-2xl border border-white/5">
                    <ActionButton icon={<Book size={16} />} label="Library" onClick={() => setShowPicker('book')} />
                    <ActionButton icon={<QuoteIcon size={16} />} label="Quote" onClick={() => setShowPicker('quote')} />
                    <ActionButton icon={<Brain size={16} />} label="Note" onClick={() => {}} />
                    <div className="w-px h-6 bg-white/10 mx-2" />
                    <button 
                      onClick={() => setIsImportant(!isImportant)}
                      className={`p-2 rounded-xl transition-all ${isImportant ? 'text-amber-400 bg-amber-400/10' : 'text-slate-500 hover:text-slate-300'}`}
                    >
                      <Star size={18} fill={isImportant ? 'currentColor' : 'none'} />
                    </button>
                  </div>

                  <button 
                    onClick={handleSend}
                    className="flex items-center gap-3 px-8 py-4 rounded-2xl bg-indigo-500 text-white font-black text-[11px] uppercase tracking-widest shadow-xl shadow-indigo-500/20 hover:scale-105 active:scale-95 transition-all"
                  >
                    Send Correspondence <Send size={16} />
                  </button>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-12 opacity-40">
            <div className="w-24 h-24 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mb-8">
              <Inbox size={48} className="text-slate-700" />
            </div>
            <h3 className="text-2xl font-black text-white mb-2 uppercase tracking-[0.3em]">Correspondence Chamber</h3>
            <p className="max-w-xs text-slate-500 font-medium">Select a correspondent to begin a deliberate intellectual exchange.</p>
          </div>
        )}
      </main>

      {/* --- CONTEXT SIDEBAR (DESKTOP) --- */}
      {activeConv && (
        <aside className="w-80 border-l border-white/5 bg-slate-900/10 backdrop-blur-3xl hidden xl:flex flex-col">
          <div className="p-8 border-b border-white/5">
            <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.4em] mb-6">Discussed Material</h3>
            <div className="space-y-6">
              <section>
                <span className="text-[9px] font-bold text-indigo-400 uppercase tracking-widest block mb-4">Books Mentioned</span>
                <div className="space-y-3">
                  {library.slice(0, 2).map(book => (
                    <div key={book.id} className="flex items-center gap-3 p-3 rounded-2xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.05] transition-all cursor-pointer group">
                      <img src={book.volumeInfo.imageLinks?.thumbnail} className="w-10 h-14 rounded-lg object-cover" />
                      <div className="min-w-0">
                        <p className="text-[11px] font-bold text-white truncate">{book.volumeInfo.title}</p>
                        <p className="text-[9px] text-slate-500 font-black uppercase tracking-widest truncate">{book.volumeInfo.authors?.[0]}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </div>
        </aside>
      )}

      {/* --- PICKERS --- */}
      {showPicker !== 'none' && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-8 bg-slate-950/90 backdrop-blur-xl">
           <div className="w-full max-w-2xl glass rounded-[2.5rem] border-white/10 flex flex-col max-h-[80vh]">
              <div className="p-8 border-b border-white/5 flex items-center justify-between">
                <h3 className="text-xl font-black text-white">Select {showPicker === 'book' ? 'Volume' : 'Insight'}</h3>
                <button onClick={() => setShowPicker('none')} className="p-2 text-slate-500 hover:text-white transition-colors"><X size={24} /></button>
              </div>
              <div className="flex-1 overflow-y-auto p-8 grid grid-cols-2 gap-4 custom-scrollbar">
                {showPicker === 'book' ? library.map(book => (
                   <div key={book.id} onClick={() => addAttachment('book', book)} className="p-4 rounded-3xl bg-white/5 border border-white/10 hover:border-indigo-500 cursor-pointer transition-all flex gap-4">
                      <img src={book.volumeInfo.imageLinks?.thumbnail} className="w-12 h-18 rounded-lg object-cover" />
                      <div className="min-w-0">
                        <p className="text-sm font-bold text-white truncate">{book.volumeInfo.title}</p>
                        <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest">{book.volumeInfo.authors?.[0]}</p>
                      </div>
                   </div>
                )) : quotes.map(quote => (
                   <div key={quote.id} onClick={() => addAttachment('quote', quote)} className="p-6 rounded-3xl bg-white/5 border border-white/10 hover:border-indigo-500 cursor-pointer transition-all italic font-serif text-slate-300">
                      "{quote.content.substring(0, 60)}..."
                      <p className="text-[9px] font-black uppercase tracking-widest text-indigo-400 mt-4">— {quote.bookAuthor}</p>
                   </div>
                ))}
              </div>
           </div>
        </div>
      )}
    </div>
  );
};

const ConversationItem = ({ conv, isActive, onClick }: { conv: Conversation, isActive: boolean, onClick: () => void }) => {
  const otherParticipant = conv.participants.find(p => p.id !== 'me');
  const lastMsg = conv.lastMessage;

  return (
    <div 
      onClick={onClick}
      className={`p-6 cursor-pointer transition-all border-l-2 ${isActive ? 'bg-indigo-500/10 border-indigo-500 shadow-[inset_10px_0_30px_rgba(99,102,241,0.05)]' : 'border-transparent hover:bg-white/[0.02]'}`}
    >
      <div className="flex gap-4 items-start">
        <div className="w-12 h-12 rounded-2xl overflow-hidden ring-1 ring-white/10">
          <img src={otherParticipant?.avatar || 'https://via.placeholder.com/100'} className="w-full h-full object-cover" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <h4 className="text-sm font-bold text-white truncate">{otherParticipant?.name}</h4>
            <span className="text-[9px] font-black text-slate-500 uppercase">
              {lastMsg ? new Date(lastMsg.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' }) : ''}
            </span>
          </div>
          <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
            {lastMsg?.isImportant && <Star size={10} className="inline mr-1 text-amber-500 fill-current" />}
            {lastMsg?.content}
          </p>
          {conv.unreadCount > 0 && (
            <div className="mt-2 w-2 h-2 rounded-full bg-indigo-500 shadow-[0_0_8px_#6366f1]" />
          )}
        </div>
      </div>
    </div>
  );
};

const MessageCard = ({ msg, isMe }: { msg: Message, isMe: boolean }) => (
  <div className={`flex flex-col ${isMe ? 'items-end' : 'items-start'} max-w-3xl ${isMe ? 'ml-auto' : ''}`}>
    <div className={`flex items-center gap-3 mb-3 ${isMe ? 'flex-row-reverse' : ''}`}>
      <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{msg.senderName}</span>
      <span className="text-[9px] text-slate-700 font-bold">{new Date(msg.timestamp).toLocaleString()}</span>
      {msg.isImportant && (
        <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-[8px] font-black uppercase text-amber-500 tracking-widest">
          <Star size={10} fill="currentColor" /> Important Correspondence
        </span>
      )}
    </div>

    <div className={`p-8 rounded-[2.5rem] border ${isMe ? 'bg-white/[0.04] border-indigo-500/30 shadow-[0_20px_50px_rgba(0,0,0,0.4)]' : 'bg-slate-900/30 border-white/5 shadow-xl'} w-full`}>
      {msg.subject && (
        <h3 className="text-indigo-400 font-black uppercase tracking-[0.2em] text-[11px] mb-6 flex items-center gap-3">
          <div className="w-1.5 h-1.5 rounded-full bg-indigo-500"></div>
          Subject: {msg.subject}
        </h3>
      )}
      
      <p className="text-xl font-serif text-slate-200 leading-relaxed italic mb-8 selection:bg-indigo-500/30">
        "{msg.content}"
      </p>

      {msg.attachments.length > 0 && (
        <div className="space-y-4 pt-6 border-t border-white/5">
          {msg.attachments.map((at, i) => (
            <AttachmentCard key={i} at={at} />
          ))}
        </div>
      )}
    </div>
  </div>
);

const AttachmentCard = ({ at }: { at: MessageAttachment }) => {
  if (at.type === 'book') {
    return (
      <div className="flex items-center gap-6 p-6 rounded-3xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-all group">
        <div className="w-16 h-24 rounded-xl overflow-hidden shadow-2xl group-hover:scale-105 transition-transform duration-500 ring-1 ring-white/10">
          <img src={at.image} className="w-full h-full object-cover" />
        </div>
        <div className="flex-1">
          <p className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.3em] mb-2 flex items-center gap-2">
            <Book size={12} /> Volume Recommendation
          </p>
          <h4 className="text-lg font-black text-white tracking-tight">{at.title}</h4>
          <p className="text-xs text-slate-500 font-bold">{at.subtitle}</p>
          <button className="mt-4 px-6 py-2 rounded-xl bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-white hover:bg-white/10 transition-all flex items-center gap-2">
            View Entry <ChevronRight size={12} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 rounded-3xl bg-white/[0.02] border border-white/5 italic font-serif text-slate-300 relative group overflow-hidden">
      <div className="absolute top-0 right-0 p-6 opacity-[0.05] group-hover:scale-110 transition-transform">
        <QuoteIcon size={64} />
      </div>
      <p className="text-lg leading-relaxed relative z-10">"{at.content}"</p>
      <p className="text-[10px] font-black uppercase tracking-[0.3em] text-indigo-400 mt-6 relative z-10">
        — {at.subtitle}
      </p>
    </div>
  );
};

const ActionButton = ({ icon, label, onClick }: { icon: any, label: string, onClick: () => void }) => (
  <button 
    onClick={onClick}
    className="p-3 rounded-xl text-slate-500 hover:text-white hover:bg-white/5 transition-all flex items-center gap-2 group"
  >
    {icon}
    <span className="text-[10px] font-black uppercase tracking-widest hidden lg:block opacity-0 group-hover:opacity-100 transition-opacity">{label}</span>
  </button>
);

const Minimize2 = ({ size }: { size: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 14h6v6"/><path d="m10 14-6 6"/><path d="M20 10h-6V4"/><path d="m14 10 6-6"/></svg>
);
