/**
 * AI Experiment Logger - Frontend Application
 */

let currentView = 'dashboard';
let currentRating = 0;
let experiments = [];
let sortField = 'date';
let sortDirection = 'desc';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
  loadExperiments();
  setupEventListeners();
});

function setupEventListeners() {
  // Form submission
  document.getElementById('experimentForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    await saveExperiment();
  });

  // Real-time search
  document.getElementById('searchQuery').addEventListener('input', debounce(applyFilters, 300));
}

// View management
function showView(view) {
  currentView = view;

  // Hide all views
  document.getElementById('viewLog').classList.add('hidden');
  document.getElementById('viewDashboard').classList.add('hidden');
  document.getElementById('viewStatistics').classList.add('hidden');

  // Update navigation
  document.getElementById('navDashboard').className = 'py-4 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 font-medium';
  document.getElementById('navStatistics').className = 'py-4 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 font-medium';

  // Show selected view
  if (view === 'log') {
    document.getElementById('viewLog').classList.remove('hidden');
    resetForm();
  } else if (view === 'dashboard') {
    document.getElementById('viewDashboard').classList.remove('hidden');
    document.getElementById('navDashboard').className = 'py-4 px-1 border-b-2 border-indigo-600 text-indigo-600 font-medium';
    loadExperiments();
  } else if (view === 'statistics') {
    document.getElementById('viewStatistics').classList.remove('hidden');
    document.getElementById('navStatistics').className = 'py-4 px-1 border-b-2 border-indigo-600 text-indigo-600 font-medium';
    loadStatistics();
  }
}

// Rating stars
function setRating(rating) {
  currentRating = rating;
  document.getElementById('rating').value = rating;

  // Update star display
  for (let i = 1; i <= 5; i++) {
    const star = document.getElementById(`star${i}`);
    if (i <= rating) {
      star.className = 'text-3xl text-yellow-400';
    } else {
      star.className = 'text-3xl text-gray-300 hover:text-yellow-400';
    }
  }
}

// Save experiment
async function saveExperiment() {
  const data = {
    aiTool: document.getElementById('aiTool').value,
    prompt: document.getElementById('prompt').value,
    result: document.getElementById('result').value,
    rating: parseInt(document.getElementById('rating').value),
    tags: document.getElementById('tags').value
      ? document.getElementById('tags').value.split(',').map(t => t.trim()).filter(t => t)
      : []
  };

  const dateInput = document.getElementById('date').value;
  if (dateInput) {
    data.date = new Date(dateInput).toISOString();
  }

  try {
    const response = await fetch('/api/experiments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    if (result.success) {
      showNotification('Experiment saved successfully!', 'success');
      resetForm();
      showView('dashboard');
    } else {
      showNotification(result.error || 'Failed to save experiment', 'error');
    }
  } catch (error) {
    showNotification('Network error. Please try again.', 'error');
  }
}

// Load experiments
async function loadExperiments() {
  try {
    const response = await fetch('/api/experiments');
    const result = await response.json();

    if (result.success) {
      experiments = result.experiments;
      renderExperiments(experiments);
    }
  } catch (error) {
    showNotification('Failed to load experiments', 'error');
  }
}

// Render experiments table
function renderExperiments(data) {
  const tbody = document.getElementById('experimentsTable');
  const emptyState = document.getElementById('emptyState');

  if (data.length === 0) {
    tbody.innerHTML = '';
    emptyState.classList.remove('hidden');
    return;
  }

  emptyState.classList.add('hidden');

  tbody.innerHTML = data.map(exp => `
    <tr class="hover:bg-gray-50">
      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        ${formatDate(exp.date)}
      </td>
      <td class="px-6 py-4 whitespace-nowrap">
        <span class="px-2 py-1 text-sm font-medium text-indigo-600 bg-indigo-50 rounded">
          ${escapeHtml(exp.aiTool)}
        </span>
      </td>
      <td class="px-6 py-4 text-sm text-gray-900 max-w-xs truncate" title="${escapeHtml(exp.prompt)}">
        ${escapeHtml(exp.prompt)}
      </td>
      <td class="px-6 py-4 text-sm text-gray-900 max-w-xs truncate" title="${escapeHtml(exp.result)}">
        ${escapeHtml(exp.result)}
      </td>
      <td class="px-6 py-4 whitespace-nowrap text-sm">
        ${renderStars(exp.rating)}
      </td>
      <td class="px-6 py-4 whitespace-nowrap">
        <div class="flex flex-wrap gap-1">
          ${exp.tags.map(tag => `<span class="px-2 py-0.5 text-xs font-medium text-gray-600 bg-gray-100 rounded">${escapeHtml(tag)}</span>`).join('')}
        </div>
      </td>
      <td class="px-6 py-4 whitespace-nowrap text-sm">
        <button onclick="deleteExperiment('${exp.id}')" class="text-red-600 hover:text-red-800">
          Delete
        </button>
      </td>
    </tr>
  `).join('');
}

// Apply filters
async function applyFilters() {
  const params = new URLSearchParams();

  const searchQuery = document.getElementById('searchQuery').value;
  if (searchQuery) params.append('searchQuery', searchQuery);

  const aiTool = document.getElementById('filterAiTool').value;
  if (aiTool) params.append('aiTool', aiTool);

  const rating = document.getElementById('filterRating').value;
  if (rating) params.append('rating', rating);

  try {
    const response = await fetch(`/api/experiments?${params}`);
    const result = await response.json();

    if (result.success) {
      renderExperiments(result.experiments);
    }
  } catch (error) {
    showNotification('Failed to filter experiments', 'error');
  }
}

// Sort table
function sortTable(field) {
  if (sortField === field) {
    sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
  } else {
    sortField = field;
    sortDirection = 'asc';
  }

  const sorted = [...experiments].sort((a, b) => {
    let aVal = a[field];
    let bVal = b[field];

    if (field === 'date') {
      aVal = new Date(aVal).getTime();
      bVal = new Date(bVal).getTime();
    }

    if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  renderExperiments(sorted);
}

// Delete experiment
async function deleteExperiment(id) {
  if (!confirm('Are you sure you want to delete this experiment?')) return;

  try {
    const response = await fetch(`/api/experiments/${id}`, {
      method: 'DELETE'
    });

    const result = await response.json();

    if (result.success) {
      showNotification('Experiment deleted', 'success');
      loadExperiments();
    } else {
      showNotification(result.error || 'Failed to delete experiment', 'error');
    }
  } catch (error) {
    showNotification('Network error. Please try again.', 'error');
  }
}

// Load and render statistics
async function loadStatistics() {
  try {
    const response = await fetch('/api/statistics');
    const result = await response.json();

    if (result.success) {
      renderStatistics(result.statistics);
    }
  } catch (error) {
    showNotification('Failed to load statistics', 'error');
  }
}

function renderStatistics(stats) {
  // Summary cards
  document.getElementById('statTotal').textContent = stats.totalExperiments;
  document.getElementById('statAvgRating').textContent = stats.averageRating.toFixed(2);
  document.getElementById('statTopTool').textContent = stats.toolStats[0]?.tool || '-';
  document.getElementById('statUniqueTags').textContent = stats.topTags.length;

  // Tool statistics
  const toolStatsHtml = stats.toolStats.map(tool => `
    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div>
        <div class="font-medium text-gray-900">${escapeHtml(tool.tool)}</div>
        <div class="text-sm text-gray-500">${tool.count} experiments</div>
      </div>
      <div class="text-right">
        <div class="text-lg font-bold text-indigo-600">${tool.averageRating.toFixed(2)}</div>
        <div class="text-xs text-gray-500">avg rating</div>
      </div>
    </div>
  `).join('');
  document.getElementById('toolStats').innerHTML = toolStatsHtml || '<p class="text-gray-500">No data yet</p>';

  // Rating distribution
  const maxCount = Math.max(...stats.ratingDistribution.map(r => r.count), 1);
  const ratingDistHtml = stats.ratingDistribution.map(rating => {
    const percentage = (rating.count / maxCount) * 100;
    return `
      <div class="flex items-center space-x-3">
        <div class="w-20 text-sm font-medium text-gray-700">${rating.rating} star${rating.rating !== 1 ? 's' : ''}</div>
        <div class="flex-1 bg-gray-200 rounded-full h-6 overflow-hidden">
          <div class="bg-yellow-400 h-full flex items-center justify-end px-2" style="width: ${percentage}%">
            <span class="text-xs font-medium text-gray-900">${rating.count}</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
  document.getElementById('ratingDistribution').innerHTML = ratingDistHtml || '<p class="text-gray-500">No data yet</p>';

  // Top tags
  const topTagsHtml = stats.topTags.map(tag => `
    <span class="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium">
      ${escapeHtml(tag.tag)} (${tag.count})
    </span>
  `).join('');
  document.getElementById('topTags').innerHTML = topTagsHtml || '<p class="text-gray-500">No tags yet</p>';

  // Recent activity
  const activityHtml = stats.recentActivity.map(day => `
    <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
      <span class="text-sm text-gray-700">${formatDate(day.date)}</span>
      <span class="text-sm font-medium text-indigo-600">${day.count} experiments</span>
    </div>
  `).join('');
  document.getElementById('recentActivity').innerHTML = activityHtml || '<p class="text-gray-500">No recent activity</p>';
}

// Export to CSV
async function exportCSV() {
  try {
    const response = await fetch('/api/export');
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai-experiments-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    showNotification('CSV exported successfully!', 'success');
  } catch (error) {
    showNotification('Failed to export CSV', 'error');
  }
}

// Utility functions
function resetForm() {
  document.getElementById('experimentForm').reset();
  currentRating = 0;
  for (let i = 1; i <= 5; i++) {
    document.getElementById(`star${i}`).className = 'text-3xl text-gray-300 hover:text-yellow-400';
  }
  // Set current date/time
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  document.getElementById('date').value = now.toISOString().slice(0, 16);
}

function renderStars(rating) {
  return '★'.repeat(rating) + '☆'.repeat(5 - rating);
}

function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

function showNotification(message, type) {
  const notification = document.createElement('div');
  notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white ${
    type === 'success' ? 'bg-green-500' : 'bg-red-500'
  } animate-fade-in z-50`;
  notification.textContent = message;
  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.opacity = '0';
    notification.style.transition = 'opacity 0.3s';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}
