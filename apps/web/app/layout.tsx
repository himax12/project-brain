import "./globals.css";
import type { ReactNode } from "react";
import Link from "next/link";

export const metadata = {
  title: "Project Brain",
  description: "HITL inbox for governed project memory",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header>
          <strong>Project Brain</strong>
          <nav>
            <Link href="/pending">Pending</Link>
            <Link href="/context">Active</Link>
            <Link href="/recall">Recall</Link>
            <Link href="/ingest">Ingest</Link>
          </nav>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
