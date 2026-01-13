
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Conversation, Message, MessageAttachment, UserBook, Quote } from '../types';
import { getConversations, getMessages, sendMessage } from '../services/chatService';
import { getUserLibrary } from '../services/userBooksService';
import { getQuotes } from '../services/quotesService';
import { 
  MessageSquare, Search, Plus, Filter, Star, 
  Send, Paperclip, Book, Quote as QuoteIcon, 
  Brain, Maximize2, X, ChevronRight, MoreHorizontal,
  Bookmark, Inbox, Archive, Users, Layout, Clock, ExternalLink, Minimize2
} from 'lucide-react';

export const CorrespondenceView: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  
  // Composer state
  const [messageText, setMessageText] = useState('');
  const [isImportant, setIsImportant] = useState(false);
  const [attachments, setAttachments] = useState<MessageAttachment[]>([]);
  const [showPicker, setShowPicker] = useState<'none' | 'book' | 'quote'>('none');
  const [isExpanded, setIsExpanded] = useState(false);

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
    <div className="h-full flex animate-in fade-in duration-700 bg-[var(--color-bg)]">
      
      {/* --- INBOX PANEL (Secondary Sidebar) --- */}
      <aside className="w-80 border-r border-[var(--color-border)] flex flex-col bg-[var(--color-surface)] backdrop-blur-md">
        <div className="p-6 border-b border-[var(--color-border)]">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xs font-black text-[var(--color-text-primary)] uppercase tracking-[0.3em]">Correspondents</h2>
            <button className="p-2 rounded-xl bg-[var(--color-accent)]/10 text-[var(--color-accent)] hover:bg-[var(--color-accent)] hover:text-white transition-all">
              <Plus size={16} />
            </button>
          </div>
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-secondary)] group-focus-within:text-[var(--color-accent)] transition-colors" size={14} />
            <input 
              type="text" 
              placeholder="Filter peer discussions..."
              className="w-full bg-white/5 border border-[var(--color-border)] rounded-xl pl-10 pr-4 py-2 text-xs text-[var(--color-text-primary)] outline-none focus:border-[var(--color-accent)] transition-all"
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
      <main className="flex-1 flex flex-col relative">
        {activeConv ? (
          <>
            <header className="h-16 border-b border-[var(--color-border)] px-8 flex items-center justify-between bg-[var(--color-surface)] backdrop-blur-md sticky top-0 z-20">
              <div className="flex items-center gap-4">
                <div className="w-8 h-8 rounded-full bg-[var(--color-accent)] flex items-center justify-center text-[10px] font-black text-white">
                  {activeConv.participants.find(p => p.id !== 'me')?.name.charAt(0)}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[var(--color-text-primary)]">{activeConv.participants.find(p => p.id !== 'me')?.name}</h3>
                  <span className="text-[9px] text-[var(--color-text-secondary)] font-black uppercase tracking-widest">Deliberate Exchange</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button className="p-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"><Star size={18} /></button>
                <button className="p-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"><MoreHorizontal size={18} /></button>
              </div>
            </header>

            <div className="flex-1 overflow-y-auto p-12 custom-scrollbar space-y-12">
               {messages.map(msg => (
                 <MessageCard key={msg.id} msg={msg} isMe={msg.senderId === 'me'} />
               ))}
               <div className="h-20" />
            </div>

            {/* Composer */}
            <div className={`p-6 border-t border-[var(--color-border)] bg-[var(--color-surface)] backdrop-blur-md transition-all duration-500 ${isExpanded ? 'h-[60vh]' : 'h-auto'}`}>
              <div className="max-w-4xl mx-auto space-y-4">
                {attachments.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {attachments.map((at, idx) => (
                      <div key={idx} className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[var(--color-accent)]/10 border border-[var(--color-accent)]/20 text-[10px] font-bold text-[var(--color-accent)]">
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
                    className={`w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded-[2rem] px-8 py-6 text-lg font-serif text-[var(--color-text-primary)] placeholder-[var(--color-text-secondary)] focus:border-[var(--color-accent)] transition-all outline-none resize-none ${isExpanded ? 'h-full' : 'h-32'}`}
                  />
                  <button 
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="absolute bottom-4 right-8 p-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
                  >
                    {isExpanded ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                  </button>
                </div>

                <div className="flex items-center justify-between px-4">
                  <div className="flex items-center gap-1 p-1 bg-white/5 rounded-2xl border border-[var(--color-border)]">
                    <ActionButton icon={<Book size={16} />} label="Library" onClick={() => setShowPicker('book')} />
                    <ActionButton icon={<QuoteIcon size={16} />} label="Quote" onClick={() => setShowPicker('quote')} />
                    <div className="w-px h-6 bg-[var(--color-border)] mx-2" />
                    <button 
                      onClick={() => setIsImportant(!isImportant)}
                      className={`p-2 rounded-xl transition-all ${isImportant ? 'text-amber-500 bg-amber-500/10' : 'text-[var(--color-text-secondary)]'}`}
                    >
                      <Star size={18} fill={isImportant ? 'currentColor' : 'none'} />
                    </button>
                  </div>

                  <button 
                    onClick={handleSend}
                    className="flex items-center gap-3 px-8 py-4 rounded-2xl bg-[var(--color-accent)] text-white font-black text-[11px] uppercase tracking-widest shadow-xl shadow-indigo-500/20 hover:scale-105 active:scale-95 transition-all"
                  >
                    Send Correspondence <Send size={16} />
                  </button>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-12 opacity-40">
            <Inbox size={48} className="text-[var(--color-text-secondary)] mb-8" />
            <h3 className="text-2xl font-black text-[var(--color-text-primary)] mb-2 uppercase tracking-[0.3em]">Correspondence Chamber</h3>
            <p className="max-w-xs text-[var(--color-text-secondary)] font-medium">Select a correspondent to begin a deliberate intellectual exchange.</p>
          </div>
        )}
      </main>

      {/* --- PICKERS --- */}
      {showPicker !== 'none' && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-8 bg-[var(--color-bg)]/90 backdrop-blur-xl">
           <div className="w-full max-w-2xl glass rounded-[2.5rem] border-[var(--color-border)] flex flex-col max-h-[80vh]">
              <div className="p-8 border-b border-[var(--color-border)] flex items-center justify-between">
                <h3 className="text-xl font-black text-[var(--color-text-primary)]">Select {showPicker === 'book' ? 'Volume' : 'Insight'}</h3>
                <button onClick={() => setShowPicker('none')} className="p-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"><X size={24} /></button>
              </div>
              <div className="flex-1 overflow-y-auto p-8 grid grid-cols-2 gap-4 custom-scrollbar">
                {showPicker === 'book' ? library.map(book => (
                   <div key={book.id} onClick={() => addAttachment('book', book)} className="p-4 rounded-3xl bg-[var(--color-border)] border border-transparent hover:border-[var(--color-accent)] cursor-pointer transition-all flex gap-4">
                      <img src={book.volumeInfo.imageLinks?.thumbnail} className="w-12 h-18 rounded-lg object-cover" />
                      <div className="min-w-0">
                        <p className="text-sm font-bold text-[var(--color-text-primary)] truncate">{book.volumeInfo.title}</p>
                        <p className="text-[10px] text-[var(--color-text-secondary)] font-black uppercase tracking-widest">{book.volumeInfo.authors?.[0]}</p>
                      </div>
                   </div>
                )) : quotes.map(quote => (
                   <div key={quote.id} onClick={() => addAttachment('quote', quote)} className="p-6 rounded-3xl bg-[var(--color-border)] border border-transparent hover:border-[var(--color-accent)] cursor-pointer transition-all italic font-serif text-[var(--color-text-primary)]">
                      "{quote.content.substring(0, 60)}..."
                      <p className="text-[9px] font-black uppercase tracking-widest text-[var(--color-accent)] mt-4">— {quote.bookAuthor}</p>
                   </div>
                ))}
              </div>
           </div>
        </div>
      )}
    </div>
  );
};

const ConversationItem: React.FC<{ conv: Conversation, isActive: boolean, onClick: () => void }> = ({ conv, isActive, onClick }) => {
  const otherParticipant = conv.participants.find(p => p.id !== 'me');
  const lastMsg = conv.lastMessage;

  return (
    <div 
      onClick={onClick}
      className={`p-6 cursor-pointer transition-all border-l-2 ${isActive ? 'bg-[var(--color-accent)]/10 border-[var(--color-accent)] shadow-[inset_10px_0_30px_rgba(99,102,241,0.05)]' : 'border-transparent hover:bg-white/[0.02]'}`}
    >
      <div className="flex gap-4 items-start">
        <div className="w-12 h-12 rounded-2xl overflow-hidden ring-1 ring-[var(--color-border)]">
          <img src={otherParticipant?.avatar || 'https://via.placeholder.com/100'} className="w-full h-full object-cover" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <h4 className="text-sm font-bold text-[var(--color-text-primary)] truncate">{otherParticipant?.name}</h4>
            <span className="text-[9px] font-black text-[var(--color-text-secondary)] uppercase">
              {lastMsg ? new Date(lastMsg.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' }) : ''}
            </span>
          </div>
          <p className="text-xs text-[var(--color-text-secondary)] line-clamp-2 leading-relaxed">
            {lastMsg?.isImportant && <Star size={10} className="inline mr-1 text-amber-500 fill-current" />}
            {lastMsg?.content}
          </p>
          {conv.unreadCount > 0 && (
            <div className="mt-2 w-2 h-2 rounded-full bg-[var(--color-accent)] shadow-[0_0_8px_var(--color-accent)]" />
          )}
        </div>
      </div>
    </div>
  );
};

const MessageCard: React.FC<{ msg: Message, isMe: boolean }> = ({ msg, isMe }) => (
  <div className={`flex flex-col ${isMe ? 'items-end' : 'items-start'} max-w-3xl ${isMe ? 'ml-auto' : ''}`}>
    <div className={`flex items-center gap-3 mb-3 ${isMe ? 'flex-row-reverse' : ''}`}>
      <span className="text-[10px] font-black text-[var(--color-text-secondary)] uppercase tracking-widest">{msg.senderName}</span>
      <span className="text-[9px] text-[var(--color-text-secondary)] font-bold">{new Date(msg.timestamp).toLocaleString()}</span>
      {msg.isImportant && (
        <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-[8px] font-black uppercase text-amber-500 tracking-widest">
          <Star size={10} fill="currentColor" /> Important Correspondence
        </span>
      )}
    </div>

    <div className={`p-8 rounded-[2.5rem] border ${isMe ? 'bg-[var(--color-accent)]/5 border-[var(--color-accent)]/20 shadow-xl' : 'bg-[var(--color-surface)] border-[var(--color-border)] shadow-md'} w-full`}>
      {msg.subject && (
        <h3 className="text-[var(--color-accent)] font-black uppercase tracking-[0.2em] text-[11px] mb-6 flex items-center gap-3">
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-accent)]"></div>
          Subject: {msg.subject}
        </h3>
      )}
      <p className="text-xl font-serif text-[var(--color-text-primary)] leading-relaxed italic mb-8">
        "{msg.content}"
      </p>
      {msg.attachments.length > 0 && (
        <div className="space-y-4 pt-6 border-t border-[var(--color-border)]">
          {msg.attachments.map((at, i) => (
            <AttachmentCard key={i} at={at} />
          ))}
        </div>
      )}
    </div>
  </div>
);

const AttachmentCard: React.FC<{ at: MessageAttachment }> = ({ at }) => {
  if (at.type === 'book') {
    return (
      <div className="flex items-center gap-6 p-6 rounded-3xl bg-white/[0.02] border border-[var(--color-border)] hover:bg-white/[0.04] transition-all group">
        <div className="w-16 h-24 rounded-xl overflow-hidden shadow-2xl group-hover:scale-105 transition-transform duration-500 ring-1 ring-[var(--color-border)]">
          <img src={at.image} className="w-full h-full object-cover" />
        </div>
        <div className="flex-1">
          <p className="text-[10px] font-black text-[var(--color-accent)] uppercase tracking-[0.3em] mb-2 flex items-center gap-2">
            <Book size={12} /> Volume Recommendation
          </p>
          <h4 className="text-lg font-black text-[var(--color-text-primary)] tracking-tight">{at.title}</h4>
          <p className="text-xs text-[var(--color-text-secondary)] font-bold">{at.subtitle}</p>
          <button className="mt-4 px-6 py-2 rounded-xl bg-white/5 border border-[var(--color-border)] text-[10px] font-black uppercase tracking-widest text-[var(--color-text-primary)] hover:bg-white/10 transition-all flex items-center gap-2">
            View Entry <ChevronRight size={12} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 rounded-3xl bg-white/[0.02] border border-[var(--color-border)] italic font-serif text-[var(--color-text-primary)] relative group overflow-hidden">
      <div className="absolute top-0 right-0 p-6 opacity-[0.05] group-hover:scale-110 transition-transform">
        <QuoteIcon size={64} />
      </div>
      <p className="text-lg leading-relaxed relative z-10">"{at.content}"</p>
      <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[var(--color-accent)] mt-6 relative z-10">
        — {at.subtitle}
      </p>
    </div>
  );
};

const ActionButton: React.FC<{ icon: any, label: string, onClick: () => void }> = ({ icon, label, onClick }) => (
  <button 
    onClick={onClick}
    className="p-3 rounded-xl text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-white/5 transition-all flex items-center gap-2 group"
  >
    {icon}
    <span className="text-[10px] font-black uppercase tracking-widest hidden lg:block opacity-0 group-hover:opacity-100 transition-opacity">{label}</span>
  </button>
);
