import { AgentApiClient, DEFAULT_API_BASE } from "../shared/api";
import { ExtractedJob } from "../shared/types";

// In WebExtension context, chrome or browser global is available
declare const chrome: any;

async function getStorageData(keys: string[]): Promise<Record<string, any>> {
  return new Promise((resolve) => {
    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.get(keys, (res: any) => resolve(res || {}));
    } else {
      resolve({});
    }
  });
}

async function setStorageData(items: Record<string, any>): Promise<void> {
  return new Promise((resolve) => {
    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.set(items, () => resolve());
    } else {
      resolve();
    }
  });
}

async function getApiClient(): Promise<{ client: AgentApiClient; token: string }> {
  const data = await getStorageData(["sirafit_token", "sirafit_api_base"]);
  const token = data.sirafit_token || "";
  const apiBase = data.sirafit_api_base || DEFAULT_API_BASE;
  return {
    client: new AgentApiClient(apiBase),
    token,
  };
}

if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
  chrome.runtime.onMessage.addListener(
    (request: any, sender: any, sendResponse: (response?: any) => void) => {
      const handleAsync = async () => {
        try {
          if (request.type === "GET_STATE") {
            const { client, token } = await getApiClient();
            if (!token) {
              return { connected: false, token: "", apiBase: DEFAULT_API_BASE };
            }
            try {
              const status = await client.getStatus(token);
              return {
                connected: status.connected,
                user: {
                  id: status.user_id,
                  email: status.user_email,
                  name: status.user_name,
                },
                token,
                apiBase: client["apiBase"] || DEFAULT_API_BASE,
              };
            } catch (err: any) {
              return { connected: false, token, error: err.message };
            }
          }

          if (request.type === "SAVE_TOKEN") {
            const rawToken = request.token;
            const apiBase = request.apiBase || DEFAULT_API_BASE;
            const client = new AgentApiClient(apiBase);
            const status = await client.getStatus(rawToken);

            await setStorageData({
              sirafit_token: rawToken,
              sirafit_api_base: apiBase,
            });

            return {
              success: true,
              user: {
                id: status.user_id,
                email: status.user_email,
                name: status.user_name,
              },
            };
          }

          if (request.type === "LOGOUT") {
            const { client, token } = await getApiClient();
            if (token) {
              try {
                await client.logout(token);
              } catch (_) {}
            }
            await setStorageData({ sirafit_token: "" });
            return { success: true };
          }

          if (request.type === "GET_PROFILE") {
            const { client, token } = await getApiClient();
            if (!token) throw new Error("Not authenticated with SiraFit");
            const profile = await client.getProfile(token);
            return { success: true, profile };
          }

          if (request.type === "SUBMIT_CAPTURE") {
            const { client, token } = await getApiClient();
            if (!token) throw new Error("Not authenticated with SiraFit");
            const payload: ExtractedJob = request.payload;
            const result = await client.importJob(token, payload);
            return { success: true, result };
          }

          return { error: "Unknown message type" };
        } catch (err: any) {
          return { error: err.message || "An error occurred" };
        }
      };

      handleAsync().then(sendResponse);
      return true; // Keep message channel open for async response
    }
  );
}
