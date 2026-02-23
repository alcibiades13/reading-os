
import React, { useState, useEffect, useRef, useMemo } from 'react';
import { GoogleGenAI } from "@google/genai";
import { Sparkles, Brain, Zap, Send, MessageSquare, BookOpen, Quote as QuoteIcon, Network, ArrowRight, Mic, Cpu, Globe, Info, ShieldCheck } from 'lucide-react';
import { getQuotes } from '../services/quotesService';
import { getUserLibrary } from '../services/userBooksService';
import { getVocabulary } from '../services/vocabularyService';

export const IntelligenceView: React.FC = () => {
  const [query, setQuery] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [conversations, setConversations] = useState<{role: 'user' | 'ai', text: string}[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  const library = useMemo(() => getUserLibrary(), []);
  const quotes = useMemo(() => getQuotes(), []);
  const lexicon = useMemo(() => getVocabulary(), []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [conversations]);

  const handleSynthesis = async () => {
    if (!query.trim()) return;
    
    const userMsg = query;
    setConversations(prev => [...prev, { role: 'user', text: userMsg }]);
    setQuery('');
    setIsProcessing(true);

    try {
      // Inicijalizacija klijenta unutar funkcije kako bi uvek koristio najsvežiji ključ
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      
      // Optimizovan kontekst za smanjenje potrošnje tokena
      const compactLibrary = library.slice(0, 15).map(b => b.volumeInfo.title).join(', ');
      const compactQuotes = quotes.slice(0, 3).map(q => q.content.substring(0, 100)).join(' | ');

      const response = await ai.models.generateContent({
        // Koristimo Flash model koji je optimizovan za Free Tier (brzina + besplatni nivo)
        model: 'gemini-3-flash-preview',
        contents: `Kao Aethel, tvoj književni savetnik, analiziraj biblioteku: ${compactLibrary}. 
                   Nedavni citati: ${compactQuotes}.
                   Korisnik pita: ${userMsg}.
                   Odgovori duboko, intelektualno, na SRPSKOM jeziku. Poveži ideje iz knjiga.`,
      });

      setConversations(prev => [...prev, { 
        role: 'ai', 
        text: response.text || "Veza sa arhivom je trenutno nestabilna. Molim vas, ponovite upit." 
      }]);
    } catch (err) {
      console.error(err);
      setConversations(prev => [...prev, { role: 'ai', text: "Došlo je do greške u neuronskoj mreži. Proverite internet vezu." }]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#02040a] relative overflow-hidden">
      
      {/* Background Neural Animation */}
      <div className="absolute inset-0 opacity-20 pointer-events-none">
         <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-500/20 blur-[120px] rounded-full animate-pulse" />
         <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-500/20 blur-[120px] rounded-full animate-pulse" style={{ animationDelay: '2s' }} />
      </div>

      {/* Header */}
      <header className="p-8 border-b border-white/5 relative z-10 flex items-center justify-between glass">
         <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-500 to-fuchsia-500 p-0.5 shadow-2xl shadow-indigo-500/20">
               <div className="w-full h-full rounded-2xl bg-slate-900 flex items-center justify-center">
                  <Sparkles size={20} className="text-white animate-pulse" />
               </div>
            </div>
            <div>
               <h1 className="text-2xl font-black text-white tracking-tighter uppercase">Aethel <span className="text-indigo-500">Intelligence</span></h1>
               <div className="flex items-center gap-2">
                  <span className="text-[9px] font-black text-slate-500 uppercase tracking-[0.4em]">Core Synthesis v4.2</span>
                  <div className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-[8px] font-black text-emerald-400 uppercase tracking-widest">Free Tier Active</div>
               </div>
            </div>
         </div>

         <div className="flex items-center gap-4">
            <div className="hidden lg:flex items-center gap-6 mr-4">
               <Stat label="Model" value="Gemini Flash" />
               <Stat label="Latencija" value="< 1.2s" />
            </div>
            <button className="p-3 rounded-2xl bg-white/5 border border-white/10 text-slate-400 hover:text-white transition-all group relative">
               <ShieldCheck size={18} />
               <div className="absolute top-full mt-4 right-0 w-48 p-4 glass rounded-2xl border-white/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-[100] text-[10px] text-slate-400 leading-relaxed">
                  Vaši podaci se obrađuju u skladu sa Google AI Free Tier uslovima za unapređenje modela.
               </div>
            </button>
         </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto custom-scrollbar p-10 relative z-10" ref={scrollRef}>
         <div className="max-w-4xl mx-auto space-y-10">
            {conversations.length === 0 && (
              <div className="py-20 text-center space-y-8 animate-in fade-in zoom-in duration-1000">
                 <div className="w-24 h-24 rounded-[2.5rem] bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto shadow-2xl">
                    <Brain size={48} className="text-indigo-400" />
                 </div>
                 <h2 className="text-4xl font-black text-white tracking-tighter">Šta ćemo danas sintetizovati?</h2>
                 <p className="text-slate-500 max-w-md mx-auto leading-relaxed">Indeksirao sam tvoju biblioteku. Pitaj me da pronađem veze, sumiram teorije ili ti pomognem da razviješ novu filozofiju.</p>
                 
                 <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left max-w-2xl mx-auto">
                    <SuggestionCard 
                      icon={<Network size={16}/>} 
                      text="Poveži Stoicizam sa Atomic Habits" 
                      onClick={() => setQuery("Poveži učenja Marka Aurelija sa konceptom sistema u knjizi Atomic Habits.")} 
                    />
                    <SuggestionCard 
                      icon={<BookOpen size={16}/>} 
                      text="Analiziraj razvoj Paula Atreidesa" 
                      onClick={() => setQuery("Sumiraj psihološku evoluciju Paula Atreidesa kroz moju biblioteku.")} 
                    />
                 </div>
              </div>
            )}

            {conversations.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-4 duration-500`}>
                <div className={`max-w-[80%] p-8 rounded-[2.5rem] border ${
                  msg.role === 'user' 
                  ? 'bg-indigo-500/10 border-indigo-500/20 text-white rounded-tr-none' 
                  : 'bg-slate-900/60 border-white/5 text-slate-200 rounded-tl-none glass'
                }`}>
                  <div className="flex items-center gap-3 mb-4 opacity-50">
                    {msg.role === 'ai' ? <Sparkles size={14} className="text-indigo-400" /> : <div className="w-2 h-2 rounded-full bg-white" />}
                    <span className="text-[10px] font-black uppercase tracking-widest">{msg.role === 'ai' ? 'Aethel' : 'Ti'}</span>
                  </div>
                  <div className={`text-xl font-serif italic leading-relaxed ${msg.role === 'ai' ? 'text-slate-200' : 'text-indigo-100'}`}>
                    {msg.text}
                  </div>
                </div>
              </div>
            ))}

            {isProcessing && (
              <div className="flex justify-start">
                <div className="p-8 rounded-[2.5rem] bg-slate-900/40 border border-white/5 glass flex items-center gap-4">
                   <div className="flex gap-1">
                      <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                      <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                      <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                   </div>
                   <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Sintetizujem neuronske puteve...</span>
                </div>
              </div>
            )}
         </div>
      </main>

      {/* Input Bar */}
      <footer className="p-10 relative z-10 glass border-t border-white/5">
         <div className="max-w-4xl mx-auto relative group">
            <div className="absolute inset-0 bg-indigo-500/10 blur-3xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-1000" />
            <div className="relative flex items-center gap-4">
               <div className="flex-1 relative">
                  <input 
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSynthesis()}
                    placeholder="Postavi pitanje Aethel-u..."
                    className="w-full bg-white/5 border border-white/10 rounded-[2rem] px-8 py-6 text-xl text-white placeholder-slate-700 outline-none focus:border-indigo-500/50 transition-all font-serif italic"
                  />
                  <div className="absolute right-6 top-1/2 -translate-y-1/2 flex items-center gap-2">
                     <button className="p-2 text-slate-600 hover:text-indigo-400 transition-colors"><Mic size={20} /></button>
                  </div>
               </div>
               <button 
                 onClick={handleSynthesis}
                 className="w-16 h-16 rounded-full bg-indigo-500 text-white flex items-center justify-center shadow-2xl shadow-indigo-500/40 hover:scale-110 active:scale-95 transition-all"
               >
                  <Send size={24} />
               </button>
            </div>
         </div>
         <div className="text-center mt-6">
            <p className="text-[9px] font-black text-slate-700 uppercase tracking-[0.3em]">AI može pogrešiti. Uvek konsultujte originalni tekst knjige.</p>
         </div>
      </footer>
    </div>
  );
};

const Stat = ({ label, value }: { label: string, value: string }) => (
  <div className="text-right">
    <p className="text-[8px] font-black text-slate-500 uppercase tracking-widest mb-0.5">{label}</p>
    <p className="text-sm font-black text-white">{value}</p>
  </div>
);

const SuggestionCard = ({ icon, text, onClick }: { icon: any, text: string, onClick: () => void }) => (
  <button onClick={onClick} className="p-5 rounded-2xl bg-white/5 border border-white/5 hover:border-indigo-500/30 hover:bg-white/10 transition-all text-left flex items-start gap-4 group">
    <div className="p-2.5 rounded-xl bg-slate-800 text-slate-500 group-hover:text-indigo-400 transition-colors">{icon}</div>
    <span className="text-xs font-bold text-slate-400 group-hover:text-white transition-colors">{text}</span>
  </button>
);
