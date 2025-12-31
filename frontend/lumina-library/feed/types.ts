
export interface GoogleBook {
  id: string;
  volumeInfo: {
    title: string;
    authors?: string[];
    publisher?: string;
    publishedDate?: string;
    description?: string;
    industryIdentifiers?: { type: string; identifier: string }[];
    pageCount?: number;
    categories?: string[];
    averageRating?: number;
    ratingsCount?: number;
    imageLinks?: {
      thumbnail?: string;
      smallThumbnail?: string;
      medium?: string;
      large?: string;
    };
    language?: string;
    previewLink?: string;
  };
}

export type LibraryStatus = 'want_to_read' | 'currently_reading' | 'read' | null;

export interface ImportPayload {
  book: GoogleBook;
  addToLibrary: boolean;
  libraryData: {
    status: LibraryStatus;
    rating: number | null;
  };
}

export interface Tag {
  id: string;
  name: string;
  category: 'theme' | 'mood' | 'topic' | 'other';
}

export interface Quote {
  id: string;
  bookId: string;
  bookTitle: string;
  bookAuthor: string;
  bookCover?: string;
  content: string;
  pageNumber?: number;
  chapter?: string;
  notes?: string;
  isPublic: boolean;
  isFavorite: boolean;
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

export type FeedActivityType = 'finished' | 'started' | 'quote' | 'review' | 'progress' | 'challenge' | 'list';

export interface FeedPost {
  id: string;
  user: {
    name: string;
    avatar?: string | null;
  };
  type: FeedActivityType;
  timestamp: string;
  book: {
    title: string;
    author: string;
    cover: string | null;
  };
  content: {
    rating?: number;
    review?: string;
    quote?: string;
    note?: string;
    progress?: number;
    challengeTitle?: string;
    listTitle?: string;
  };
  stats: {
    likes: number;
    comments: number;
    hasLiked?: boolean;
  };
}
