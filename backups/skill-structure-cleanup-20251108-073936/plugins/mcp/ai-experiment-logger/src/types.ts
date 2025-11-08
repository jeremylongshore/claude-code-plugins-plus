/**
 * AI Experiment Logger - Type Definitions
 */

export interface Experiment {
  id: string;
  date: string; // ISO 8601 format
  aiTool: string;
  prompt: string;
  result: string;
  rating: 1 | 2 | 3 | 4 | 5;
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

export interface ExperimentInput {
  date?: string;
  aiTool: string;
  prompt: string;
  result: string;
  rating: 1 | 2 | 3 | 4 | 5;
  tags?: string[];
}

export interface ExperimentFilters {
  aiTool?: string;
  rating?: number;
  tags?: string[];
  dateFrom?: string;
  dateTo?: string;
  searchQuery?: string;
}

export interface ExperimentStatistics {
  totalExperiments: number;
  averageRating: number;
  toolStats: {
    tool: string;
    count: number;
    averageRating: number;
  }[];
  ratingDistribution: {
    rating: number;
    count: number;
  }[];
  topTags: {
    tag: string;
    count: number;
  }[];
  recentActivity: {
    date: string;
    count: number;
  }[];
}

export interface StorageData {
  experiments: Experiment[];
  version: string;
}
