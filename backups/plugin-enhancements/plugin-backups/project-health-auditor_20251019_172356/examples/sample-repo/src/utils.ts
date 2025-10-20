// Example: Low complexity, well-maintained
/**
 * Formats a date string to ISO format
 */
export function formatDate(date: Date): string {
  return date.toISOString();
}

/**
 * Validates an email address
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Generates a random ID
 */
export function generateId(): string {
  return Math.random().toString(36).substring(2, 15);
}
