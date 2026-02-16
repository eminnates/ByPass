import type { Metadata } from "next";
import { Space_Grotesk } from "next/font/google";
import Script from "next/script";
import "./globals.css";

const space = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Linkvertise Bypass",
    template: "%s | Linkvertise Bypass",
  },
  description: "Hızlı, güvenli ve modern link geçme servisi.",
  keywords: ["linkvertise bypass", "link bypass", "url bypass"],
  metadataBase: new URL("https://yourdomain.com"), // domainini buraya yaz
  openGraph: {
    title: "Linkvertise Bypass",
    description: "Hızlı ve güvenli link geçme servisi.",
    url: "https://yourdomain.com",
    siteName: "Linkvertise Bypass",
    locale: "tr_TR",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <head>
        {/* Google AdSense */}
        <Script
          async
          src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX"
          crossOrigin="anonymous"
          strategy="afterInteractive"
        />
      </head>
      <body
        className={`${space.className} bg-black text-white antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
