import "./lib/error-capture";

import { consumeLastCapturedError } from "./lib/error-capture";
import { renderErrorPage } from "./lib/error-page";

type ServerEntry = {
  fetch: (request: Request, env: unknown, ctx: unknown) => Promise<Response> | Response;
};

let serverEntryPromise: Promise<ServerEntry> | undefined;

async function getServerEntry(): Promise<ServerEntry> {
  if (!serverEntryPromise) {
    serverEntryPromise = import("@tanstack/react-start/server-entry").then(
      (m) => (m.default ?? m) as ServerEntry,
    );
  }
  return serverEntryPromise;
}

// h3 swallows in-handler throws into a normal 500 Response with body
// {"unhandled":true,"message":"HTTPError"} — try/catch alone never fires for those.
async function normalizeCatastrophicSsrResponse(response: Response): Promise<Response> {
  if (response.status < 500) return response;
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) return response;

  const body = await response.clone().text();
  if (!body.includes('"unhandled":true') || !body.includes('"message":"HTTPError"')) {
    return response;
  }

  console.error(consumeLastCapturedError() ?? new Error(`h3 swallowed SSR error: ${body}`));
  return new Response(renderErrorPage(), {
    status: 500,
    headers: { "content-type": "text/html; charset=utf-8" },
  });
}

/**
 * In development the TanStack Start / h3 server handles ALL incoming requests
 * before Vite's proxy gets a chance. This means /api/* requests from the
 * browser hit this server first and never reach the Vite proxy config.
 *
 * To keep the browser on the same origin (avoiding CORS entirely), we proxy
 * /api/* straight to the FastAPI backend from inside the h3 server.
 */
const BACKEND_ORIGIN =
  process.env.VITE_API_URL ?? process.env.BACKEND_URL ?? "http://localhost:8000";
const IS_DEV = process.env.NODE_ENV !== "production";

async function proxyToBackend(request: Request): Promise<Response> {
  const url = new URL(request.url);
  const targetUrl = `${BACKEND_ORIGIN}${url.pathname}${url.search}`;

  // Forward all headers except Host (the backend sets its own)
  const forwardHeaders = new Headers(request.headers);
  forwardHeaders.delete("host");

  const proxyRequest = new Request(targetUrl, {
    method: request.method,
    headers: forwardHeaders,
    body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
    // @ts-ignore — duplex required for streaming bodies in Node 18+
    duplex: "half",
  });

  try {
    return await fetch(proxyRequest);
  } catch (e) {
    console.error(`[proxy] Failed to reach backend at ${targetUrl}:`, e);
    return new Response(
      JSON.stringify({ detail: "Backend unavailable" }),
      { status: 502, headers: { "content-type": "application/json" } },
    );
  }
}

export default {
  async fetch(request: Request, env: unknown, ctx: unknown) {
    const url = new URL(request.url);

    // In development, proxy /api/* directly to FastAPI so requests stay
    // same-origin from the browser's perspective — no CORS needed.
    if (IS_DEV && url.pathname.startsWith("/api/")) {
      return proxyToBackend(request);
    }

    try {
      const handler = await getServerEntry();
      const response = await handler.fetch(request, env, ctx);
      return await normalizeCatastrophicSsrResponse(response);
    } catch (error) {
      console.error(error);
      return new Response(renderErrorPage(), {
        status: 500,
        headers: { "content-type": "text/html; charset=utf-8" },
      });
    }
  },
};
