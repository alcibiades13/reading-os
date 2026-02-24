
import { UserBook, GoogleBook } from '../types';

export interface DataConflict {
  id: string;
  field: string;
  sourceA: { value: string; provider: string };
  sourceB: { value: string; provider: string };
  timestamp: string;
  bookTitle: string;
  bookCover?: string;
}

export interface AuthorMergeCandidate {
  id: string;
  primaryName: string;
  variants: string[];
  bookCount: number;
  lastIngested: string;
}

export const getAdminStats = () => ({
  totalCanonicalWorks: 12402,
  pendingConflicts: 42,
  unlinkedAuthors: 156,
  databaseHealth: 98.4,
  ingestionRate: '+12% / mo'
});

export const getPendingConflicts = (): DataConflict[] => [
  {
    id: 'conf-1',
    field: 'Published Date',
    sourceA: { value: '1965-06-01', provider: 'Google Books' },
    sourceB: { value: '1965-08-12', provider: 'Manual Override' },
    timestamp: new Date().toISOString(),
    bookTitle: 'Dune',
    bookCover: 'https://books.google.com/books/content?id=B1hGBAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api'
  },
  {
    id: 'conf-2',
    field: 'Category',
    sourceA: { value: 'Self-Help', provider: 'Google Books' },
    sourceB: { value: 'Psychology / Systems', provider: 'Lumina Curator' },
    timestamp: new Date().toISOString(),
    bookTitle: 'Atomic Habits',
    bookCover: 'https://books.google.com/books/content?id=f_S8DwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api'
  }
];

export const getAuthorMergeCandidates = (): AuthorMergeCandidate[] => [
  { id: 'auth-1', primaryName: 'J.R.R. Tolkien', variants: ['John Ronald Reuel Tolkien', 'Tolkien, J. R. R.'], bookCount: 24, lastIngested: '2 days ago' },
  { id: 'auth-2', primaryName: 'Marcus Aurelius', variants: ['Marko Aurelije', 'Aurelius Antoninus'], bookCount: 15, lastIngested: '1 week ago' }
];
