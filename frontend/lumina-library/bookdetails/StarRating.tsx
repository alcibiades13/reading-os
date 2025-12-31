
import React, { useState } from 'react';
import { Star, StarHalf } from 'lucide-react';

interface StarRatingProps {
  rating: number; // 0 to 10
  editable?: boolean;
  onChange?: (rating: number) => void;
  size?: number;
}

export const StarRating: React.FC<StarRatingProps> = ({ rating, editable = false, onChange, size = 20 }) => {
  const [hoverRating, setHoverRating] = useState<number | null>(null);

  const displayRating = hoverRating !== null ? hoverRating : rating;

  const handleStarClick = (index: number, isHalf: boolean) => {
    if (!editable || !onChange) return;
    const newRating = (index + 1) - (isHalf ? 0.5 : 0);
    onChange(newRating);
  };

  return (
    <div className="flex items-center gap-1 group/rating">
      {Array.from({ length: 10 }).map((_, i) => {
        const starValue = i + 1;
        const isFull = displayRating >= starValue;
        const isHalf = !isFull && displayRating >= starValue - 0.5;

        return (
          <div 
            key={i} 
            className={`relative transition-transform duration-200 ${editable ? 'cursor-pointer hover:scale-125' : ''}`}
            onMouseEnter={() => editable && setHoverRating(starValue)}
            onMouseLeave={() => editable && setHoverRating(null)}
            onClick={() => handleStarClick(i, false)}
          >
            <Star 
              size={size} 
              className={`${isFull || isHalf ? 'text-amber-400' : 'text-slate-700'} ${isFull ? 'fill-current' : 'fill-none'}`} 
            />
            {isHalf && (
              <div className="absolute inset-0 overflow-hidden w-1/2">
                <Star size={size} className="text-amber-400 fill-current" />
              </div>
            )}
            
            {/* Invisible zones for half-star clicks if editable */}
            {editable && (
              <div 
                className="absolute inset-0 flex"
                onMouseEnter={() => setHoverRating(starValue - 0.5)}
              >
                <div className="w-1/2 h-full" onClick={(e) => { e.stopPropagation(); handleStarClick(i, true); }} />
                <div className="w-1/2 h-full" onClick={(e) => { e.stopPropagation(); handleStarClick(i, false); }} />
              </div>
            )}
          </div>
        );
      })}
      {displayRating > 0 && (
        <span className="ml-2 text-sm font-bold text-amber-400">{displayRating.toFixed(1)}</span>
      )}
    </div>
  );
};
