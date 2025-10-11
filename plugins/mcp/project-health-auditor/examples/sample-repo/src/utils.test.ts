import { describe, it, expect } from 'vitest';
import { formatDate, isValidEmail, generateId } from './utils';

describe('utils', () => {
  describe('formatDate', () => {
    it('should format date to ISO string', () => {
      const date = new Date('2025-10-10T12:00:00Z');
      expect(formatDate(date)).toBe('2025-10-10T12:00:00.000Z');
    });
  });

  describe('isValidEmail', () => {
    it('should validate correct email', () => {
      expect(isValidEmail('[email protected]')).toBe(true);
    });

    it('should reject invalid email', () => {
      expect(isValidEmail('notanemail')).toBe(false);
    });
  });

  describe('generateId', () => {
    it('should generate random ID', () => {
      const id = generateId();
      expect(id).toBeTruthy();
      expect(id.length).toBeGreaterThan(5);
    });
  });
});
