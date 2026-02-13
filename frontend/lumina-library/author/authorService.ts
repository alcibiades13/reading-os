
import { Author, GoogleBook } from '../types';
import { searchBooks } from './googleBooks';

export const getAuthorDetails = async (name: string): Promise<Author> => {
  // In a real app, this might fetch from a specific DB or Wikipedia API.
  // Here we simulate based on the name.
  
  const mockBios: Record<string, string> = {
    'James Clear': 'James Clear is an American author and speaker, best known for his book Atomic Habits. His work focuses on habits, decision making, and continuous improvement.',
    'Marcus Aurelius': 'Marcus Aurelius was Roman Emperor from 161 to 180 and a Stoic philosopher. He was the last of the rulers known as the Five Good Emperors.',
    'Matt Haig': 'Matt Haig is an English author and journalist. He has written both fiction and non-fiction for children and adults, often focusing on mental health.',
    'Frank Herbert': 'Frank Herbert was an American science fiction novelist, best known for the 1965 novel Dune and its five sequels.',
    'Andy Weir': 'Andy Weir is an American novelist whose debut novel, The Martian, was adapted into a major motion picture directed by Ridley Scott.',
  };

  return {
    name,
    biography: mockBios[name] || `${name} is an influential creator whose works have left a lasting impact on literature and human thought. Through their unique perspective, they challenge readers to explore new dimensions of the intellectual landscape.`,
    birthDate: 'Mid 20th Century',
    nationality: 'Cosmopolitan',
    portraitUrl: `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=6366f1&color=fff&size=512`,
    notableWorks: ['The Opus', 'Echoes of Time', 'The Silent Library'],
    similarAuthors: ['Ryan Holiday', 'Robert Greene', 'Yuval Noah Harari'],
    tags: ['Philosophical', 'Strategic', 'Visionary']
  };
};

export const getBooksByAuthor = async (authorName: string): Promise<GoogleBook[]> => {
  return await searchBooks(`inauthor:"${authorName}"`, 'general');
};
