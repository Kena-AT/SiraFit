import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Class joiner with Tailwind conflict resolution â€” same util as SiraFit-docs. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

