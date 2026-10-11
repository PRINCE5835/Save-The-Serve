import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { AppProvider } from "@/context/AppContext";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Save The Serve (S.T.S) - Food & Relief Surplus Logistics",
  description:
    "Next-generation surplus food rescue and essential goods distribution platform connecting Donors, NGOs, and Volunteers with real-time geospatial dispatch.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900 font-sans dark:bg-slate-950 dark:text-slate-50 selection:bg-emerald-500 selection:text-white">
        <AuthProvider>
          <AppProvider>
            <Navbar />
            <main className="flex-1 flex flex-col">{children}</main>
            <Footer />
          </AppProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
