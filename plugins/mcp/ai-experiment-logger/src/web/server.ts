/**
 * AI Experiment Logger - Web Server
 * Serves the web UI and provides REST API endpoints
 */

import express from 'express';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { ExperimentStorage } from '../storage.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize storage
const storage = new ExperimentStorage();
await storage.initialize();

// Middleware
app.use(express.json());
app.use(express.static(join(__dirname, 'public')));

// API Routes
app.post('/api/experiments', async (req, res) => {
  try {
    const experiment = await storage.createExperiment(req.body);
    res.json({ success: true, experiment });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to create experiment'
    });
  }
});

app.get('/api/experiments', async (req, res) => {
  try {
    const filters = {
      aiTool: req.query.aiTool as string | undefined,
      rating: req.query.rating ? Number(req.query.rating) : undefined,
      tags: req.query.tags ? (req.query.tags as string).split(',') : undefined,
      dateFrom: req.query.dateFrom as string | undefined,
      dateTo: req.query.dateTo as string | undefined,
      searchQuery: req.query.searchQuery as string | undefined
    };
    const experiments = await storage.listExperiments(filters);
    res.json({ success: true, experiments });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to list experiments'
    });
  }
});

app.get('/api/experiments/:id', async (req, res) => {
  try {
    const experiment = await storage.getExperiment(req.params.id);
    if (!experiment) {
      return res.status(404).json({ success: false, error: 'Experiment not found' });
    }
    res.json({ success: true, experiment });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get experiment'
    });
  }
});

app.put('/api/experiments/:id', async (req, res) => {
  try {
    const experiment = await storage.updateExperiment(req.params.id, req.body);
    if (!experiment) {
      return res.status(404).json({ success: false, error: 'Experiment not found' });
    }
    res.json({ success: true, experiment });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to update experiment'
    });
  }
});

app.delete('/api/experiments/:id', async (req, res) => {
  try {
    const deleted = await storage.deleteExperiment(req.params.id);
    if (!deleted) {
      return res.status(404).json({ success: false, error: 'Experiment not found' });
    }
    res.json({ success: true, message: 'Experiment deleted' });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to delete experiment'
    });
  }
});

app.get('/api/statistics', async (req, res) => {
  try {
    const statistics = await storage.getStatistics();
    res.json({ success: true, statistics });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get statistics'
    });
  }
});

app.get('/api/export', async (req, res) => {
  try {
    const csv = await storage.exportToCSV();
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename=experiments.csv');
    res.send(csv);
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to export experiments'
    });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`AI Experiment Logger web UI running at http://localhost:${PORT}`);
  console.log(`Data stored at: ${storage.getDataFilePath()}`);
});
