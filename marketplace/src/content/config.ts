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
      'other'
    ]),
    keywords: z.array(z.string()),
    author: z.object({
      name: z.string(),
      email: z.string().optional(),
      url: z.string().optional()
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

export const collections = {
  'plugins': pluginsCollection
};
