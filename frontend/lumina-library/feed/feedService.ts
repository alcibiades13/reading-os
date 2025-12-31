
import { FeedPost } from '../types';

export const getFeedPosts = (): FeedPost[] => {
  return [
    {
      id: 'post-1',
      user: { name: 'Sarah Mitchell', avatar: null },
      type: 'finished',
      timestamp: '2 hours ago',
      book: {
        title: 'The Midnight Library',
        author: 'Matt Haig',
        cover: 'https://books.google.com/books/content?id=8L_SDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api'
      },
      content: {
        rating: 5,
        review: "An absolute masterpiece about life choices and regret. Haig's writing is both philosophical and deeply emotional. Every page resonated with me."
      },
      stats: { likes: 12, comments: 3, hasLiked: false }
    },
    {
      id: 'post-2',
      user: { name: 'Marcus Chen', avatar: null },
      type: 'quote',
      timestamp: '5 hours ago',
      book: {
        title: 'Atomic Habits',
        author: 'James Clear',
        cover: 'https://books.google.com/books/content?id=f_S8DwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api'
      },
      content: {
        quote: 'You do not rise to the level of your goals. You fall to the level of your systems.',
        note: 'This changed how I think about productivity.'
      },
      stats: { likes: 24, comments: 7, hasLiked: true }
    },
    {
      id: 'post-3',
      user: { name: 'Elena Rodriguez', avatar: null },
      type: 'started',
      timestamp: '8 hours ago',
      book: {
        title: 'Project Hail Mary',
        author: 'Andy Weir',
        cover: 'https://books.google.com/books/content?id=D_4yEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api'
      },
      content: {
        note: "Heard so many good things about this! Time to dive into some hard science fiction."
      },
      stats: { likes: 8, comments: 2, hasLiked: false }
    },
    {
      id: 'post-4',
      user: { name: 'David Wilson', avatar: null },
      type: 'progress',
      timestamp: '1 day ago',
      book: {
        title: 'Dune',
        author: 'Frank Herbert',
        cover: 'https://books.google.com/books/content?id=B1hGBAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api'
      },
      content: {
        progress: 75,
        note: "The world-building on Arrakis is unmatched. Paul is truly starting to understand his path."
      },
      stats: { likes: 15, comments: 4, hasLiked: false }
    },
    {
      id: 'post-5',
      user: { name: 'Lumina Community', avatar: null },
      type: 'challenge',
      timestamp: '2 days ago',
      book: {
        title: 'Reading Odyssey 2024',
        author: 'Annual Challenge',
        cover: null
      },
      content: {
        challengeTitle: 'Halfway Point!',
        note: "Over 5,000 readers have reached their mid-year reading goals. Keep those pages turning!"
      },
      stats: { likes: 156, comments: 42, hasLiked: false }
    },
    {
      id: 'post-6',
      user: { name: 'Julian Thorne', avatar: null },
      type: 'list',
      timestamp: '2 days ago',
      book: {
        title: 'Modern Stoicism',
        author: 'Curated List',
        cover: 'https://books.google.com/books/content?id=7S7mDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api'
      },
      content: {
        listTitle: 'Essentials for the Modern Stoic',
        note: "A collection of 12 books to help navigate the chaos of the 21st century."
      },
      stats: { likes: 31, comments: 11, hasLiked: true }
    },
    {
      id: 'post-7',
      user: { name: 'Sophie Banks', avatar: null },
      type: 'review',
      timestamp: '3 days ago',
      book: {
        title: 'Deep Work',
        author: 'Cal Newport',
        cover: 'https://books.google.com/books/content?id=XmYpCgAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api'
      },
      content: {
        rating: 4,
        review: "Practical and convicting. Newport makes a compelling case for intense concentration in an age of distraction. I've already started scheduling my deep work blocks."
      },
      stats: { likes: 19, comments: 5, hasLiked: false }
    }
  ];
};
