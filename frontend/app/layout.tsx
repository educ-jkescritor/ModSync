import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ModSync",
  description: "Faculty-assistive curriculum review recommendations for technical modules."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

