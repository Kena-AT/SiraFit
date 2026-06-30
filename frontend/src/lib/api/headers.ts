export function getAIHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  
  if (typeof localStorage !== 'undefined') {
    const key = localStorage.getItem("ai_api_key");
    const provider = localStorage.getItem("ai_provider");
    const model = localStorage.getItem("ai_model");
    
    if (key) headers["X-AI-API-Key"] = key;
    if (provider) headers["X-AI-Provider"] = provider;
    if (model) headers["X-AI-Model"] = model;
  }
  
  return headers;
}
