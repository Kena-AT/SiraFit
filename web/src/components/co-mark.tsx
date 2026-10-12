import { instrumentSerif } from "@/lib/fonts";

// Brand mark â€” lowercase "co" on brand orange in Instrument Serif. Matches the
// favicon (src/app/icon.tsx) and the SiraFit-docs home one-for-one so the
// app reads as a sibling. Dual meaning: "co" of SiraFit AND "co" of
// companies â€” the word the manifesto inverts ("â€¦AI to choose companies").
export function CoMark({ size = 28 }: { size?: number }) {
  return (
    <span
      aria-hidden="true"
      className={`${instrumentSerif.className} inline-flex shrink-0 items-center justify-center rounded-md bg-brand text-white`}
      style={{
        width: size,
        height: size,
        fontSize: Math.round(size * 0.78),
        letterSpacing: "0.01em",
        lineHeight: 1,
        paddingBottom: Math.round(size * 0.08),
      }}
    >
      co
    </span>
  );
}

