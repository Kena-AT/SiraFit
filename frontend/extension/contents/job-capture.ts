import type { PlasmoCSConfig } from "plasmo";
import { extractJobFromPage } from "../lib/extractors";

export const config: PlasmoCSConfig = {
  matches: ["<all_urls>"]
};

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "CAPTURE_ACTIVE_TAB") {
    const result = extractJobFromPage(window.location.href, document);
    if (result) {
      sendResponse({ data: result });
    } else {
      sendResponse({ error: "Could not extract job from this page" });
    }
  }
  return true; // Keep channel open for async response
});
