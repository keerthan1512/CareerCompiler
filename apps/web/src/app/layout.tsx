import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CareerCompiler — AI Resume Engineering Platform",
  description:
    "Maintain one authoritative LaTeX resume and generate factually grounded, job-specific variants with AI assistance.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
