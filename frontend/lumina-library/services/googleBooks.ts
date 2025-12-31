
import { GoogleBook } from '../types';

export const searchBooks = async (query: string, type: 'general' | 'isbn' = 'general'): Promise<GoogleBook[]> => {
  if (!query) return [];
  
  const searchType = type === 'isbn' ? `isbn:${query}` : query;
  const url = `https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(searchType)}&maxResults=20`;
  
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch books');
    const data = await response.json();
    return data.items || [];
  } catch (error) {
    console.error('Search Error:', error);
    return [];
  }
};
