
import { VocabularyWord, MasteryLevel } from '../types';

const STORAGE_KEY = 'lumina_vocabulary';

const INITIAL_WORDS: VocabularyWord[] = [
  {
    id: 'v-1',
    word: 'Ethereal',
    bookTitle: 'The Midnight Library',
    bookAuthor: 'Matt Haig',
    context: 'The library felt ethereal, as if it were made of starlight and old paper.',
    pageNumber: 12,
    definition: 'Extremely delicate and light in a way that seems too perfect for this world.',
    mastery: 'learning',
    tags: ['poetic', 'beautiful'],
    isFavorite: true,
    isPublic: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    reviewCount: 5
  },
  {
    id: 'v-2',
    word: 'Mellifluous',
    bookTitle: 'Atomic Habits',
    bookAuthor: 'James Clear',
    context: 'A mellifluous voice can often persuade even the most stubborn of minds.',
    pageNumber: 85,
    definition: 'Sweet or musical; pleasant to hear.',
    mastery: 'new',
    tags: ['phonaesthetics'],
    isFavorite: false,
    isPublic: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    reviewCount: 1
  },
  {
    id: 'v-3',
    word: 'Ephemeral',
    bookTitle: 'Meditations',
    bookAuthor: 'Marcus Aurelius',
    context: 'All things are ephemeral—both the one who remembers and the one remembered.',
    pageNumber: 42,
    definition: 'Lasting for a very short time.',
    mastery: 'mastered',
    tags: ['philosophy', 'time'],
    isFavorite: true,
    isPublic: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    reviewCount: 12
  }
];

export const getVocabulary = (): VocabularyWord[] => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (!stored) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_WORDS));
    return INITIAL_WORDS;
  }
  return JSON.parse(stored);
};

export const saveWord = (word: Partial<VocabularyWord>): VocabularyWord => {
  const words = getVocabulary();
  const now = new Date().toISOString();
  
  if (word.id) {
    const index = words.findIndex(w => w.id === word.id);
    if (index !== -1) {
      const updated = { ...words[index], ...word, updatedAt: now } as VocabularyWord;
      words[index] = updated;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(words));
      return updated;
    }
  }
  
  const newWord: VocabularyWord = {
    ...word,
    id: 'word-' + Math.random().toString(36).substr(2, 9),
    mastery: word.mastery || 'new',
    tags: word.tags || [],
    isFavorite: word.isFavorite || false,
    isPublic: word.isPublic !== undefined ? word.isPublic : true,
    createdAt: now,
    updatedAt: now,
    reviewCount: 0,
    word: word.word || '',
  } as VocabularyWord;

  words.unshift(newWord);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(words));
  return newWord;
};

export const deleteWord = (id: string): void => {
  const words = getVocabulary().filter(w => w.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(words));
};

export const updateMastery = (id: string, level: MasteryLevel): VocabularyWord | null => {
  const words = getVocabulary();
  const index = words.findIndex(w => w.id === id);
  if (index !== -1) {
    words[index].mastery = level;
    words[index].reviewCount += 1;
    words[index].lastReviewedAt = new Date().toISOString();
    words[index].updatedAt = new Date().toISOString();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(words));
    return words[index];
  }
  return null;
};

export const getVocabStats = () => {
  const words = getVocabulary();
  return {
    total: words.length,
    new: words.filter(w => w.mastery === 'new').length,
    learning: words.filter(w => w.mastery === 'learning').length,
    mastered: words.filter(w => w.mastery === 'mastered').length,
    favorites: words.filter(w => w.isFavorite).length,
    byBook: words.reduce((acc: Record<string, number>, w) => {
      const book = w.bookTitle || 'Manual Entry';
      acc[book] = (acc[book] || 0) + 1;
      return acc;
    }, {})
  };
};
