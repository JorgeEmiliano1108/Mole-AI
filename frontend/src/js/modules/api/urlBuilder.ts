/**
 * URL builder utility – joins API base URL with a path safely.
 * Prevents duplicate slashes that cause 400 Bad Request errors.
 */
import { API_BASE_URL } from './config';

export function apiUrl(path: string): string {
  // Remove trailing slashes from base and leading slashes from path, then join with a single slash.
  const base = API_BASE_URL.replace(/\/+$/g, '');
  const cleanPath = path.replace(/^\/+/, '');
  return `${base}/${cleanPath}`;
}
