
import { GoogleBook, LibraryStatus, UserBook } from '../types';

export interface ReadingChallenge {
  id: string;
  title: string;
  goal: number;
  current: number;
  deadline: string;
  color: string;
}

export interface CustomList {
  id: string;
  title: string;
  bookIds: string[];
  description: string;
  icon: string;
}

const STORAGE_KEY = 'lumina_user_library';

const MOCK_LIBRARY: UserBook[] = [
  {
    id: 'f_S8DwAAQBAJ',
    volumeInfo: {
      title: 'Atomic Habits',
      authors: ['James Clear'],
      imageLinks: { thumbnail: 'https://books.google.com/books/content?id=f_S8DwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api' },
      pageCount: 320,
      categories: ['Self-Help', 'Productivity'],
      averageRating: 4.8
    },
    libraryData: {
      status: 'currently_reading',
      rating: null,
      currentPage: 145,
      startedAt: '2024-05-01',
      isFavorite: true,
      lastOpened: new Date().toISOString(),
      shelfId: 'current',
      spineColor: 'bg-indigo-600'
    }
  },
  {
    id: 'D_4yEAAAQBAJ',
    volumeInfo: {
      title: 'Project Hail Mary',
      authors: ['Andy Weir'],
      imageLinks: { thumbnail: 'https://books.google.com/books/content?id=D_4yEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api' },
      pageCount: 496,
      categories: ['Sci-Fi', 'Thriller'],
      averageRating: 4.9
    },
    libraryData: {
      status: 'currently_reading',
      rating: null,
      currentPage: 312,
      startedAt: '2024-05-15',
      isFavorite: false,
      lastOpened: new Date(Date.now() - 3600000).toISOString(),
      shelfId: 'current',
      spineColor: 'bg-sky-700'
    }
  },
  {
    id: '8L_SDwAAQBAJ',
    volumeInfo: {
      title: 'The Midnight Library',
      authors: ['Matt Haig'],
      imageLinks: { thumbnail: 'https://books.google.com/books/content?id=8L_SDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api' },
      pageCount: 304,
      categories: ['Fiction', 'Philosophy'],
      averageRating: 4.5
    },
    libraryData: {
      status: 'read',
      rating: 9.0,
      currentPage: 304,
      startedAt: '2024-04-10',
      finishedAt: '2024-04-25',
      isFavorite: false,
      shelfId: 'finished',
      spineColor: 'bg-emerald-600'
    }
  },
  {
    id: 'B1hGBAAAQBAJ',
    volumeInfo: {
      title: 'Dune',
      authors: ['Frank Herbert'],
      imageLinks: { thumbnail: 'https://books.google.com/books/content?id=B1hGBAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api' },
      pageCount: 688,
      categories: ['Sci-Fi', 'Classics'],
      averageRating: 4.7
    },
    libraryData: {
      status: 'want_to_read',
      rating: null,
      currentPage: 0,
      startedAt: '',
      isFavorite: true,
      shelfId: 'queue',
      spineColor: 'bg-amber-700'
    }
  },
  {
    id: 'Zu9_sz_X_isC',
    volumeInfo: {
      title: 'Thinking, Fast and Slow',
      authors: ['Daniel Kahneman'],
      imageLinks: { thumbnail: 'https://books.google.com/books/content?id=Zu9_sz_X_isC&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api' },
      pageCount: 499,
      categories: ['Psychology', 'Productivity'],
      averageRating: 4.6
    },
    libraryData: {
      status: 'read',
      rating: 9.5,
      currentPage: 499,
      startedAt: '2024-01-10',
      finishedAt: '2024-02-15',
      isFavorite: true,
      shelfId: 'finished',
      spineColor: 'bg-slate-700'
    }
  },
  {
    id: '5XvUDAAAQBAJ',
    volumeInfo: {
      title: "Man's Search for Meaning",
      authors: ['Viktor E. Frankl'],
      imageLinks: { thumbnail: 'https://books.google.com/books/content?id=5XvUDAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api' },
      pageCount: 165,
      categories: ['Psychology', 'Philosophy'],
      averageRating: 4.9
    },
    libraryData: {
      status: 'read',
      rating: 10,
      currentPage: 165,
      startedAt: '2024-03-01',
      finishedAt: '2024-03-05',
      isFavorite: true,
      shelfId: 'finished',
      spineColor: 'bg-zinc-800'
    }
  },
  {
    id: 'XmYpCgAAQBAJ',
    volumeInfo: {
      title: 'Deep Work',
      authors: ['Cal Newport'],
      imageLinks: { thumbnail: 'https://books.google.com/books/content?id=XmYpCgAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api' },
      pageCount: 304,
      categories: ['Self-Help', 'Productivity'],
      averageRating: 4.7
    },
    libraryData: {
      status: 'currently_reading',
      rating: null,
      currentPage: 50,
      startedAt: '2024-05-20',
      isFavorite: false,
      shelfId: 'current',
      spineColor: 'bg-blue-900'
    }
  },
  {
    id: 'iXn5U2uS_88C',
    volumeInfo: {
      title: 'The Great Gatsby',
      authors: ['F. Scott Fitzgerald'],
      imageLinks: { thumbnail: 'https://books.google.com/books/content?id=iXn5U2uS_88C&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api' },
      pageCount: 180,
      categories: ['Fiction', 'Classics'],
      averageRating: 4.4
    },
    libraryData: {
      status: 'read',
      rating: 8.5,
      currentPage: 180,
      startedAt: '2023-12-01',
      finishedAt: '2023-12-15',
      isFavorite: false,
      shelfId: 'finished',
      spineColor: 'bg-emerald-900'
    }
  }
];

export const getUserLibrary = (): UserBook[] => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (!stored) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(MOCK_LIBRARY));
    return MOCK_LIBRARY;
  }
  return JSON.parse(stored);
};

export const getReadingChallenges = (): ReadingChallenge[] => [
  { id: '2025-goal', title: '2025 Yearly Goal', goal: 50, current: 14, deadline: '2025-12-31', color: 'bg-indigo-500' },
  { id: 'sci-fi-summer', title: 'Sci-Fi Summer', goal: 10, current: 3, deadline: '2025-08-31', color: 'bg-sky-500' }
];

export const getCustomLists = (): CustomList[] => [
  { id: 'top-10', title: 'Life Changers', description: 'Books that fundamentally changed my perspective.', bookIds: ['f_S8DwAAQBAJ', '8L_SDwAAQBAJ'], icon: 'Sparkles' },
  { id: 'to-buy', title: 'Hardcover Wishlist', description: 'Books I need to own physically.', bookIds: ['B1hGBAAAQBAJ'], icon: 'Bookmark' }
];

export const getLibraryStats = () => {
  const library = getUserLibrary();
  const finishedThisYear = library.filter(b => b.libraryData.status === 'read' && b.libraryData.finishedAt?.startsWith('2024')).length;
  
  return {
    total: library.length,
    reading: library.filter(b => b.libraryData.status === 'currently_reading').length,
    finished: library.filter(b => b.libraryData.status === 'read').length,
    wishlist: library.filter(b => b.libraryData.status === 'want_to_read').length,
    totalPagesRead: library.reduce((acc, b) => acc + b.libraryData.currentPage, 0),
    favorites: library.filter(b => b.libraryData.isFavorite).length,
    finishedThisYear,
    streak: 12,
    dailyAverage: 42
  };
};
