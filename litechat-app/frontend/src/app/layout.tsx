import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LiteChat - 月500円のAIチャット",
  description: "月500円でAI使い放題。ChatGPTの1/6の価格で、利用制限なし。",
  metadataBase: new URL("https://pik-tal.com"),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
