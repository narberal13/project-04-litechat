import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "きくよ - あなたの話を聴くAI",
  description: "月500円で、あなたの話をただ聴いてくれるAI。愚痴も、悩みも、何でも。全力で肯定します。",
  metadataBase: new URL("https://pik-tal.com"),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
