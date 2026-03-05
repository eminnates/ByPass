import type { Metadata, Viewport } from "next";
import { Space_Grotesk } from "next/font/google";
import Script from "next/script";
import "./globals.css";

const space = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const viewport: Viewport = {
  themeColor: "#a855f7",
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  title: {
    default: "ReklamAtla — Link Bypass",
    template: "%s | ReklamAtla",
  },
  description: "Kısaltılmış linkleri anında bypass et. Reklamsız, hızlı, güvenli.",
  keywords: ["linkvertise bypass", "link bypass", "url bypass", "ouo bypass", "aylink bypass", "reklam atla"],
  metadataBase: new URL("https://reklamatla.com"),
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "ReklamAtla",
  },
  openGraph: {
    title: "ReklamAtla — Link Bypass",
    description: "Kısaltılmış linkleri anında bypass et. Reklamsız, hızlı, güvenli.",
    url: "https://reklamatla.com",
    siteName: "ReklamAtla",
    locale: "tr_TR",
    type: "website",
  },
  icons: {
    icon: "/icon-192.png",
    apple: "/icon-512.png",
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

        {/* Service Worker Registration */}
        <Script id="sw-register" strategy="afterInteractive">
          {`
            if ('serviceWorker' in navigator) {
              window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                  .then(reg => console.log('SW registered:', reg.scope))
                  .catch(err => console.log('SW registration failed:', err));
              });
            }
          `}
        </Script>
      </head>
      <body
        className={`${space.className} bg-black text-white antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
