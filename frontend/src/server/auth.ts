// Server-side auth helper for TanStack Start
// Used in beforeLoad to check auth with cookies during SSR

import { defineHandler } from "@tanstack/react-start-server";
import { getCookie } from "@tanstack/start-server-core";

export const getSSRUser = defineHandler(async () => {
  const token = getCookie("access_token");
  if (!token) return null;

  try {
    const res = await fetch("http://localhost:8000/api/v1/users/me", {
      method: "GET",
      headers: {
        Cookie: `access_token=${token}`,
      },
    });

    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
});