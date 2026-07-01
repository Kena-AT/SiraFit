/**
 * AI configuration is now stored server-side (encrypted) and never exposed to the client.
 * These headers are no longer needed; API keys are resolved by the backend from:
 *   1. User-stored encrypted key (via UserPreference table)
 *   2. Server environment variables (GEMINI_API_KEY / OPENROUTER_API_KEY)
 *
 * This file is kept for backward compatibility but returns no sensitive data.
 */
export function getAIHeaders(): Record<string, string> {
  return {};
}
