import { Storage } from "@plasmohq/storage";

const storage = new Storage();
const TOKEN_KEY = "sirafit_ext_token";

export async function getExtensionToken(): Promise<string | null> {
  return await storage.get(TOKEN_KEY);
}

export async function setExtensionToken(token: string): Promise<void> {
  await storage.set(TOKEN_KEY, token);
}

export async function clearExtensionToken(): Promise<void> {
  await storage.remove(TOKEN_KEY);
}
