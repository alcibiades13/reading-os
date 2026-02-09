
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

export interface UserBook extends GoogleBook {
  libraryData: {
    status: LibraryStatus;
    rating: number | null;
    currentPage: number;
    startedAt: string;
    finishedAt?: string;
    isFavorite: boolean;
    review?: string;
    lastOpened?: string;
    shelfId?: string;
    spineColor?: string;
  };
}

// --- CODEX / JOURNAL / MANUSCRIPT ---

export type Mood = 'contemplative' | 'inspired' | 'melancholic' | 'energetic' | 'serene';

export interface JournalEntry {
  id: string;
  date: string;
  title: string;
  content: string;
  mood: Mood;
  tags: string[];
  bookReferenceId?: string;
  isLocked: boolean;
}

export interface Chapter {
  id: string;
  title: string;
  content: string;
  wordCount: number;
  order: number;
  lastEdited: string;
}

export interface Manuscript {
  id: string;
  title: string;
  subtitle: string;
  genre: string;
  chapters: Chapter[];
  coverColor: string;
  targetWordCount: number;
  currentWordCount: number;
}

// --- OSTALI PRETHODNI TIPOVI ---
export interface ImportPayload {
  book: GoogleBook;
  addToLibrary: boolean;
  libraryData: { status: LibraryStatus; rating: number | null };
}

export interface DiscussionTopic {
  id: string; title: string; description: string; lastActivity: string;
  messageCount: number; isLocked: boolean; requiredProgress?: number;
  category: 'general' | 'spoilers' | 'theories' | 'characters';
}

export interface BookClub {
  id: string; name: string; description: string; avatar?: string;
  memberCount: number; currentBookId: string; currentBookTitle: string;
  currentBookCover?: string; averageProgress: number; topics: DiscussionTopic[];
  isPrivate: boolean; accentColor: string;
}

export type MessageAttachmentType = 'book' | 'quote' | 'note' | 'reading_invite';
export interface MessageAttachment {
  type: MessageAttachmentType; id: string; title: string; subtitle?: string;
  image?: string; content?: string; payload?: any;
}
export interface Message {
  id: string; senderId: string; senderName: string; senderAvatar?: string;
  timestamp: string; subject?: string; content: string; attachments: MessageAttachment[];
  isImportant: boolean; status: 'sent' | 'read' | 'pondering';
}
export interface Conversation {
  id: string; participants: { id: string, name: string, avatar?: string }[];
  lastMessage?: Message; unreadCount: number; type: 'direct' | 'club' | 'circle';
  relatedBookIds: string[];
}
export interface Quote {
  id: string; bookId: string; bookTitle: string; bookAuthor: string;
  bookCover?: string; content: string; pageNumber?: number; chapter?: string;
  notes?: string; isPublic: boolean; isFavorite: boolean; tags: string[];
  createdAt: string; updatedAt: string;
}
export type StudyNoteType = 'quote' | 'note' | 'question' | 'insight';
export interface StudyNote {
  id: string; bookId: string; reference: string; type: StudyNoteType;
  content: string; tags: string[]; createdAt: string; updatedAt: string;
}
export type MasteryLevel = 'new' | 'learning' | 'mastered';
export interface VocabularyWord {
  id: string; word: string; bookId?: string; bookTitle?: string;
  bookAuthor?: string; context?: string; pageNumber?: number;
  definition?: string; mastery: MasteryLevel; tags: string[];
  isFavorite: boolean; isPublic: boolean; createdAt: string;
  updatedAt: string; lastReviewedAt?: string; reviewCount: number;
}
export type FeedActivityType = 'finished' | 'started' | 'quote' | 'review' | 'progress' | 'challenge' | 'list' | 'vocabulary' | 'study_session';
export interface FeedPost {
  id: string; user: { name: string; avatar?: string | null };
  type: FeedActivityType; timestamp: string;
  book: { title: string; author: string; cover: string | null };
  content: { rating?: number; review?: string; quote?: string; note?: string; progress?: number; challengeTitle?: string; listTitle?: string; wordCount?: number; studyNoteCount?: number };
  stats: { likes: number; comments: number; hasLiked?: boolean };
}
export type ShelfType = 'mahogany' | 'glass' | 'oak' | 'minimal';
export interface CustomShelf { id: string; title: string; type: ShelfType; bookIds: string[]; }
