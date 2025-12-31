
import React from 'react';
import { GoogleBook } from '../types';
import { Star, BookOpen, Calendar, Globe, ExternalLink } from 'lucide-react';

interface BookCardProps {
  book: GoogleBook;
  onClick: (book: GoogleBook) => void;
  onOpenDetail?: (book: GoogleBook) => void;
}

export const BookCard: React.FC<BookCardProps> = ({ book, onClick, onOpenDetail }) => {
  const { volumeInfo } = book;
  const title = volumeInfo.title;
  const authors = volumeInfo.authors?.join(', ') || 'Unknown Author';
  const coverUrl = volumeInfo.imageLinks?.thumbnail?.replace('http:', 'https:') || 
    `https://via.placeholder.com/300x450/1E293B/64748B?text=${encodeURIComponent(title)}`;
  
  return (
    <div 
      className="group cursor-pointer transition-all duration-300 transform hover:-translate-y-2"
      onClick={() => onClick(book)}
    >
      {/* Cover Image Container */}
      <div className="relative aspect-[2/3] w-full rounded-xl overflow-hidden shadow-2xl bg-slate-800 border border-slate-700/50">
        <img 
          src={coverUrl} 
          alt={title} 
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
          loading="lazy"
        />
        
        {/* Hover Overlay */}
        <div className="absolute inset-0 bg-slate-950/80 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col items-center justify-center p-6 text-center space-y-4">
          <div className="flex items-center gap-1.5 text-amber-400">
            <Star size={16} fill="currentColor" />
            <span className="font-semibold">{volumeInfo.averageRating || 'N/A'}</span>
          </div>
          <div className="flex flex-col items-center text-slate-300 text-sm space-y-1">
            <span className="flex items-center gap-1.5">
              <BookOpen size={14} /> {volumeInfo.pageCount || '?'} pages
            </span>
            <span className="flex items-center gap-1.5">
              <Calendar size={14} /> {volumeInfo.publishedDate?.split('-')[0] || 'Unknown'}
            </span>
          </div>
          <div className="flex flex-col gap-2 w-full">
            <button className="w-full px-5 py-2 glass rounded-full text-white text-sm font-medium hover:bg-white/20 transition-colors">
              Quick Preview
            </button>
            {onOpenDetail && (
              <button 
                onClick={(e) => { e.stopPropagation(); onOpenDetail(book); }}
                className="w-full px-5 py-2 rounded-full bg-indigo-500 text-white text-sm font-bold hover:bg-indigo-400 transition-colors flex items-center justify-center gap-2"
              >
                Full Details <ExternalLink size={14} />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Book Info */}
      <div className="mt-4 px-1">
        <h3 className="text-slate-100 font-semibold line-clamp-2 leading-tight group-hover:text-indigo-400 transition-colors">
          {title}
        </h3>
        <p className="text-slate-400 text-sm mt-1 truncate">{authors}</p>
        
        <div className="flex flex-wrap gap-2 mt-3">
          {volumeInfo.publishedDate && (
            <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              {volumeInfo.publishedDate.split('-')[0]}
            </span>
          )}
          {volumeInfo.language && (
            <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              <Globe size={10} /> {volumeInfo.language.toUpperCase()}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
