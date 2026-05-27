import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VerifyHire — AI Video Resume Platform",
  description: "AI-powered job matching for blue-collar workers",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}