
import React, { useState, useEffect, useCallback } from 'react';
import { VocabularyWord, MasteryLevel } from '../types';
import { ChevronLeft, ChevronRight, RotateCcw, Check, Brain, SkipForward, Play, Pause } from 'lucide-react';

interface FlashcardPlayerProps {
  words: VocabularyWord[];
  onComplete: () => void;
  onUpdateMastery: (id: string, level: MasteryLevel) => void;
}

export const FlashcardPlayer: React.FC<FlashcardPlayerProps> = ({ words, onComplete, onUpdateMastery }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [isAutoPlay, setIsAutoPlay] = useState(false);

  const currentWord = words[currentIndex];

  const handleNext = useCallback(() => {
    setIsFlipped(false);
    if (currentIndex < words.length - 1) {
      setCurrentIndex(prev => prev + 1);
    } else {
      onComplete();
    }
  }, [currentIndex, words.length, onComplete]);

  const handlePrev = useCallback(() => {
    setIsFlipped(false);
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
    }
  }, [currentIndex]);

  const handleFlip = useCallback(() => {
    setIsFlipped(prev => !prev);
  }, []);

  useEffect(() => {
    const handleKeys = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        e.preventDefault();
        handleFlip();
      } else if (e.code === 'ArrowRight') {
        handleNext();
      } else if (e.code === 'ArrowLeft') {
        handlePrev();
      }
    };
    window.addEventListener('keydown', handleKeys);
    return () => window.removeEventListener('keydown', handleKeys);
  }, [handleFlip, handleNext, handlePrev]);

  useEffect(() => {
    let interval: number;
    if (isAutoPlay) {
      interval = window.setInterval(() => {
        if (!isFlipped) {
          setIsFlipped(true);
        } else {
          handleNext();
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [isAutoPlay, isFlipped, handleNext]);

  if (!currentWord) return null;

  return (
    <div className="max-w-3xl mx-auto space-y-12">
      {/* Top Bar / Progress */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Brain size={20} />
          </div>
          <div>
            <h3 className="text-white font-bold text-sm">Lexicon Practice</h3>
            <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest">Mastery focus session</p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <button 
            onClick={() => setIsAutoPlay(!isAutoPlay)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-800 text-[10px] font-black uppercase tracking-widest transition-all ${isAutoPlay ? 'bg-indigo-500 text-white border-indigo-500' : 'text-slate-500 hover:text-white'}`}
          >
            {isAutoPlay ? <Pause size={14} /> : <Play size={14} />}
            {isAutoPlay ? 'Auto-play On' : 'Auto-play Off'}
          </button>
          <div className="text-right">
            <p className="text-xs font-black text-white">{currentIndex + 1} <span className="text-slate-600">/ {words.length}</span></p>
            <div className="w-32 h-1 bg-slate-900 rounded-full mt-1">
              <div className="h-full bg-indigo-500 transition-all duration-500" style={{ width: `${((currentIndex + 1) / words.length) * 100}%` }} />
            </div>
          </div>
        </div>
      </div>

      {/* Main Card */}
      <div className={`flip-card w-full aspect-[16/10] md:aspect-[2/1] cursor-pointer ${isFlipped ? 'flipped' : ''}`} onClick={handleFlip}>
        <div className="flip-card-inner">
          {/* Front */}
          <div className="flip-card-front glass bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/20 flex flex-col items-center justify-center p-12 border border-slate-800 shadow-2xl">
            <span className="text-5xl md:text-7xl font-serif text-white tracking-tight text-center selection:bg-indigo-500/30">
              {currentWord.word}
            </span>
            <div className="absolute bottom-8 text-[10px] font-black uppercase tracking-[0.4em] text-indigo-500/40">
              Tap or Space to Flip
            </div>
          </div>
          
          {/* Back */}
          <div className="flip-card-back glass bg-gradient-to-br from-slate-900 via-slate-900 to-emerald-950/20 p-10 flex flex-col border border-emerald-500/20 shadow-2xl overflow-y-auto custom-scrollbar">
            <div className="mb-8">
              <span className="text-xs font-black text-emerald-400 uppercase tracking-widest block mb-2">Definition</span>
              <p className="text-2xl text-white font-medium leading-relaxed">
                {currentWord.definition || "No definition provided."}
              </p>
            </div>

            {currentWord.context && (
              <div className="mb-8 p-6 rounded-2xl bg-emerald-500/5 border-l-4 border-emerald-500/30 italic text-slate-300 font-serif text-lg">
                "{currentWord.context}"
              </div>
            )}

            <div className="mt-auto flex items-center justify-between pt-6 border-t border-slate-800">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-500">
                  <RotateCcw size={14} />
                </div>
                <div>
                  <p className="text-[10px] font-black text-slate-500 uppercase">Book Source</p>
                  <p className="text-xs font-bold text-white">{currentWord.bookTitle || "Manual Entry"}</p>
                </div>
              </div>
              {currentWord.pageNumber && (
                <div className="text-right">
                  <p className="text-[10px] font-black text-slate-500 uppercase">Page</p>
                  <p className="text-xs font-bold text-white">{currentWord.pageNumber}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Mastery Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <button 
          onClick={(e) => { e.stopPropagation(); onUpdateMastery(currentWord.id, 'learning'); handleNext(); }}
          className="p-6 rounded-2xl glass border-slate-800 bg-slate-900/50 hover:bg-amber-500/10 hover:border-amber-500/30 transition-all flex flex-col items-center gap-3 group"
        >
          <div className="w-12 h-12 rounded-xl bg-slate-800 group-hover:bg-amber-500/20 flex items-center justify-center text-slate-500 group-hover:text-amber-400 transition-colors">
            <RotateCcw size={24} />
          </div>
          <span className="text-xs font-black uppercase tracking-widest text-slate-500 group-hover:text-amber-400">Still Learning</span>
        </button>

        <button 
          onClick={(e) => { e.stopPropagation(); onUpdateMastery(currentWord.id, 'mastered'); handleNext(); }}
          className="p-6 rounded-2xl glass border-slate-800 bg-slate-900/50 hover:bg-emerald-500/10 hover:border-emerald-500/30 transition-all flex flex-col items-center gap-3 group"
        >
          <div className="w-12 h-12 rounded-xl bg-slate-800 group-hover:bg-emerald-500/20 flex items-center justify-center text-slate-500 group-hover:text-emerald-400 transition-colors">
            <Check size={24} />
          </div>
          <span className="text-xs font-black uppercase tracking-widest text-slate-500 group-hover:text-emerald-400">Got it!</span>
        </button>

        <button 
          onClick={(e) => { e.stopPropagation(); handleNext(); }}
          className="p-6 rounded-2xl glass border-slate-800 bg-slate-900/50 hover:bg-slate-800 transition-all flex flex-col items-center gap-3 group"
        >
          <div className="w-12 h-12 rounded-xl bg-slate-800 group-hover:bg-slate-700 flex items-center justify-center text-slate-500 group-hover:text-white transition-colors">
            <SkipForward size={24} />
          </div>
          <span className="text-xs font-black uppercase tracking-widest text-slate-500 group-hover:text-white">Skip</span>
        </button>
      </div>

      {/* Navigation Controls */}
      <div className="flex items-center justify-center gap-8 pt-6">
        <button 
          onClick={handlePrev}
          disabled={currentIndex === 0}
          className="p-4 rounded-full border border-slate-800 text-slate-500 hover:text-white hover:bg-slate-900 transition-all disabled:opacity-20 disabled:cursor-not-allowed"
        >
          <ChevronLeft size={24} />
        </button>
        <button 
          onClick={handleNext}
          className="p-4 rounded-full border border-slate-800 text-slate-500 hover:text-white hover:bg-slate-900 transition-all"
        >
          <ChevronRight size={24} />
        </button>
      </div>
    </div>
  );
};
