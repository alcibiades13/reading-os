
import { Quote } from '../types';

const STORAGE_KEY = 'lumina_quotes';

const INITIAL_QUOTES: Quote[] = [
  {
    id: 'placeholder-1',
    bookId: 'manual',
    bookTitle: 'Atomic Habits',
    bookAuthor: 'James Clear',
    bookCover: 'https://books.google.com/books/content?id=f_S8DwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api',
    content: "You do not rise to the level of your goals. You fall to the level of your systems.",
    pageNumber: 27,
    chapter: 'Chapter 1',
    notes: "A powerful reminder that progress is a product of daily habits, not once-in-a-lifetime transformations.",
    isPublic: true,
    isFavorite: true,
    tags: ['productivity', 'growth', 'habits'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'placeholder-2',
    bookId: 'manual',
    bookTitle: 'The Midnight Library',
    bookAuthor: 'Matt Haig',
    bookCover: 'https://books.google.com/books/content?id=8L_SDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api',
    content: "Between life and death there is a library, and within that library, the shelves go on forever. Every book provides a chance to try another life you could have lived.",
    pageNumber: 1,
    chapter: 'Prologue',
    notes: "This concept of a library of 'what-ifs' is so hauntingly beautiful.",
    isPublic: true,
    isFavorite: false,
    tags: ['fiction', 'philosophy', 'regret'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'placeholder-3',
    bookId: 'manual',
    bookTitle: 'Dune',
    bookAuthor: 'Frank Herbert',
    bookCover: 'https://books.google.com/books/content?id=B1hGBAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api',
    content: "I must not fear. Fear is the mind-killer. Fear is the little-death that brings total obliteration. I will face my fear.",
    pageNumber: 8,
    chapter: 'The Litany Against Fear',
    notes: "The most iconic mantra in science fiction. Use this when facing high-pressure situations.",
    isPublic: true,
    isFavorite: true,
    tags: ['sci-fi', 'courage', 'classics'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'placeholder-4',
    bookId: 'manual',
    bookTitle: 'Meditations',
    bookAuthor: 'Marcus Aurelius',
    bookCover: 'https://books.google.com/books/content?id=7S7mDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api',
    content: "The happiness of your life depends upon the quality of your thoughts.",
    pageNumber: 42,
    chapter: 'Book IV',
    notes: "Stoicism in its purest form. It reminds me that internal state dictates external reality.",
    isPublic: true,
    isFavorite: true,
    tags: ['stoicism', 'philosophy', 'mindset'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'placeholder-5',
    bookId: 'manual',
    bookTitle: 'Project Hail Mary',
    bookAuthor: 'Andy Weir',
    bookCover: 'https://books.google.com/books/content?id=D_4yEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api',
    content: "Human beings have a remarkable ability to accept the impossible in every situation.",
    pageNumber: 215,
    chapter: 'Chapter 12',
    notes: "Rocky and Ryland's friendship is the highlight of the book, but this observation about human nature is spot on.",
    isPublic: true,
    isFavorite: false,
    tags: ['sci-fi', 'humanity', 'science'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'placeholder-6',
    bookId: 'manual',
    bookTitle: 'Thinking, Fast and Slow',
    bookAuthor: 'Daniel Kahneman',
    bookCover: 'https://books.google.com/books/content?id=Zu9_sz_X_isC&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api',
    content: "A reliable way to make people believe in falsehoods is frequent repetition, because familiarity is not easily distinguished from truth.",
    pageNumber: 62,
    chapter: 'The Illusion of Truth',
    notes: "Deeply relevant to modern social media and political discourse.",
    isPublic: true,
    isFavorite: false,
    tags: ['psychology', 'rationality', 'non-fiction'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'placeholder-7',
    bookId: 'manual',
    bookTitle: 'The Great Gatsby',
    bookAuthor: 'F. Scott Fitzgerald',
    bookCover: 'https://books.google.com/books/content?id=iXn5U2uS_88C&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api',
    content: "So we beat on, boats against the current, borne back ceaselessly into the past.",
    pageNumber: 180,
    chapter: 'Chapter 9',
    notes: "The most beautiful closing line in American literature.",
    isPublic: true,
    isFavorite: true,
    tags: ['classics', 'lit', 'nostalgia'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'placeholder-8',
    bookId: 'manual',
    bookTitle: 'Brave New World',
    bookAuthor: 'Aldous Huxley',
    bookCover: 'https://books.google.com/books/content?id=j6Y9DwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api',
    content: "Words can be like X-rays if you use them properly—they’ll go through anything. You read and you’re pierced.",
    pageNumber: 70,
    chapter: 'Chapter 4',
    notes: "An incredible metaphor for the power of precise language.",
    isPublic: true,
    isFavorite: false,
    tags: ['dystopian', 'language', 'power'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'placeholder-9',
    bookId: 'manual',
    bookTitle: 'Man\'s Search for Meaning',
    bookAuthor: 'Viktor E. Frankl',
    bookCover: 'https://books.google.com/books/content?id=5XvUDAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api',
    content: "Everything can be taken from a man but one thing: the last of the human freedoms—to choose one’s attitude in any given set of circumstances.",
    pageNumber: 66,
    chapter: 'Part One',
    notes: "Crucial perspective on agency and resilience during suffering.",
    isPublic: true,
    isFavorite: true,
    tags: ['psychology', 'resilience', 'meaning'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'placeholder-10',
    bookId: 'manual',
    bookTitle: 'Deep Work',
    bookAuthor: 'Cal Newport',
    bookCover: 'https://books.google.com/books/content?id=XmYpCgAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api',
    content: "Who you are, what you think, feel, and do, what you love—is the sum of what you focus on.",
    pageNumber: 77,
    chapter: 'Part 1',
    notes: "Focus is the ultimate currency of the modern age.",
    isPublic: true,
    isFavorite: false,
    tags: ['productivity', 'focus', 'career'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  }
];

export const getQuotes = (): Quote[] => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (!stored) {
    // Initialize with placeholders if empty
    localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_QUOTES));
    return INITIAL_QUOTES;
  }
  return JSON.parse(stored);
};

export const saveQuote = (quote: Omit<Quote, 'id' | 'createdAt' | 'updatedAt'> & { id?: string }): Quote => {
  const quotes = getQuotes();
  const now = new Date().toISOString();
  
  if (quote.id) {
    const index = quotes.findIndex(q => q.id === quote.id);
    if (index !== -1) {
      const updated = { ...quotes[index], ...quote, updatedAt: now } as Quote;
      quotes[index] = updated;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(quotes));
      return updated;
    }
  }
  
  const newQuote: Quote = {
    ...quote,
    id: Math.random().toString(36).substr(2, 9),
    createdAt: now,
    updatedAt: now,
  } as Quote;
  quotes.unshift(newQuote);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(quotes));
  return newQuote;
};

export const deleteQuote = (id: string): void => {
  const quotes = getQuotes().filter(q => q.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(quotes));
};

export const toggleFavorite = (id: string): Quote | null => {
  const quotes = getQuotes();
  const index = quotes.findIndex(q => q.id === id);
  if (index !== -1) {
    quotes[index].isFavorite = !quotes[index].isFavorite;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(quotes));
    return quotes[index];
  }
  return null;
};
