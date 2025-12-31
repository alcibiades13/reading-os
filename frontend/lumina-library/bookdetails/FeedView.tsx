
import React, { useState, useEffect } from 'react';
import { FeedPostCard } from '../components/FeedPostCard';
import { getFeedPosts } from '../services/feedService';
import { FeedPost } from '../types';
import { Users, TrendingUp, Sparkles, Filter, ChevronDown } from 'lucide-react';

interface FeedViewProps {
  onOpenBook?: (title: string) => void;
}

export const FeedView: React.FC<FeedViewProps> = ({ onOpenBook }) => {
  const [posts, setPosts] = useState<FeedPost[]>([]);
  const [activeTab, setActiveTab] = useState<'all' | 'following' | 'books' | 'genres'>('all');

  useEffect(() => {
    // Simulate API fetch delay
    setTimeout(() => {
      setPosts(getFeedPosts());
    }, 400);
  }, []);

  return (
    <div className="animate-in fade-in duration-700">
      {/* Page Header */}
      <div className="max-w-4xl mx-auto pt-12 pb-8 px-6">
        <header className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Users className="text-indigo-400" size={24} />
            </div>
            <span className="text-sm font-bold text-indigo-400 uppercase tracking-[0.3em]">Activity Stream</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-white tracking-tight mb-4">
            Lumina <span className="text-indigo-500">Feed</span>
          </h1>
          <p className="text-slate-400 text-lg leading-relaxed">
            See what your reading community is up to. Discover new books, insights, and reading milestones.
          </p>
        </header>

        {/* Filter Tabs */}
        <div className="flex items-center justify-between mb-8 overflow-x-auto pb-2 scrollbar-hide">
          <div className="flex items-center gap-1 p-1 bg-slate-900/80 rounded-2xl border border-slate-800">
            <TabButton active={activeTab === 'all'} onClick={() => setActiveTab('all')} label="All Activity" icon={<Sparkles size={14} />} />
            <TabButton active={activeTab === 'following'} onClick={() => setActiveTab('following')} label="Following" icon={<Users size={14} />} />
            <TabButton active={activeTab === 'books'} onClick={() => setActiveTab('books')} label="My Books" icon={<TrendingUp size={14} />} />
          </div>

          <button className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-all text-sm font-bold ml-4">
            <Filter size={16} />
            Filters
            <ChevronDown size={14} />
          </button>
        </div>

        {/* Feed Stream */}
        <div className="space-y-8">
          {posts.length === 0 ? (
            <div className="space-y-8">
              {[1, 2, 3].map((n) => (
                <div key={n} className="h-64 glass bg-slate-900/50 rounded-2xl animate-pulse flex items-center justify-center">
                  <div className="w-12 h-12 rounded-full border-4 border-slate-800 border-t-indigo-500 animate-spin" />
                </div>
              ))}
            </div>
          ) : (
            <>
              {posts.map((post) => (
                <FeedPostCard 
                  key={post.id} 
                  post={post} 
                  onOpenBook={onOpenBook}
                />
              ))}
              
              <div className="flex justify-center pt-8">
                <button className="px-8 py-4 rounded-2xl bg-slate-900 border border-slate-800 text-white font-bold hover:bg-slate-800 hover:border-slate-700 transition-all flex items-center gap-3 active:scale-95">
                  <TrendingUp size={20} className="text-indigo-400" />
                  Load Older Activity
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const TabButton = ({ active, onClick, label, icon }: { active: boolean, onClick: () => void, label: string, icon: any }) => (
  <button 
    onClick={onClick}
    className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all ${
      active ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:text-slate-300'
    }`}
  >
    {icon}
    {label}
  </button>
);
