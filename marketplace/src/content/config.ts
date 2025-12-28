import { defineCollection, z } from 'astro:content';

const pluginsCollection = defineCollection({
  type: 'data',
  schema: z.object({
    name: z.string(),
    description: z.string(),
    version: z.string(),
    category: z.enum([
      'automation',
      'business-tools',
      'devops',
      'code-analysis',
      'debugging',
      'ai-ml-assistance',
      'frontend-development',
      'security',
      'testing',
      'documentation',
      'performance',
      'database',
      'cloud-infrastructure',
      'accessibility',
      'mobile',
      'skill-enhancers',
      'other'
    ]),
    keywords: z.array(z.string()),
    author: z.object({
      name: z.string(),
      email: z.string().email().optional(),
      url: z.string().url().optional()
    }),
    featured: z.boolean().optional().default(false),
    repository: z.string().url().optional(),
    license: z.string().optional(),
    installation: z.string(),
    features: z.array(z.string()).optional(),
    requirements: z.array(z.string()).optional(),
    screenshots: z.array(z.string()).optional()
  })
});

const playbooksCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    category: z.string(),
    wordCount: z.number().int().nonnegative().optional(),
    readTime: z.number().int().nonnegative().optional(),
    featured: z.boolean().optional().default(false),
    order: z.number().int().nonnegative().optional(),
    tags: z.array(z.string()).optional().default([]),
    prerequisites: z.array(z.string()).optional().default([]),
    relatedPlaybooks: z.array(z.string()).optional().default([])
  })
});

export const collections = {
  'plugins': pluginsCollection,
  'playbooks': playbooksCollection
};
