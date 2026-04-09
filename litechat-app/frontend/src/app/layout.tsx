import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LiteChat - 月300円からのAIチャット",
  description: "月300円からAI使い放題。ChatGPT Plusの1/10の価格。プライバシー重視、データ外部送信なし。",
  metadataBase: new URL("https://pik-tal.com"),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
