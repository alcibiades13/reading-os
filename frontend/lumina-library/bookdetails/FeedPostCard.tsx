
import React, { useState } from 'react';
import { FeedPost, FeedActivityType } from '../types';
import { 
  Heart, MessageCircle, Share2, CheckCircle, BookOpen, 
  Quote as QuoteIcon, MessageSquare, TrendingUp, Star, MoreHorizontal, ExternalLink
} from 'lucide-react';

interface FeedPostCardProps {
  post: FeedPost;
  onOpenBook?: (title: string) => void;
}

export const FeedPostCard: React.FC<FeedPostCardProps> = ({ post, onOpenBook }) => {
  const [liked, setLiked] = useState(post.stats.hasLiked);
  const [likeCount, setLikeCount] = useState(post.stats.likes);

  const toggleLike = () => {
    setLiked(!liked);
    setLikeCount(prev => liked ? prev - 1 : prev + 1);
  };

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase();
  };

  const activityConfig: Record<FeedActivityType, { icon: any, label: string, color: string }> = {
    finished: { icon: <CheckCircle size={14} />, label: 'Finished', color: 'text-emerald-400 bg-emerald-400/10' },
    started: { icon: <BookOpen size={14} />, label: 'Started Reading', color: 'text-indigo-400 bg-indigo-400/10' },
    quote: { icon: <QuoteIcon size={14} />, label: 'Shared a Quote', color: 'text-purple-400 bg-purple-400/10' },
    review: { icon: <MessageSquare size={14} />, label: 'Reviewed', color: 'text-sky-400 bg-sky-400/10' },
    progress: { icon: <TrendingUp size={14} />, label: 'Reading Progress', color: 'text-amber-400 bg-amber-400/10' },
    challenge: { icon: <Star size={14} />, label: 'Challenge Update', color: 'text-pink-400 bg-pink-400/10' },
    list: { icon: <MessageCircle size={14} />, label: 'Created a List', color: 'text-indigo-400 bg-indigo-400/10' }
  };

  const config = activityConfig[post.type];

  return (
    <div className="group glass bg-slate-900/50 rounded-2xl border border-slate-800 p-6 hover:border-indigo-500/50 transition-all duration-300 animate-in fade-in slide-in-from-bottom-4 shadow-xl shadow-slate-950/20">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold ring-2 ring-slate-800 ring-offset-2 ring-offset-slate-900">
            {getInitials(post.user.name)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-white hover:text-indigo-400 transition-colors cursor-pointer">{post.user.name}</span>
              <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${config.color}`}>
                {config.icon}
                {config.label}
              </div>
            </div>
            <span className="text-xs text-slate-500">{post.timestamp}</span>
          </div>
        </div>
        <button className="text-slate-600 hover:text-slate-400 transition-colors p-2 rounded-full hover:bg-slate-800">
          <MoreHorizontal size={18} />
        </button>
      </div>

      {/* Content Area */}
      <div className="flex gap-6 mb-6">
        {/* Book Cover */}
        {post.book.cover && (
          <div 
            className="hidden sm:block shrink-0 w-[80px] h-[120px] rounded-lg overflow-hidden shadow-2xl ring-1 ring-white/10 group-hover:scale-105 transition-transform duration-300 cursor-pointer"
            onClick={() => onOpenBook?.(post.book.title)}
          >
            <img src={post.book.cover} alt={post.book.title} className="w-full h-full object-cover" />
          </div>
        )}

        <div className="flex-1 min-w-0">
          <div className="mb-3">
            <h3 
              className="text-lg font-bold text-slate-100 group-hover:text-indigo-400 transition-colors cursor-pointer truncate flex items-center gap-2"
              onClick={() => onOpenBook?.(post.book.title)}
            >
              {post.book.title}
              <ExternalLink size={14} className="opacity-0 group-hover:opacity-100 transition-opacity" />
            </h3>
            <p className="text-sm text-slate-400">by {post.book.author}</p>
          </div>

          {/* Activity Specific Content */}
          <div className="space-y-3">
            {post.type === 'quote' && post.content.quote && (
              <blockquote className="relative p-4 rounded-xl bg-indigo-500/5 border-l-4 border-indigo-500 italic text-slate-200 font-serif text-base leading-relaxed">
                "{post.content.quote}"
              </blockquote>
            )}

            {post.content.review && (
              <p className="text-sm text-slate-300 leading-relaxed italic line-clamp-3">
                "{post.content.review}"
              </p>
            )}

            {post.type === 'progress' && post.content.progress && (
              <div className="w-full bg-slate-800 rounded-full h-2 mb-2 relative overflow-hidden">
                <div 
                  className="bg-indigo-500 h-full rounded-full transition-all duration-1000 ease-out" 
                  style={{ width: `${post.content.progress}%` }} 
                />
                <span className="absolute right-0 -top-6 text-[10px] font-bold text-indigo-400">{post.content.progress}% Complete</span>
              </div>
            )}

            {post.content.rating && (
              <div className="flex gap-0.5">
                {[1, 2, 3, 4, 5].map((s) => (
                  <Star key={s} size={14} className={s <= post.content.rating! ? 'text-amber-400' : 'text-slate-700'} fill={s <= post.content.rating! ? 'currentColor' : 'none'} />
                ))}
              </div>
            )}

            {post.content.note && (
              <p className="text-sm text-slate-400 line-clamp-2">
                {post.content.note}
              </p>
            )}
            
            {post.content.challengeTitle && (
              <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20">
                <p className="text-sm font-bold text-indigo-400">{post.content.challengeTitle}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <button 
            onClick={toggleLike}
            className={`flex items-center gap-2 group/btn transition-colors ${liked ? 'text-indigo-400' : 'text-slate-500 hover:text-indigo-400'}`}
          >
            <div className={`p-2 rounded-full transition-colors ${liked ? 'bg-indigo-400/10' : 'group-hover/btn:bg-indigo-400/10'}`}>
              <Heart size={18} fill={liked ? 'currentColor' : 'none'} className={liked ? 'animate-in zoom-in-50 duration-300' : ''} />
            </div>
            <span className="text-xs font-bold">{likeCount}</span>
          </button>
          
          <button className="flex items-center gap-2 group/btn text-slate-500 hover:text-sky-400 transition-colors">
            <div className="p-2 rounded-full group-hover/btn:bg-sky-400/10 transition-colors">
              <MessageCircle size={18} />
            </div>
            <span className="text-xs font-bold">{post.stats.comments}</span>
          </button>
        </div>

        <button className="flex items-center gap-2 group/btn text-slate-500 hover:text-emerald-400 transition-colors">
          <div className="p-2 rounded-full group-hover/btn:bg-emerald-400/10 transition-colors">
            <Share2 size={18} />
          </div>
          <span className="text-xs font-bold hidden sm:inline">Share Insight</span>
        </button>
      </div>
    </div>
  );
};
