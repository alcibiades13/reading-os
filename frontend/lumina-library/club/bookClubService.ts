
import { BookClub } from '../types';

export const getBookClubs = (): BookClub[] => [
  {
    id: 'circle-1',
    name: 'The Obsidian Society',
    description: 'A focused group exploring the depths of high-fantasy worldbuilding and complex political structures.',
    memberCount: 128,
    currentBookId: 'B1hGBAAAQBAJ',
    currentBookTitle: 'Dune',
    currentBookCover: 'https://books.google.com/books/content?id=B1hGBAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api',
    averageProgress: 64,
    accentColor: '#6366f1',
    isPrivate: true,
    topics: [
      { id: 't-1', title: 'Political Machinations', description: 'Discussing the Bene Gesserit influence.', lastActivity: '10m ago', messageCount: 42, isLocked: false, category: 'theories' },
      { id: 't-2', title: 'The Ecology of Arrakis', description: 'Technical analysis of the planet.', lastActivity: '2h ago', messageCount: 15, isLocked: false, category: 'general' },
      { id: 't-3', title: 'Endgame Spoilers', description: 'Full book discussion.', lastActivity: '1d ago', messageCount: 89, isLocked: true, requiredProgress: 90, category: 'spoilers' }
    ]
  },
  {
    id: 'circle-2',
    name: 'Philosophy & Flow',
    description: 'Weekly meditations on stoicism, mindfulness, and the intersection of productivity and soul.',
    memberCount: 2560,
    currentBookId: '7S7mDwAAQBAJ',
    currentBookTitle: 'Meditations',
    currentBookCover: 'https://books.google.com/books/content?id=7S7mDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api',
    averageProgress: 30,
    accentColor: '#10b981',
    isPrivate: false,
    topics: [
      { id: 't-4', title: 'Daily Discipline', description: 'Applying Book II to modern work.', lastActivity: '1m ago', messageCount: 156, isLocked: false, category: 'general' },
      { id: 't-5', title: 'The Inner Citadel', description: 'Building mental resilience.', lastActivity: '5h ago', messageCount: 34, isLocked: false, category: 'characters' }
    ]
  },
  {
    id: 'circle-3',
    name: 'Cybernetic Dreams',
    description: 'Speculative fiction, artificial intelligence, and what it means to be human in a digital age.',
    memberCount: 84,
    currentBookId: 'D_4yEAAAQBAJ',
    currentBookTitle: 'Project Hail Mary',
    currentBookCover: 'https://books.google.com/books/content?id=D_4yEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api',
    averageProgress: 88,
    accentColor: '#f59e0b',
    isPrivate: true,
    topics: [
      { id: 't-6', title: 'Astrophage Mechanics', description: 'Scientific feasibility discussion.', lastActivity: '12h ago', messageCount: 27, isLocked: false, category: 'general' }
    ]
  }
];
