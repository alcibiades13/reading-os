
import React from 'react';

export const SkeletonCard: React.FC = () => {
  return (
    <div className="flex flex-col space-y-3 animate-pulse">
      <div className="relative aspect-[2/3] w-full bg-slate-800 rounded-xl overflow-hidden">
        <div className="absolute inset-0 shimmer" />
      </div>
      <div className="space-y-2 px-1">
        <div className="h-4 bg-slate-800 rounded w-3/4 shimmer" />
        <div className="h-3 bg-slate-800 rounded w-1/2 shimmer" />
        <div className="flex gap-2 mt-2">
          <div className="h-4 bg-slate-800 rounded w-8 shimmer" />
          <div className="h-4 bg-slate-800 rounded w-8 shimmer" />
        </div>
      </div>
    </div>
  );
};
