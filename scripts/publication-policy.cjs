'use strict';

/**
 * Canonical catalog publication policy.
 *
 * marketplace.extended.json retains quarantined records for attribution and
 * provenance. Every installable/public projection must call this helper and
 * omit them. Unknown states fail closed.
 */
function isPublishedPlugin(plugin, label = 'catalog plugin') {
  if (!plugin || typeof plugin !== 'object' || Array.isArray(plugin)) {
    throw new Error(`${label} must be an object`);
  }
  if (plugin.publication === undefined) return true;
  if (plugin.publication === 'quarantined') return false;
  throw new Error(`${label} has unknown publication state: ${String(plugin.publication)}`);
}

function publishedPlugins(plugins, label = 'catalog') {
  if (!Array.isArray(plugins)) throw new Error(`${label} plugins must be an array`);
  return plugins.filter((plugin, index) => isPublishedPlugin(plugin, `${label} plugin ${index}`));
}

module.exports = { isPublishedPlugin, publishedPlugins };
