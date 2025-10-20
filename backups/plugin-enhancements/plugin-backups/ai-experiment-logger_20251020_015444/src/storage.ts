/**
 * AI Experiment Logger - Storage Layer
 * Handles data persistence to JSON file
 */

import { readFile, writeFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';
import type { Experiment, ExperimentInput, ExperimentFilters, ExperimentStatistics, StorageData } from './types.js';

const DATA_DIR = join(homedir(), '.ai-experiment-logger');
const DATA_FILE = join(DATA_DIR, 'experiments.json');
const VERSION = '1.0.0';

export class ExperimentStorage {
  private data: StorageData = {
    experiments: [],
    version: VERSION
  };

  async initialize(): Promise<void> {
    // Ensure data directory exists
    if (!existsSync(DATA_DIR)) {
      await mkdir(DATA_DIR, { recursive: true });
    }

    // Load existing data
    if (existsSync(DATA_FILE)) {
      try {
        const content = await readFile(DATA_FILE, 'utf-8');
        this.data = JSON.parse(content);
      } catch (error) {
        console.error('Error loading data:', error);
        // Start with fresh data
        await this.save();
      }
    } else {
      await this.save();
    }
  }

  private async save(): Promise<void> {
    await writeFile(DATA_FILE, JSON.stringify(this.data, null, 2), 'utf-8');
  }

  private generateId(): string {
    return `exp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  async createExperiment(input: ExperimentInput): Promise<Experiment> {
    const now = new Date().toISOString();
    const experiment: Experiment = {
      id: this.generateId(),
      date: input.date || now,
      aiTool: input.aiTool,
      prompt: input.prompt,
      result: input.result,
      rating: input.rating,
      tags: input.tags || [],
      createdAt: now,
      updatedAt: now
    };

    this.data.experiments.push(experiment);
    await this.save();
    return experiment;
  }

  async getExperiment(id: string): Promise<Experiment | null> {
    return this.data.experiments.find(exp => exp.id === id) || null;
  }

  async listExperiments(filters?: ExperimentFilters): Promise<Experiment[]> {
    let experiments = [...this.data.experiments];

    if (filters) {
      if (filters.aiTool) {
        experiments = experiments.filter(exp =>
          exp.aiTool.toLowerCase().includes(filters.aiTool!.toLowerCase())
        );
      }

      if (filters.rating !== undefined) {
        experiments = experiments.filter(exp => exp.rating === filters.rating);
      }

      if (filters.tags && filters.tags.length > 0) {
        experiments = experiments.filter(exp =>
          filters.tags!.some(tag => exp.tags.includes(tag))
        );
      }

      if (filters.dateFrom) {
        experiments = experiments.filter(exp => exp.date >= filters.dateFrom!);
      }

      if (filters.dateTo) {
        experiments = experiments.filter(exp => exp.date <= filters.dateTo!);
      }

      if (filters.searchQuery) {
        const query = filters.searchQuery.toLowerCase();
        experiments = experiments.filter(exp =>
          exp.aiTool.toLowerCase().includes(query) ||
          exp.prompt.toLowerCase().includes(query) ||
          exp.result.toLowerCase().includes(query) ||
          exp.tags.some(tag => tag.toLowerCase().includes(query))
        );
      }
    }

    // Sort by date (newest first)
    return experiments.sort((a, b) =>
      new Date(b.date).getTime() - new Date(a.date).getTime()
    );
  }

  async updateExperiment(id: string, updates: Partial<ExperimentInput>): Promise<Experiment | null> {
    const index = this.data.experiments.findIndex(exp => exp.id === id);
    if (index === -1) return null;

    const experiment = this.data.experiments[index];
    const updated: Experiment = {
      ...experiment,
      ...updates,
      updatedAt: new Date().toISOString()
    };

    this.data.experiments[index] = updated;
    await this.save();
    return updated;
  }

  async deleteExperiment(id: string): Promise<boolean> {
    const index = this.data.experiments.findIndex(exp => exp.id === id);
    if (index === -1) return false;

    this.data.experiments.splice(index, 1);
    await this.save();
    return true;
  }

  async getStatistics(): Promise<ExperimentStatistics> {
    const experiments = this.data.experiments;
    const totalExperiments = experiments.length;

    if (totalExperiments === 0) {
      return {
        totalExperiments: 0,
        averageRating: 0,
        toolStats: [],
        ratingDistribution: [],
        topTags: [],
        recentActivity: []
      };
    }

    // Average rating
    const averageRating = experiments.reduce((sum, exp) => sum + exp.rating, 0) / totalExperiments;

    // Tool statistics
    const toolMap = new Map<string, { count: number; totalRating: number }>();
    experiments.forEach(exp => {
      const current = toolMap.get(exp.aiTool) || { count: 0, totalRating: 0 };
      toolMap.set(exp.aiTool, {
        count: current.count + 1,
        totalRating: current.totalRating + exp.rating
      });
    });

    const toolStats = Array.from(toolMap.entries())
      .map(([tool, stats]) => ({
        tool,
        count: stats.count,
        averageRating: stats.totalRating / stats.count
      }))
      .sort((a, b) => b.count - a.count);

    // Rating distribution
    const ratingMap = new Map<number, number>();
    experiments.forEach(exp => {
      ratingMap.set(exp.rating, (ratingMap.get(exp.rating) || 0) + 1);
    });

    const ratingDistribution = Array.from(ratingMap.entries())
      .map(([rating, count]) => ({ rating, count }))
      .sort((a, b) => a.rating - b.rating);

    // Top tags
    const tagMap = new Map<string, number>();
    experiments.forEach(exp => {
      exp.tags.forEach(tag => {
        tagMap.set(tag, (tagMap.get(tag) || 0) + 1);
      });
    });

    const topTags = Array.from(tagMap.entries())
      .map(([tag, count]) => ({ tag, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    // Recent activity (last 30 days)
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

    const activityMap = new Map<string, number>();
    experiments
      .filter(exp => new Date(exp.date) >= thirtyDaysAgo)
      .forEach(exp => {
        const dateStr = exp.date.split('T')[0];
        activityMap.set(dateStr, (activityMap.get(dateStr) || 0) + 1);
      });

    const recentActivity = Array.from(activityMap.entries())
      .map(([date, count]) => ({ date, count }))
      .sort((a, b) => a.date.localeCompare(b.date));

    return {
      totalExperiments,
      averageRating: Math.round(averageRating * 100) / 100,
      toolStats,
      ratingDistribution,
      topTags,
      recentActivity
    };
  }

  async exportToCSV(): Promise<string> {
    const experiments = await this.listExperiments();

    // CSV header
    let csv = 'ID,Date,AI Tool,Prompt,Result,Rating,Tags,Created At,Updated At\n';

    // CSV rows
    experiments.forEach(exp => {
      const row = [
        exp.id,
        exp.date,
        `"${exp.aiTool.replace(/"/g, '""')}"`,
        `"${exp.prompt.replace(/"/g, '""')}"`,
        `"${exp.result.replace(/"/g, '""')}"`,
        exp.rating,
        `"${exp.tags.join(', ')}"`,
        exp.createdAt,
        exp.updatedAt
      ].join(',');
      csv += row + '\n';
    });

    return csv;
  }

  getDataFilePath(): string {
    return DATA_FILE;
  }
}
