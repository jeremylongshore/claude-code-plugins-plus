// acme-widgets CLI — golden-fixture implementation (illustrative, not shipped).
'use strict';

const registry = new Map();

function registerCommand(name, handler) {
  registry.set(name, handler);
}

registerCommand('create', () => 'created');
registerCommand('list', () => [...registry.keys()]);

module.exports = { registerCommand, registry };
