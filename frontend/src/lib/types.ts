// Mirrors backend Pydantic schemas (app/schemas/*). Keep in sync when contracts change.

export type Cefr = "A1" | "A2" | "B1" | "B2" | "C1" | "C2";
export const CEFR_LEVELS: Cefr[] = ["A1", "A2", "B1", "B2", "C1", "C2"];

export const PARTS_OF_SPEECH = [
  "noun", "verb", "adjective", "adverb", "preposition", "conjunction", "pronoun",
  "article", "numeral", "interjection", "particle", "phrase", "idiom", "other",
] as const;
export type PartOfSpeech = (typeof PARTS_OF_SPEECH)[number];

export interface Preferences {
  target_language: string;
  explanation_language: string;
  show_hindi: boolean;
  cefr_level: Cefr;
  daily_new_cards: number;
  daily_review_limit: number;
  timezone: string;
  theme: "light" | "dark" | "system";
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  preferences: Preferences;
}

export interface Example {
  id?: string;
  sentence: string;
  translation?: string | null;
  kind?: "example" | "conversation" | "source";
}

export interface Card {
  id: string;
  term: string;
  lemma: string;
  sense_key: string;
  language: string;
  part_of_speech: PartOfSpeech;
  cefr_level: Cefr | null;
  translations: Record<string, string>;
  phonetic: string | null;
  explanation: string | null;
  source_sentence: string | null;
  source_reference: string | null;
  synonyms: string[];
  antonyms: string[];
  collocations: string[];
  common_mistakes: string[];
  personal_note: string | null;
  grammar: Record<string, unknown> | null;
  examples: Example[];
  collection_ids: string[];
  status: string;
  created_via: string;
  due_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CardPage {
  items: Card[];
  total: number;
  page: number;
  page_size: number;
}

export interface Collection {
  id: string;
  name: string;
  description: string | null;
  color: string | null;
  is_default: boolean;
  card_count: number;
}

export interface Dashboard {
  total_cards: number;
  new_today: number;
  mastered: number;
  due_now: number;
  difficult: number;
  streak_days: number;
  reviews_today: number;
  retention_30d: number | null;
  minutes_studied_7d: number;
  cefr_distribution: Record<string, number>;
  status_distribution: Record<string, number>;
  last_7_days: { day: string; cards_added: number; reviews: number }[];
  daily_new_goal: number;
  recommendations: string[];
}
