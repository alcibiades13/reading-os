
import React, { useState, useEffect, useMemo } from 'react';
import { UserProfile } from '../types';
import { getFriends } from '../services/friendService';
import { FriendCard } from '../components/FriendCard';
import { Waves, Sparkles, Search, Filter, Globe, Network, Trophy, Brain } from 'lucide-react';

interface FriendsViewProps {
  onOpenFriend: (friend: UserProfile) => void;
  onMessage: (friend: UserProfile) => void;
}

export const FriendsView: React.FC<FriendsViewProps> = ({ onOpenFriend, onMessage }) => {
  const [friends, setFriends] = useState<UserProfile[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => {
      setFriends(getFriends());
      setLoading(false);
    }, 600);
  }, []);

  const filteredFriends = useMemo(() => {
    return friends.filter(f => 
      f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  }, [friends, searchQuery]);

  return (
    <div className="animate-in fade-in duration-1000 p-8 lg:p-12">
      {/* 1. HERO HEADER */}
      <header className="max-w-[1600px] mx-auto mb-12">
         <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8">
            <div className="space-y-6">
               <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                     <Waves className="text-indigo-400" size={20} />
                  </div>
                  <span className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.4em]">Intellectual Resonance</span>
               </div>
               <h1 className="text-5xl lg:text-7xl font-black text-white tracking-tighter">
                  The <span className="text-indigo-500">Resonance</span>
               </h1>
               <p className="text-xl text-slate-400 max-w-xl leading-relaxed">
                  Connect with minds sharing your reading frequency. Discover kindred archives, explore peer vaults, and exchange deep intellectual insights.
               </p>
            </div>

            {/* Quick Global Stats */}
            <div className="flex items-center gap-10">
               <GlobalStat label="Global Rank" value="#428" icon={<Trophy size={16}/>} />
               <GlobalStat label="Avg Resonance" value="84%" icon={<Sparkles size={16}/>} />
               <GlobalStat label="Shared Insights" value="1.2k" icon={<Brain size={16}/>} />
            </div>
         </div>
      </header>

      {/* 2. SEARCH & FILTERS */}
      <section className="max-w-[1600px] mx-auto mb-10 flex flex-col md:flex-row gap-6 items-center">
         <div className="relative flex-1 group">
            <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-indigo-500 transition-colors" size={20} />
            <input 
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name, interests or resonance..."
              className="w-full bg-white/5 border border-white/5 rounded-[2rem] pl-16 pr-8 py-5 text-lg text-white outline-none focus:border-indigo-500 transition-all placeholder-slate-700 glass"
            />
         </div>
         <div className="flex items-center gap-2 p-1 bg-slate-900/40 border border-white/5 rounded-2xl">
            <FilterTab active label="All Members" />
            <FilterTab label="High Resonance" />
            <FilterTab label="Elite Archivists" />
         </div>
      </section>

      {/* 3. FRIENDS GRID - Optimized for 5 columns */}
      <section className="max-w-[1600px] mx-auto">
         {loading ? (
           <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="h-96 rounded-[2rem] bg-white/5 animate-pulse" />
              ))}
           </div>
         ) : filteredFriends.length > 0 ? (
           <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              {filteredFriends.map(friend => (
                <FriendCard 
                  key={friend.id} 
                  friend={friend} 
                  onClick={onOpenFriend} 
                  onMessage={onMessage} 
                />
              ))}
           </div>
         ) : (
           <div className="py-40 text-center space-y-8">
              <div className="w-20 h-20 rounded-full border-2 border-dashed border-slate-700 flex items-center justify-center mx-auto opacity-20">
                 <Search size={32} className="text-slate-500" />
              </div>
              <h3 className="text-2xl font-black text-white uppercase tracking-widest opacity-30">No Resonating Minds Found</h3>
              <p className="text-slate-600 max-w-sm mx-auto">Try a different search term or explore the global network to expand your circle.</p>
           </div>
         )}
      </section>

      {/* 4. FOOTER CALL TO ACTION */}
      <footer className="max-w-[1600px] mx-auto mt-24 p-12 rounded-[3rem] bg-indigo-500/5 border border-indigo-500/10 flex flex-col md:flex-row items-center justify-between gap-8 overflow-hidden relative group">
         <div className="absolute top-0 right-0 p-20 opacity-5 group-hover:scale-110 transition-transform duration-1000">
            <Network size={120} />
         </div>
         <div className="relative z-10 text-center md:text-left">
            <h3 className="text-2xl font-black text-white mb-2">Grow Your Intellectual Network</h3>
            <p className="text-slate-500 font-medium">Sync your reading circles and engage with the world's most deliberate readers.</p>
         </div>
         <button className="relative z-10 px-10 py-5 rounded-2xl bg-indigo-500 text-white font-black text-xs uppercase tracking-widest shadow-2xl shadow-indigo-500/20 hover:scale-105 transition-all">
            Join a Global Salon
         </button>
      </footer>
    </div>
  );
};

const GlobalStat = ({ label, value, icon }: { label: string, value: string, icon: any }) => (
  <div className="text-right">
    <div className="flex items-center justify-end gap-2 text-slate-500 mb-1">
       {icon}
       <span className="text-[9px] font-black uppercase tracking-widest">{label}</span>
    </div>
    <p className="text-2xl font-black text-white tracking-tight">{value}</p>
  </div>
);

const FilterTab = ({ label, active = false }: { label: string, active?: boolean }) => (
  <button className={`px-5 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all ${
    active ? 'bg-indigo-500 text-white shadow-lg' : 'text-slate-500 hover:text-white'
  }`}>
     {label}
  </button>
);
