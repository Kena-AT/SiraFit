import { ExtensionMessage } from "../lib/messages";

chrome.runtime.onMessage.addListener((message: ExtensionMessage, sender, sendResponse) => {
  // Handle background specific messages if needed
  return true;
});
