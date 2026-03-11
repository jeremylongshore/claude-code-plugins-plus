# Evernote Cost Tuning - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Quota Monitoring

```javascript
// services/quota-service.js
const Evernote = require('evernote');

class QuotaService {
  constructor(userStore) {
    this.userStore = userStore;
  }

  /**
   * Get current quota status
   */
  async getQuotaStatus() {
    const user = await this.userStore.getUser();
    const accounting = user.accounting;

    const uploadLimit = accounting.uploadLimit;
    const uploaded = accounting.uploaded;
    const remaining = uploadLimit - uploaded;
    const usagePercent = (uploaded / uploadLimit) * 100;

    return {
      tier: this.getTierName(user.privilege),
      uploadLimit: this.formatBytes(uploadLimit),
      uploaded: this.formatBytes(uploaded),
      remaining: this.formatBytes(remaining),
      usagePercent: usagePercent.toFixed(1) + '%',
      resetsAt: new Date(accounting.uploadLimitEnd),
      daysUntilReset: this.daysUntil(accounting.uploadLimitEnd),

      // Raw values for calculations
      raw: {
        uploadLimit,
        uploaded,
        remaining
      }
    };
  }

  /**
   * Check if upload is safe
   */
  async canUpload(fileSizeBytes) {
    const status = await this.getQuotaStatus();
    return status.raw.remaining >= fileSizeBytes;
  }

  /**
   * Estimate uploads remaining
   */
  async estimateRemainingUploads(avgFileSizeBytes) {
    const status = await this.getQuotaStatus();
    return Math.floor(status.raw.remaining / avgFileSizeBytes);
  }

  /**
   * Check if approaching limit
   */
  async isApproachingLimit(thresholdPercent = 80) {
    const status = await this.getQuotaStatus();
    return parseFloat(status.usagePercent) >= thresholdPercent;
  }

  getTierName(privilege) {
    const tiers = {
      1: 'Basic',
      2: 'Personal (Premium)',
      3: 'VIP',
      5: 'Professional'
    };
    return tiers[privilege] || 'Unknown';
  }

  formatBytes(bytes) {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    let i = 0;
    while (bytes >= 1024 && i < units.length - 1) {
      bytes /= 1024;
      i++;
    }
    return `${bytes.toFixed(2)} ${units[i]}`;
  }

  daysUntil(timestamp) {
    const ms = timestamp - Date.now();
    return Math.max(0, Math.ceil(ms / (24 * 60 * 60 * 1000)));
  }
}

module.exports = QuotaService;
```

### Step 2: Resource Optimization

```javascript
// services/resource-optimizer.js
const sharp = require('sharp');
const path = require('path');

class ResourceOptimizer {
  constructor(options = {}) {
    this.maxImageWidth = options.maxImageWidth || 1920;
    this.maxImageHeight = options.maxImageHeight || 1080;
    this.imageQuality = options.imageQuality || 80;
    this.maxFileSizeMB = options.maxFileSizeMB || 10;
  }

  /**
   * Optimize image before upload
   */
  async optimizeImage(buffer, originalName) {
    const originalSize = buffer.length;

    // Determine format
    const ext = path.extname(originalName).toLowerCase();
    const format = ext === '.png' ? 'png' : 'jpeg';

    // Resize and compress
    let optimized = sharp(buffer)
      .resize(this.maxImageWidth, this.maxImageHeight, {
        fit: 'inside',
        withoutEnlargement: true
      });

    if (format === 'jpeg') {
      optimized = optimized.jpeg({ quality: this.imageQuality });
    } else {
      optimized = optimized.png({ compressionLevel: 9 });
    }

    const result = await optimized.toBuffer();
    const savings = originalSize - result.length;
    const savingsPercent = (savings / originalSize) * 100;

    console.log(`Image optimized: ${this.formatBytes(savings)} saved (${savingsPercent.toFixed(1)}%)`);

    return {
      buffer: result,
      originalSize,
      optimizedSize: result.length,
      savings,
      savingsPercent
    };
  }

  /**
   * Estimate if file needs optimization
   */
  shouldOptimize(fileSizeBytes, mimeType) {
    // Images over 500KB should be optimized
    if (mimeType.startsWith('image/') && fileSizeBytes > 500 * 1024) {
      return true;
    }

    // Files over max size must be optimized
    if (fileSizeBytes > this.maxFileSizeMB * 1024 * 1024) {
      return true;
    }

    return false;
  }

  /**
   * Compress PDF
   */
  async compressPDF(buffer) {
    // Requires external tool like ghostscript
    // This is a placeholder - implement based on your needs
    return buffer;
  }

  formatBytes(bytes) {
    const units = ['B', 'KB', 'MB'];
    let i = 0;
    while (bytes >= 1024 && i < units.length - 1) {
      bytes /= 1024;
      i++;
    }
    return `${bytes.toFixed(2)} ${units[i]}`;
  }
}

module.exports = ResourceOptimizer;
```

### Step 3: Efficient Note Creation

```javascript
// services/efficient-note-service.js

class EfficientNoteService {
  constructor(noteStore, quotaService, optimizer) {
    this.noteStore = noteStore;
    this.quota = quotaService;
    this.optimizer = optimizer;
  }

  /**
   * Create note with size checking
   */
  async createNoteWithQuotaCheck(note, resources = []) {
    // Calculate total size
    let totalSize = Buffer.byteLength(note.content, 'utf8');
    for (const resource of resources) {
      totalSize += resource.data.size;
    }

    // Check quota
    const canUpload = await this.quota.canUpload(totalSize);
    if (!canUpload) {
      const status = await this.quota.getQuotaStatus();
      throw new Error(
        `Insufficient quota. Need ${this.formatBytes(totalSize)}, ` +
        `have ${status.remaining}. Resets in ${status.daysUntilReset} days.`
      );
    }

    // Optimize resources if needed
    const optimizedResources = [];
    for (const resource of resources) {
      if (this.optimizer.shouldOptimize(resource.data.size, resource.mime)) {
        const optimized = await this.optimizer.optimizeImage(
          resource.data.body,
          resource.attributes?.fileName || 'image'
        );
        resource.data.body = optimized.buffer;
        resource.data.size = optimized.buffer.length;
        resource.data.bodyHash = this.computeHash(optimized.buffer);
      }
      optimizedResources.push(resource);
    }

    note.resources = optimizedResources;
    return this.noteStore.createNote(note);
  }

  /**
   * Create note with deferred resources
   */
  async createNoteDeferResources(title, content, resourcePaths) {
    // Create note without resources first
    const note = new Evernote.Types.Note();
    note.title = title;
    note.content = this.wrapENML(content);

    const created = await this.noteStore.createNote(note);

    // Add resources in background
    for (const resourcePath of resourcePaths) {
      await this.addResourceToNote(created.guid, resourcePath);
    }

    return created;
  }

  /**
   * Batch small notes together
   */
  async createNotesEfficiently(notes) {
    // Sort by size (smallest first)
    notes.sort((a, b) => {
      const sizeA = Buffer.byteLength(a.content, 'utf8');
      const sizeB = Buffer.byteLength(b.content, 'utf8');
      return sizeA - sizeB;
    });

    const results = [];
    const status = await this.quota.getQuotaStatus();
    let usedQuota = 0;

    for (const note of notes) {
      const noteSize = Buffer.byteLength(note.content, 'utf8');

      if (usedQuota + noteSize > status.raw.remaining) {
        console.warn(`Quota limit reached. ${notes.length - results.length} notes skipped.`);
        break;
      }

      try {
        const result = await this.noteStore.createNote(note);
        results.push({ success: true, note: result });
        usedQuota += noteSize;
      } catch (error) {
        results.push({ success: false, error: error.message });
      }
    }

    return results;
  }

  computeHash(buffer) {
    const crypto = require('crypto');
    return crypto.createHash('md5').update(buffer).digest();
  }

  wrapENML(content) {
    return `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>${content}</en-note>`;
  }

  formatBytes(bytes) {
    const units = ['B', 'KB', 'MB'];
    let i = 0;
    while (bytes >= 1024 && i < units.length - 1) {
      bytes /= 1024;
      i++;
    }
    return `${bytes.toFixed(2)} ${units[i]}`;
  }
}

module.exports = EfficientNoteService;
```

### Step 4: Storage Cleanup

```javascript
// services/storage-cleanup.js

class StorageCleanup {
  constructor(noteStore) {
    this.noteStore = noteStore;
  }

  /**
   * Find large notes
   */
  async findLargeNotes(thresholdMB = 5) {
    const filter = new Evernote.NoteStore.NoteFilter({
      ascending: false,
      order: Evernote.Types.NoteSortOrder.SIZE
    });

    const spec = new Evernote.NoteStore.NotesMetadataResultSpec({
      includeTitle: true,
      includeContentLength: true,
      includeCreated: true,
      includeNotebookGuid: true
    });

    const result = await this.noteStore.findNotesMetadata(filter, 0, 100, spec);

    const thresholdBytes = thresholdMB * 1024 * 1024;
    return result.notes.filter(note =>
      note.contentLength > thresholdBytes
    );
  }

  /**
   * Find duplicate notes (by title)
   */
  async findPotentialDuplicates() {
    const spec = new Evernote.NoteStore.NotesMetadataResultSpec({
      includeTitle: true,
      includeCreated: true,
      includeContentLength: true
    });

    const filter = new Evernote.NoteStore.NoteFilter({});
    const all = await this.noteStore.findNotesMetadata(filter, 0, 1000, spec);

    // Group by title
    const byTitle = {};
    for (const note of all.notes) {
      const key = note.title.toLowerCase().trim();
      if (!byTitle[key]) {
        byTitle[key] = [];
      }
      byTitle[key].push(note);
    }

    // Find duplicates
    const duplicates = [];
    for (const [title, notes] of Object.entries(byTitle)) {
      if (notes.length > 1) {
        duplicates.push({
          title,
          count: notes.length,
          notes: notes.map(n => ({
            guid: n.guid,
            created: new Date(n.created),
            size: this.formatBytes(n.contentLength)
          }))
        });
      }
    }

    return duplicates;
  }

  /**
   * Find old, unmodified notes
   */
  async findStaleNotes(daysOld = 365) {
    const cutoff = Date.now() - (daysOld * 24 * 60 * 60 * 1000);

    const filter = new Evernote.NoteStore.NoteFilter({
      ascending: true,
      order: Evernote.Types.NoteSortOrder.UPDATED
    });

    const spec = new Evernote.NoteStore.NotesMetadataResultSpec({
      includeTitle: true,
      includeUpdated: true,
      includeContentLength: true
    });

    const result = await this.noteStore.findNotesMetadata(filter, 0, 100, spec);

    return result.notes.filter(note => note.updated < cutoff);
  }

  /**
   * Calculate storage by notebook
   */
  async getStorageByNotebook() {
    const notebooks = await this.noteStore.listNotebooks();
    const storage = [];

    for (const notebook of notebooks) {
      const filter = new Evernote.NoteStore.NoteFilter({
        notebookGuid: notebook.guid
      });

      const spec = new Evernote.NoteStore.NotesMetadataResultSpec({
        includeContentLength: true
      });

      const result = await this.noteStore.findNotesMetadata(filter, 0, 1, spec);

      // Estimate total size (would need to paginate for accuracy)
      const avgSize = result.notes[0]?.contentLength || 0;
      const estimatedTotal = avgSize * result.totalNotes;

      storage.push({
        name: notebook.name,
        guid: notebook.guid,
        noteCount: result.totalNotes,
        estimatedSize: this.formatBytes(estimatedTotal)
      });
    }

    return storage.sort((a, b) => b.noteCount - a.noteCount);
  }

  formatBytes(bytes) {
    const units = ['B', 'KB', 'MB', 'GB'];
    let i = 0;
    while (bytes >= 1024 && i < units.length - 1) {
      bytes /= 1024;
      i++;
    }
    return `${bytes.toFixed(2)} ${units[i]}`;
  }
}

module.exports = StorageCleanup;
```

### Step 5: Quota Alerts

```javascript
// services/quota-alerts.js

class QuotaAlertService {
  constructor(quotaService, options = {}) {
    this.quota = quotaService;
    this.thresholds = {
      warning: options.warningPercent || 70,
      critical: options.criticalPercent || 90
    };
    this.alertHandlers = [];
  }

  /**
   * Register alert handler
   */
  onAlert(handler) {
    this.alertHandlers.push(handler);
  }

  /**
   * Check and alert
   */
  async checkAndAlert() {
    const status = await this.quota.getQuotaStatus();
    const usagePercent = parseFloat(status.usagePercent);

    if (usagePercent >= this.thresholds.critical) {
      await this.sendAlert('critical', status);
    } else if (usagePercent >= this.thresholds.warning) {
      await this.sendAlert('warning', status);
    }

    return status;
  }

  /**
   * Send alert to handlers
   */
  async sendAlert(level, status) {
    const alert = {
      level,
      message: this.formatAlertMessage(level, status),
      status,
      timestamp: new Date()
    };

    for (const handler of this.alertHandlers) {
      try {
        await handler(alert);
      } catch (error) {
        console.error('Alert handler error:', error);
      }
    }
  }

  formatAlertMessage(level, status) {
    const emoji = level === 'critical' ? '' : '';
    return `${emoji} Evernote quota ${level.toUpperCase()}: ` +
           `${status.usagePercent} used (${status.uploaded} / ${status.uploadLimit}). ` +
           `Resets in ${status.daysUntilReset} days.`;
  }
}

// Usage example
const alertService = new QuotaAlertService(quotaService);

// Email alert
alertService.onAlert(async (alert) => {
  await sendEmail({
    to: 'admin@example.com',
    subject: `Evernote Quota ${alert.level}`,
    body: alert.message
  });
});

// Slack alert
alertService.onAlert(async (alert) => {
  await slack.send({
    channel: '#alerts',
    text: alert.message
  });
});

module.exports = QuotaAlertService;
```

### Step 6: Usage Report

```javascript
// scripts/quota-report.js

async function generateQuotaReport(quotaService, cleanupService) {
  console.log('=== Evernote Quota Report ===\n');

  // Current status
  const status = await quotaService.getQuotaStatus();
  console.log('Account Tier:', status.tier);
  console.log('Upload Quota:', `${status.uploaded} / ${status.uploadLimit} (${status.usagePercent})`);
  console.log('Remaining:', status.remaining);
  console.log('Resets:', status.resetsAt.toLocaleDateString(), `(${status.daysUntilReset} days)`);

  // Large notes
  console.log('\n--- Large Notes (>5MB) ---');
  const largeNotes = await cleanupService.findLargeNotes(5);
  if (largeNotes.length > 0) {
    largeNotes.forEach(note => {
      console.log(`- ${note.title}: ${cleanupService.formatBytes(note.contentLength)}`);
    });
    console.log(`Total: ${largeNotes.length} notes`);
  } else {
    console.log('No large notes found');
  }

  // Storage by notebook
  console.log('\n--- Storage by Notebook ---');
  const storage = await cleanupService.getStorageByNotebook();
  storage.slice(0, 10).forEach(nb => {
    console.log(`- ${nb.name}: ${nb.noteCount} notes (~${nb.estimatedSize})`);
  });

  // Recommendations
  console.log('\n--- Recommendations ---');
  const usagePercent = parseFloat(status.usagePercent);

  if (usagePercent > 80) {
    console.log('- Consider upgrading account tier');
    console.log('- Optimize images before upload');
    console.log('- Archive old notes to external storage');
  }

  if (largeNotes.length > 10) {
    console.log('- Review and compress large notes');
    console.log('- Consider moving attachments to cloud storage');
  }

  console.log('\n=== End Report ===');
}
```


## Account Limits by Tier

| Feature | Basic | Personal | Professional |
|---------|-------|----------|--------------|
| Monthly upload | 60 MB | 10 GB | 20 GB |
| Max note size | 25 MB | 200 MB | 200 MB |
| Notebooks | 250 | 1,000 | 1,000 |
| Tags | 100,000 | 100,000 | 100,000 |
| Saved searches | 100 | 100 | 100 |


## Cost Optimization Checklist

```markdown


## Monthly Checklist

- [ ] Check quota usage status
- [ ] Review large notes (>5MB)
- [ ] Find and merge duplicates
- [ ] Archive stale notes
- [ ] Optimize images in queue
- [ ] Set up quota alerts
```
