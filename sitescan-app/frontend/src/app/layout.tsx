import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SiteScan - AIによるWebサイト自動診断",
  description:
    "URLを入力するだけ。AIがあなたのWebサイトをSEO・パフォーマンス・アクセシビリティの観点から診断し、具体的な改善策をレポートします。",
  metadataBase: new URL("https://pik-tal.com"),
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body>
        {children}
        <footer className="footer">
          <div className="container">
            <a href="/toswatch/">ToSWatch</a>
            <a href="/legal/">特定商取引法に基づく表記</a>
            <a href="/privacy/">プライバシーポリシー</a>
            <p style={{ marginTop: 12 }}>
              &copy; 2026 SiteScan by pik-tal.com
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
