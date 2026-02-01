/**
 * Generates a random ID of a specified length using a url-friendly alphabet
 * Can be run without node:crypto
 * @param length - The length of the ID to generate (default: 9)
 * @returns A random string ID
 */
export declare function generateId(length?: number): string;
/**
 * Parse a time expression into seconds
 * @param timeExpression Time expression (number or string like "5m", "30s", "1h")
 * @returns Number of seconds
 */
export declare function parseTimeExpression(timeExpression: string | number): number;
