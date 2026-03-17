import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SEAS — Student Engagement Analysis",
  description: "Real-time facial emotion recognition for student engagement monitoring",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-gray-100 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
