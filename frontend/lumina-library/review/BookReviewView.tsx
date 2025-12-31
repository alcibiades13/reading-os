
import React, { useState, useEffect, useRef } from 'react';
import { GoogleBook, LibraryStatus } from '../types';
import { StarRating } from '../components/StarRating';
import { 
  ArrowLeft, Bold, Italic, Heading1, Heading2, List, Quote, 
  Link as LinkIcon, Save, Send, Globe, Lock, Eye, BookOpen,
  Calendar, Info, Sparkles, Check
} from 'lucide-react';

interface BookReviewViewProps {
  book: GoogleBook;
  onBack: () => void;
  onSave: (review: string, isPublic: boolean) => void;
  initialReview?: string;
  initialRating?: number;
  initialStatus?: LibraryStatus;
}

export const BookReviewView: React.FC<BookReviewViewProps> = ({ 
  book, 
  onBack, 
  onSave, 
  initialReview = '',
  initialRating = 0,
  initialStatus = 'read'
}) => {
  const [content, setContent] = useState(initialReview);
  const [isPublic, setIsPublic] = useState(true);
  const [isDraft, setIsDraft] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const editorRef = useRef<HTMLDivElement>(null);

  const { volumeInfo } = book;
  const coverUrl = volumeInfo.imageLinks?.thumbnail?.replace('http:', 'https:') || 
    `https://via.placeholder.com/300x450/1E293B/64748B?text=${encodeURIComponent(volumeInfo.title)}`;

  // Auto-save to localStorage
  useEffect(() => {
    const saved = localStorage.getItem(`draft_review_${book.id}`);
    if (saved && !initialReview) {
      setContent(saved);
      if (editorRef.current) editorRef.current.innerHTML = saved;
    }
  }, [book.id, initialReview]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      localStorage.setItem(`draft_review_${book.id}`, content);
    }, 1000);
    return () => clearTimeout(timeout);
  }, [content, book.id]);

  useEffect(() => {
    const text = content.replace(/<[^>]*>/g, '');
    setWordCount(text.split(/\s+/).filter(Boolean).length);
  }, [content]);

  const handleCommand = (command: string, value?: string) => {
    document.execCommand(command, false, value);
    if (editorRef.current) setContent(editorRef.current.innerHTML);
  };

  const handlePublish = async () => {
    setIsSaving(true);
    // Simulate API call
    await new Promise(r => setTimeout(r, 1500));
    onSave(content, isPublic);
    setIsDraft(false);
    setIsSaving(false);
    localStorage.removeItem(`draft_review_${book.id}`);
  };

  return (
    <div className="min-h-screen bg-slate-950 animate-in fade-in duration-700">
      {/* Header */}
      <nav className="sticky top-0 z-50 glass border-b border-slate-800 px-6 h-20 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <button 
            onClick={onBack}
            className="p-2 rounded-full hover:bg-slate-800 text-slate-400 transition-colors"
          >
            <ArrowLeft size={24} />
          </button>
          <div className="hidden sm:block h-8 w-px bg-slate-800" />
          <div>
            <h1 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-slate-500 font-medium">Review:</span> {volumeInfo.title}
            </h1>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${isDraft ? 'bg-amber-500' : 'bg-emerald-500'}`} />
              <span className="text-[10px] uppercase font-black tracking-widest text-slate-500">
                {isDraft ? 'Draft Mode' : 'Published'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-[11px] font-bold text-slate-400">
            <Sparkles size={12} className="text-indigo-400" />
            Auto-saving active
          </div>
          <button 
            onClick={handlePublish}
            disabled={isSaving}
            className="px-6 py-2.5 rounded-xl bg-indigo-500 text-white font-bold text-sm shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 transition-all flex items-center gap-2"
          >
            {isSaving ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : <Send size={16} />}
            Publish Review
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
          
          {/* Main Writing Surface */}
          <div className="lg:col-span-8 space-y-6">
            {/* Toolbar */}
            <div className="flex items-center flex-wrap gap-1 p-2 rounded-2xl glass border-slate-800 sticky top-24 z-40">
              <ToolbarButton icon={<Bold size={18} />} onClick={() => handleCommand('bold')} label="Bold" />
              <ToolbarButton icon={<Italic size={18} />} onClick={() => handleCommand('italic')} label="Italic" />
              <div className="w-px h-6 bg-slate-800 mx-1" />
              <ToolbarButton icon={<Heading1 size={18} />} onClick={() => handleCommand('formatBlock', 'H1')} label="H1" />
              <ToolbarButton icon={<Heading2 size={18} />} onClick={() => handleCommand('formatBlock', 'H2')} label="H2" />
              <div className="w-px h-6 bg-slate-800 mx-1" />
              <ToolbarButton icon={<List size={18} />} onClick={() => handleCommand('insertUnorderedList')} label="List" />
              <ToolbarButton icon={<Quote size={18} />} onClick={() => handleCommand('formatBlock', 'BLOCKQUOTE')} label="Quote" />
              <ToolbarButton icon={<LinkIcon size={18} />} onClick={() => {
                const url = prompt('Enter URL');
                if (url) handleCommand('createLink', url);
              }} label="Link" />
              
              <div className="ml-auto pr-4 flex items-center gap-6">
                 <div className="flex items-center gap-2 text-slate-500 text-xs font-bold">
                   <Eye size={14} />
                   <span>{wordCount} words</span>
                 </div>
              </div>
            </div>

            {/* Content Area */}
            <div className="min-h-[60vh] p-10 rounded-3xl glass border-slate-800 bg-slate-900/30 group">
              <div 
                ref={editorRef}
                contentEditable
                onInput={(e) => setContent(e.currentTarget.innerHTML)}
                // Removed invalid placeholder attribute from div to fix TypeScript error.
                // A custom placeholder overlay is handled below based on the content state.
                className="editor-surface text-xl md:text-2xl text-slate-200 leading-relaxed font-serif min-h-[50vh] focus:outline-none"
              />
              {content === '' && (
                <div className="absolute top-10 left-10 text-slate-600 text-2xl font-serif pointer-events-none">
                  What moved you about this book? Share your thoughts...
                </div>
              )}
            </div>

            {/* Visibility Toggle */}
            <div className="flex items-center justify-between p-6 rounded-2xl bg-slate-900/50 border border-slate-800">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-xl ${isPublic ? 'bg-sky-500/10 text-sky-400' : 'bg-slate-800 text-slate-500'}`}>
                  {isPublic ? <Globe size={20} /> : <Lock size={20} />}
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">{isPublic ? 'Public Review' : 'Private Journal'}</h4>
                  <p className="text-xs text-slate-500">
                    {isPublic ? 'Visible to the Lumina community' : 'Only you can see this reflection'}
                  </p>
                </div>
              </div>
              <button 
                onClick={() => setIsPublic(!isPublic)}
                className={`relative w-12 h-6 rounded-full transition-colors ${isPublic ? 'bg-indigo-500' : 'bg-slate-800'}`}
              >
                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${isPublic ? 'left-7' : 'left-1'}`} />
              </button>
            </div>
          </div>

          {/* Sidebar - Book Info */}
          <div className="lg:col-span-4 sticky top-24 space-y-6">
            <div className="rounded-3xl glass border-slate-800 overflow-hidden shadow-2xl bg-slate-900/40">
              <div className="aspect-[2/3] w-full overflow-hidden">
                <img src={coverUrl} alt={volumeInfo.title} className="w-full h-full object-cover" />
              </div>
              <div className="p-8 space-y-6">
                <div>
                  <h3 className="text-xl font-black text-white leading-tight mb-2">{volumeInfo.title}</h3>
                  <p className="text-indigo-400 font-bold">{volumeInfo.authors?.join(', ')}</p>
                </div>

                <div className="space-y-4 pt-6 border-t border-slate-800">
                  <div>
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-2">My Rating</span>
                    <StarRating rating={initialRating} size={18} />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-1">Status</span>
                      <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs uppercase tracking-wider">
                        <Check size={14} />
                        {initialStatus?.replace('_', ' ')}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-1">Finished</span>
                      <span className="text-slate-300 font-bold text-xs">Today</span>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10 flex items-start gap-3">
                  <Info size={16} className="text-indigo-400 shrink-0 mt-0.5" />
                  <p className="text-[11px] text-slate-400 leading-relaxed italic">
                    Your review helps other readers discover hidden gems and deep insights. Be honest, be detailed.
                  </p>
                </div>
              </div>
            </div>

            <button 
              onClick={() => setIsDraft(true)}
              className="w-full py-4 rounded-2xl border border-slate-800 text-slate-400 font-bold hover:bg-slate-800 hover:text-white transition-all flex items-center justify-center gap-3"
            >
              <Save size={18} />
              Save Draft
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const ToolbarButton = ({ icon, onClick, label }: { icon: any, onClick: () => void, label: string }) => (
  <button 
    type="button"
    onClick={onClick}
    className="p-3 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-all group relative"
    title={label}
  >
    {icon}
    <span className="absolute -bottom-10 left-1/2 -translate-x-1/2 px-2 py-1 rounded bg-slate-900 border border-slate-800 text-[10px] font-bold text-white opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
      {label}
    </span>
  </button>
);
