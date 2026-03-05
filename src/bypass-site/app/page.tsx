"use client";

// --- API BASE URL ---
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://10.13.163.46';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import AdUnit from '@/components/AdUnit';
import {
  Clipboard, ArrowRight, Zap, CheckCircle, Shield, Smartphone,
  Moon, Sun, Coffee, ChevronDown, ChevronUp,
  CheckCircle as CheckIcon, Globe, Loader2, Users, Activity,
  Send, ExternalLink, Copy, ArrowDown
} from 'lucide-react';

// ═══════════════════════════════════════════════════════
// TERCÜME VERİTABANI
// ═══════════════════════════════════════════════════════
const translations: any = {
  tr: {
    nav: { home: "Ana Sayfa", coffee: "Kahve Ismarla" },
    hero: {
      title: "Reklamları Atla,",
      titleHighlight: "Hemen Ulaş",
      subtitle: "Kısaltılmış linklerin arkasındaki gerçek URL'yi saniyeler içinde ortaya çıkar. Güvenli, hızlı ve tamamen ücretsiz.",
      placeholder: "Kısaltılmış linki buraya yapıştır...",
      button: "ATLA",
      processing: "Çözülüyor...",
      success: "Bypass Başarılı!",
      go: "Git",
      autoRedirect: "Otomatik Yönlendirme",
      autoRedirectWarn: "Bypass sonrası otomatik yönlendirilirsiniz",
      paste: "Yapıştır",
      invalidUrl: "Geçerli bir URL girin (https://...)",
      clear: "Temizle",
    },
    safety: {
      scanning: "Güvenlik taranıyor...",
      clean: "✓ Güvenli Link",
      malicious: "⚠️ Tehlikeli Link!",
      suspicious: "Şüpheli Link",
    },
    queue: {
      connecting: "Sunucuya bağlanılıyor...",
      resolving: "Link çözülüyor, lütfen bekleyin...",
      processing: "Linkiniz şu an işleniyor...",
      inQueue: "Kuyrukta",
      position: "sırada",
      timeout: "İşlem zaman aşımına uğradı. Lütfen tekrar deneyin.",
      connectionLost: "Bağlantı koptu.",
      serverDown: "Sunucuya erişilemedi. Backend çalışıyor mu?",
      unexpected: "Beklenmedik bir hata oluştu.",
      retryFailed: "Link çözülemedi. Lütfen tekrar deneyin.",
      notFound: "Bu link artık geçerli değil veya kaldırılmış (404).",
    },
    stats: { bypassed: "Bugün Çözülen", active: "Aktif Kullanıcı", live: "Canlı" },
    features: {
      security: { title: "Güvenlik Taraması", desc: "Her link VirusTotal ile otomatik taranır. Zararlı sitelere karşı korunursun." },
      speed: { title: "Anında Sonuç", desc: "Bekleme süresi ve reklam yok. Linki yapıştır, saniyeler içinde hedefe ulaş." },
      device: { title: "Her Cihazda", desc: "Telefon, tablet veya bilgisayar — her platformda sorunsuz çalışır." },
    },
    howItWorks: {
      title: "Nasıl Çalışır?",
      step1: { title: "Linki Yapıştır", desc: "Kısaltılmış linki kopyala ve yukarıdaki kutuya yapıştır." },
      step2: { title: "Bypass Et", desc: "Sistemimiz reklamları ve bekleme sürelerini otomatik atlar." },
      step3: { title: "Hedefe Ulaş", desc: "Gerçek URL'yi güvenli bir şekilde al ve doğrudan git." },
    },
    telegram: {
      title: "Telegram'dan da kullanabilirsin!",
      desc: "Linki bota gönder, bypass edilmiş halini anında al.",
      button: "Telegram Bot'u Aç",
    },
    faq: {
      title: "Sıkça Sorulan Sorular",
      q1: "Hangi servisler destekleniyor?", a1: "OUO, AyLink, Shorte.st, TR.Link, Cuty.io ve 30+ redirect kısaltıcı desteklenmektedir.",
      q2: "Tamamen ücretsiz mi?", a2: "Evet, servisimiz tamamen ücretsizdir. Hiçbir gizli ücret yoktur.",
      q3: "Güvenli mi?", a3: "Her bypass edilen link otomatik olarak VirusTotal ile taranır ve güvenlik durumu size bildirilir.",
      q4: "Hata alırsam ne yapmalıyım?", a4: "Sayfayı yenileyip tekrar deneyin. Hata devam ederse linkin geçerli olduğundan emin olun.",
      q5: "Mobilde nasıl kullanırım?", a5: "Siteyi telefonunuzdan açıp 'Ana Ekrana Ekle' yaparak uygulama gibi kullanabilir veya Telegram bot'umuzu kullanabilirsiniz.",
    },
    footer: { privacy: "Gizlilik Politikası", terms: "Kullanım Şartları", contact: "İletişim", rights: "Tüm hakları saklıdır." },
  },
  en: {
    nav: { home: "Home", coffee: "Buy Coffee" },
    hero: {
      title: "Skip the Ads,",
      titleHighlight: "Get There Instantly",
      subtitle: "Reveal the real URL behind shortened links in seconds. Safe, fast, and completely free.",
      placeholder: "Paste a shortened link here...",
      button: "BYPASS",
      processing: "Bypassing...",
      success: "Bypass Successful!",
      go: "Go",
      autoRedirect: "Auto Redirect",
      autoRedirectWarn: "You will be auto-redirected after bypass",
      paste: "Paste",
      invalidUrl: "Enter a valid URL (https://...)",
      clear: "Clear",
    },
    safety: {
      scanning: "Scanning for threats...",
      clean: "✓ Safe Link",
      malicious: "⚠️ Dangerous Link!",
      suspicious: "Suspicious Link",
    },
    queue: {
      connecting: "Connecting...", resolving: "Resolving link...", processing: "Processing...",
      inQueue: "In Queue", position: "position", timeout: "Timed out. Try again.",
      connectionLost: "Connection lost.", serverDown: "Server unreachable.", unexpected: "Unexpected error.",
      retryFailed: "Could not resolve. Try again.", notFound: "This link is no longer valid (404).",
    },
    stats: { bypassed: "Bypassed Today", active: "Active Users", live: "Live" },
    features: {
      security: { title: "Security Scan", desc: "Every link is scanned with VirusTotal. Stay protected from malicious sites." },
      speed: { title: "Instant Results", desc: "No waiting, no ads. Paste the link and reach your destination in seconds." },
      device: { title: "Any Device", desc: "Phone, tablet or computer — works seamlessly on every platform." },
    },
    howItWorks: {
      title: "How It Works",
      step1: { title: "Paste Link", desc: "Copy the shortened link and paste it in the box above." },
      step2: { title: "Bypass It", desc: "Our system automatically skips ads and wait times." },
      step3: { title: "Reach Target", desc: "Get the real URL safely and go directly." },
    },
    telegram: { title: "Also available on Telegram!", desc: "Send the link to our bot, get the bypassed result instantly.", button: "Open Telegram Bot" },
    faq: {
      title: "FAQ",
      q1: "Which services are supported?", a1: "OUO, AyLink, Shorte.st, TR.Link, Cuty.io and 30+ redirect shorteners.",
      q2: "Is it free?", a2: "Yes, completely free with no hidden charges.",
      q3: "Is it safe?", a3: "Every bypassed link is scanned with VirusTotal and safety status is reported.",
      q4: "What if I get an error?", a4: "Refresh and try again. Make sure the link is valid.",
      q5: "How to use on mobile?", a5: "Open the site on your phone or use our Telegram bot.",
    },
    footer: { privacy: "Privacy", terms: "Terms", contact: "Contact", rights: "All rights reserved." },
  },
};

const languages = [
  { code: 'tr', name: 'Türkçe', flag: '🇹🇷' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
];

// ═══════════════════════════════════════════════════════
// BILEŞENLER
// ═══════════════════════════════════════════════════════

/* --- Dil Seçici --- */
const LanguageSelector = ({ currentLang, setLang, isDarkMode }: any) => {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const close = (e: any) => { if (ref.current && !ref.current.contains(e.target)) setIsOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const sel = languages.find(l => l.code === currentLang) || languages[0];

  return (
    <div className="relative" ref={ref}>
      <button onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all border
          ${isDarkMode ? 'bg-white/5 border-white/10 text-gray-200 hover:bg-white/10' : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'}`}>
        <span className="text-lg">{sel.flag}</span>
        <span className="hidden sm:block">{sel.name}</span>
        <ChevronDown size={14} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      {isOpen && (
        <div className={`absolute top-full right-0 mt-2 w-44 rounded-xl border shadow-2xl overflow-hidden z-[70]
          ${isDarkMode ? 'bg-[#1a1a1f] border-white/10' : 'bg-white border-gray-200'}`}>
          {languages.map((lang) => (
            <button key={lang.code} onClick={() => { setLang(lang.code); setIsOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors
                ${currentLang === lang.code
                  ? (isDarkMode ? 'bg-purple-500/15 text-purple-400' : 'bg-purple-50 text-purple-600')
                  : (isDarkMode ? 'text-gray-300 hover:bg-white/5' : 'text-gray-700 hover:bg-gray-50')}`}>
              <span className="text-lg">{lang.flag}</span>
              <span className="font-medium">{lang.name}</span>
              {currentLang === lang.code && <CheckIcon size={14} className="ml-auto" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

/* --- SSS Item --- */
const FAQItem = ({ question, answer, isDarkMode }: any) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className={`border rounded-2xl overflow-hidden transition-all
      ${isDarkMode ? 'bg-white/[0.02] border-white/5 hover:border-white/10' : 'bg-white border-gray-200 shadow-sm'}`}>
      <button onClick={() => setIsOpen(!isOpen)} className="w-full px-6 py-5 flex items-center justify-between text-left">
        <span className={`font-medium ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>{question}</span>
        {isOpen ? <ChevronUp size={18} className="text-purple-400 flex-shrink-0" /> : <ChevronDown size={18} className="text-gray-500 flex-shrink-0" />}
      </button>
      <div className={`transition-all duration-300 ${isOpen ? 'max-h-[300px] opacity-100 px-6 pb-5' : 'max-h-0 opacity-0 overflow-hidden'}`}>
        <p className={`text-sm leading-relaxed ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>{answer}</p>
      </div>
    </div>
  );
};


// ═══════════════════════════════════════════════════════
// ANA SAYFA
// ═══════════════════════════════════════════════════════
export default function Home() {
  const [url, setUrl] = useState('');
  const [autoRedirect, setAutoRedirect] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [lang, setLang] = useState('tr');

  // Backend
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [resultLink, setResultLink] = useState('');
  const [error, setError] = useState('');
  const [queuePosition, setQueuePosition] = useState<number | null>(null);
  const [safetyStatus, setSafetyStatus] = useState<string | null>(null);
  const [bypassId, setBypassId] = useState<number | null>(null);
  const [stats, setStats] = useState({ links: 14205, users: 342 });
  const [copied, setCopied] = useState(false);

  const t = translations[lang] || translations['tr'];

  // İstatistik animasyonu
  useEffect(() => {
    const interval = setInterval(() => {
      setStats(prev => ({
        links: prev.links + Math.floor(Math.random() * 3) + 1,
        users: prev.users + Math.floor(Math.random() * 4) - 1,
      }));
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  // --- Yapıştır ---
  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setUrl(text);
    } catch { }
  };

  // --- Kopyala ---
  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // --- API İSTEK ---
  // URL doğrulama
  const isValidUrl = (text: string) => /^https?:\/\/.+/.test(text.trim());

  const handleBypass = async () => {
    if (!url || !isValidUrl(url)) return;
    setIsLoading(true); setError(''); setResultLink(''); setSafetyStatus(null); setBypassId(null);
    setStatusMessage(t.queue.connecting);

    try {
      const response = await fetch(`${API_BASE}/bypass`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      const data = await response.json();

      if (data.status === 'success') {
        finishProcess(data.resolved_url, data.id, data.safety_status);
      } else if (data.status === 'started' || data.status === 'pending') {
        if (data.queue_position != null) setQueuePosition(data.queue_position);
        pollStatus(data.id || data.check_id);
      } else {
        setError(t.queue.unexpected); setIsLoading(false);
      }
    } catch {
      setError(t.queue.serverDown); setIsLoading(false);
    }
  };

  // --- POLLING ---
  const pollStatus = (id: number) => {
    setStatusMessage(t.queue.resolving);
    let attempts = 0;
    const interval = setInterval(async () => {
      if (++attempts > 40) { clearInterval(interval); setError(t.queue.timeout); setIsLoading(false); setQueuePosition(null); return; }
      try {
        const res = await fetch(`${API_BASE}/status/${id}`);
        const data = await res.json();
        if (data.queue_position != null) {
          setQueuePosition(data.queue_position);
          setStatusMessage(data.queue_position === 0 ? t.queue.processing : `${t.queue.inQueue} ${data.queue_position}. ${t.queue.position}...`);
        }
        if (data.status === 'success') { clearInterval(interval); setQueuePosition(null); finishProcess(data.resolved_url, id, data.safety_status); }
        else if (data.status === 'failed' || data.status === 'error') {
          clearInterval(interval); setQueuePosition(null);
          setError(data.fail_reason === 'link_not_found' ? t.queue.notFound : data.fail_reason === 'timeout' ? t.queue.timeout : t.queue.retryFailed);
          setIsLoading(false);
        }
      } catch { clearInterval(interval); setQueuePosition(null); setError(t.queue.connectionLost); setIsLoading(false); }
    }, 3000);
  };

  // --- İŞLEM BİTİŞİ ---
  const finishProcess = (finalUrl: string, linkId?: number, initialSafety?: string) => {
    setResultLink(finalUrl); setIsLoading(false); setStatusMessage(t.hero.success); setSafetyStatus(initialSafety || null);
    if (linkId) setBypassId(linkId);
    if (initialSafety === 'scanning' && linkId) pollSafety(linkId);
    if (autoRedirect) { setStatusMessage('Yönlendiriliyor...'); setTimeout(() => { window.location.href = finalUrl; }, 1500); }
  };

  // --- GÜVENLİK POLLING ---
  const pollSafety = (linkId: number) => {
    const si = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/status/${linkId}`);
        const data = await res.json();
        if (data.safety_status && data.safety_status !== 'scanning') { setSafetyStatus(data.safety_status); clearInterval(si); }
      } catch { clearInterval(si); }
    }, 3000);
    setTimeout(() => clearInterval(si), 30000);
  };

  // Enter tuşu desteği
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading && url) handleBypass();
  };

  return (
    <main className={`min-h-screen flex flex-col relative overflow-x-hidden transition-colors duration-300
      ${isDarkMode ? 'bg-[#0a0a0f] text-white' : 'bg-[#f8f9fa] text-gray-900'}`}>

      {/* Custom scrollbar */}
      <style dangerouslySetInnerHTML={{
        __html: `
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #a855f7; border-radius: 20px; }
        * { scrollbar-width: thin; scrollbar-color: #a855f7 transparent; }
      ` }} />

      {/* ══════════ HEADER ══════════ */}
      <header className={`fixed top-0 w-full h-16 border-b z-[60] backdrop-blur-xl transition-colors
        ${isDarkMode ? 'bg-[#0a0a0f]/80 border-white/5' : 'bg-white/80 border-gray-200'}`}>
        <div className="max-w-6xl mx-auto h-full flex items-center justify-between px-4 md:px-8">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center">
              <Zap size={16} className="text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight">Reklam<span className="text-purple-500">Atla</span></span>
          </div>

          <div className="flex items-center gap-2">
            <Link href="/blog" className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all
              ${isDarkMode ? 'text-gray-400 hover:text-purple-400 hover:bg-white/5' : 'text-gray-500 hover:text-purple-600 hover:bg-purple-50'}`}>
              Blog
            </Link>
            <LanguageSelector currentLang={lang} setLang={setLang} isDarkMode={isDarkMode} />
            <button onClick={() => setIsDarkMode(!isDarkMode)} className="p-2 rounded-lg hover:bg-white/5 transition-colors">
              {isDarkMode ? <Moon size={18} className="text-yellow-300" /> : <Sun size={18} className="text-orange-500" />}
            </button>
          </div>
        </div>
      </header>

      {/* ══════════ REKLAM ALANLARI ══════════ */}
      {/* Üst banner — header'ın altında, sayfa akışında (fixed değil) */}
      <div className={`w-full h-[50px] mt-16 border-b overflow-hidden
        ${isDarkMode ? 'bg-black/90 border-white/5' : 'bg-gray-100 border-gray-300'}`}>
        <AdUnit client="ca-pub-XXXXXXXXXX" slot="XXXXXXX" format="auto" style={{ height: '50px' }} />
      </div>

      {/* Sol panel — sadece geniş ekranlarda */}
      <div className={`hidden xl:flex fixed left-0 top-[114px] bottom-0 w-[160px] border-r overflow-hidden
        ${isDarkMode ? 'bg-black/80 border-white/5' : 'bg-gray-100 border-gray-300'}`}>
        <AdUnit client="ca-pub-XXXXXXXXXX" slot="XXXXXXX" format="auto" />
      </div>

      {/* Sağ panel — sadece geniş ekranlarda */}
      <div className={`hidden xl:flex fixed right-0 top-[114px] bottom-0 w-[160px] border-l overflow-hidden
        ${isDarkMode ? 'bg-black/80 border-white/5' : 'bg-gray-100 border-gray-300'}`}>
        <AdUnit client="ca-pub-XXXXXXXXXX" slot="XXXXXXX" format="auto" />
      </div>

      {/* ══════════ HERO ══════════ */}
      <section className="relative pt-10 md:pt-16 pb-8 px-4 xl:px-[180px]">
        {/* Gradient glow */}
        {isDarkMode && (
          <>
            <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-purple-600/15 blur-[120px] rounded-full pointer-events-none" />
            <div className="absolute top-40 left-1/4 w-[200px] h-[200px] bg-blue-600/10 blur-[100px] rounded-full pointer-events-none" />
          </>
        )}

        <div className="max-w-3xl mx-auto text-center relative z-10">
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight leading-tight mb-6">
            {t.hero.title}{' '}
            <span className="bg-gradient-to-r from-purple-400 via-purple-500 to-fuchsia-500 bg-clip-text text-transparent">
              {t.hero.titleHighlight}
            </span>
          </h1>
          <p className={`text-base sm:text-lg max-w-xl mx-auto mb-10 leading-relaxed ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            {t.hero.subtitle}
          </p>

          {/* ── Input Bar ── */}
          <div className={`max-w-2xl mx-auto rounded-2xl p-1.5 transition-all
            ${isDarkMode
              ? 'bg-white/[0.04] border border-white/10 shadow-[0_0_40px_rgba(168,85,247,0.08)]'
              : 'bg-white border border-gray-200 shadow-xl'
            }`}>
            <div className="flex flex-col sm:flex-row gap-2">
              <div className={`flex-grow flex items-center rounded-xl px-4 ${isDarkMode ? 'bg-white/[0.03]' : 'bg-gray-50'}`}>
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={t.hero.placeholder}
                  disabled={isLoading}
                  className="w-full bg-transparent min-h-[56px] py-4 outline-none text-base sm:text-lg disabled:opacity-50"
                />
                <button onClick={handlePaste} disabled={isLoading}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all whitespace-nowrap
                    ${isDarkMode ? 'text-gray-400 hover:text-purple-400 hover:bg-purple-500/10' : 'text-gray-500 hover:text-purple-600 hover:bg-purple-50'}`}>
                  <Clipboard size={14} /> {t.hero.paste}
                </button>
              </div>
              <button onClick={handleBypass} disabled={isLoading || !url || !isValidUrl(url)}
                className="sm:w-48 min-h-[56px] text-white font-bold py-4 px-6 rounded-xl transition-all flex items-center justify-center gap-2 text-base
                  bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400
                  active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/20">
                {isLoading ? (
                  <><Loader2 className="animate-spin" size={20} /> {t.hero.processing}</>
                ) : (
                  <>{t.hero.button} <ArrowRight size={18} /></>
                )}
              </button>
            </div>
          </div>

          {/* URL uyarısı */}
          {url && !isValidUrl(url) && (
            <p className="text-xs text-red-400 text-center mt-2">{t.hero.invalidUrl}</p>
          )}

          {/* ── Auto redirect toggle ── */}
          <div className="flex justify-center mt-4">
            <div className="flex items-center gap-3 cursor-pointer group" onClick={() => setAutoRedirect(!autoRedirect)}>
              <div className={`w-9 h-5 rounded-full p-0.5 transition-colors ${autoRedirect ? 'bg-purple-600' : isDarkMode ? 'bg-white/10' : 'bg-gray-300'}`}>
                <div className={`w-4 h-4 bg-white rounded-full transition-transform shadow ${autoRedirect ? 'translate-x-4' : ''}`} />
              </div>
              <span className={`text-xs font-medium ${isDarkMode ? 'text-gray-500 group-hover:text-gray-300' : 'text-gray-500 group-hover:text-gray-700'}`}>
                {t.hero.autoRedirect}
              </span>
            </div>
            {autoRedirect && (
              <span className={`ml-2 text-xs italic ${isDarkMode ? 'text-yellow-400/60' : 'text-yellow-600/60'}`}>
                ⚡ {t.hero.autoRedirectWarn}
              </span>
            )}
          </div>

          {/* ── Durum / Hata / Sonuç ── */}
          <div className="max-w-2xl mx-auto mt-6 space-y-4">
            {/* Hata */}
            {error && (
              <div className={`p-4 rounded-2xl text-center font-medium text-sm animate-in fade-in flex flex-col items-center gap-3
                ${isDarkMode ? 'bg-red-500/10 border border-red-500/30 text-red-400' : 'bg-red-50 border border-red-200 text-red-600'}`}>
                <span>{error}</span>
                <button onClick={() => { setError(''); setUrl(''); }}
                  className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-colors
                    ${isDarkMode ? 'bg-white/5 hover:bg-white/10 text-gray-300' : 'bg-gray-100 hover:bg-gray-200 text-gray-600'}`}>
                  {t.hero.clear}
                </button>
              </div>
            )}

            {/* Yükleniyor */}
            {isLoading && !error && (
              <div className="text-center space-y-3">
                <p className={`text-sm animate-pulse ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>{statusMessage}</p>
                {queuePosition != null && queuePosition > 0 && (
                  <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium
                    ${isDarkMode ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20' : 'bg-yellow-50 text-yellow-600 border border-yellow-200'}`}>
                    <span className="w-1.5 h-1.5 bg-yellow-400 rounded-full animate-pulse" />
                    {t.queue.inQueue} {queuePosition}. {t.queue.position}
                  </span>
                )}
              </div>
            )}

            {/* Başarılı Sonuç */}
            {resultLink && (
              <div className={`p-5 rounded-2xl border space-y-4 animate-in zoom-in-95 duration-300
                ${isDarkMode ? 'bg-purple-500/[0.06] border-purple-500/20' : 'bg-purple-50 border-purple-200'}`}>
                <div className="flex items-center gap-2">
                  <CheckCircle size={18} className="text-purple-500" />
                  <span className="font-bold text-purple-500 text-sm">{t.hero.success}</span>
                </div>

                <div className={`flex items-center gap-2 p-3 rounded-xl ${isDarkMode ? 'bg-black/30' : 'bg-white border'}`}>
                  <input readOnly value={resultLink} onClick={(e) => (e.target as HTMLInputElement).select()} className="bg-transparent w-full outline-none text-sm text-gray-400 cursor-text select-all" />
                  <button onClick={() => handleCopy(resultLink)}
                    className={`p-2 rounded-lg transition-colors ${isDarkMode ? 'hover:bg-white/5' : 'hover:bg-gray-100'}`}>
                    {copied ? <CheckCircle size={16} className="text-green-400" /> : <Copy size={16} className="text-gray-500" />}
                  </button>
                  <a href={resultLink} target="_blank" rel="noreferrer"
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-sm rounded-lg font-medium transition-all flex items-center gap-1.5 whitespace-nowrap">
                    {t.hero.go} <ExternalLink size={14} />
                  </a>
                </div>

                {/* Güvenlik rozeti */}
                {safetyStatus && (
                  <div className="flex justify-center">
                    {safetyStatus === 'scanning' && (
                      <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium animate-pulse
                        ${isDarkMode ? 'bg-yellow-500/10 text-yellow-400' : 'bg-yellow-50 text-yellow-600'}`}>
                        <Shield size={13} /> {t.safety.scanning}
                      </span>
                    )}
                    {safetyStatus === 'Clean' && (
                      <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium
                        ${isDarkMode ? 'bg-green-500/10 text-green-400' : 'bg-green-50 text-green-600'}`}>
                        <Shield size={13} /> {t.safety.clean}
                      </span>
                    )}
                    {(safetyStatus === 'Malicious') && (
                      <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
                        <Shield size={13} /> {t.safety.malicious}
                      </span>
                    )}
                    {(safetyStatus === 'Suspicious') && (
                      <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-orange-500/10 text-orange-400 border border-orange-500/20">
                        <Shield size={13} /> {t.safety.suspicious}
                      </span>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ══════════ CANLI İSTATİSTİKLER ══════════ */}
      <section className="py-6 px-4">
        <div className="max-w-2xl mx-auto flex flex-wrap justify-center gap-6 md:gap-10">
          <div className="flex items-center gap-2.5">
            <div className="relative">
              <Activity size={16} className="text-purple-500" />
              <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-purple-500 rounded-full animate-ping" />
            </div>
            <span className={`text-sm ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>{t.stats.bypassed}:</span>
            <span className="font-bold text-base">{stats.links.toLocaleString()}</span>
          </div>
          <div className={`h-5 w-px ${isDarkMode ? 'bg-white/10' : 'bg-gray-300'} hidden md:block`} />
          <div className="flex items-center gap-2.5">
            <Users size={16} className="text-blue-500" />
            <span className={`text-sm ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>{t.stats.active}:</span>
            <span className="font-bold text-base">{stats.users.toLocaleString()}</span>
          </div>
          <div className={`h-5 w-px ${isDarkMode ? 'bg-white/10' : 'bg-gray-300'} hidden md:block`} />
          <span className="flex items-center gap-1.5 text-xs font-medium text-green-500">
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" /> {t.stats.live}
          </span>
        </div>
      </section>

      {/* ══════════ ÖZELLİK KARTLARI ══════════ */}
      <section className="py-12 px-4">
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
          {[
            { icon: <Shield size={24} />, color: "from-purple-500/20 to-purple-600/5", ...t.features.security },
            { icon: <Zap size={24} />, color: "from-blue-500/20 to-blue-600/5", ...t.features.speed },
            { icon: <Smartphone size={24} />, color: "from-emerald-500/20 to-emerald-600/5", ...t.features.device },
          ].map((f, i) => (
            <div key={i} className={`group relative p-6 md:p-8 rounded-2xl border transition-all duration-300
              ${isDarkMode
                ? 'bg-white/[0.02] border-white/5 hover:border-purple-500/20 hover:bg-white/[0.04]'
                : 'bg-white border-gray-100 shadow-sm hover:shadow-md hover:border-purple-200'}`}>
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-4
                ${isDarkMode ? 'text-purple-400' : 'text-purple-600'}`}>
                {f.icon}
              </div>
              <h3 className="text-lg font-bold mb-2">{f.title}</h3>
              <p className={`text-sm leading-relaxed ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ══════════ NASIL ÇALIŞIR? ══════════ */}
      <section className="py-12 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-12">{t.howItWorks.title}</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8 relative">
            {/* Bağlayıcı çizgi (desktop) */}
            <div className={`hidden md:block absolute top-10 left-[20%] right-[20%] h-px ${isDarkMode ? 'bg-gradient-to-r from-transparent via-purple-500/30 to-transparent' : 'bg-gradient-to-r from-transparent via-purple-300 to-transparent'}`} />

            {[t.howItWorks.step1, t.howItWorks.step2, t.howItWorks.step3].map((step, i) => (
              <div key={i} className="text-center relative">
                <div className={`w-14 h-14 rounded-2xl mx-auto mb-4 flex items-center justify-center text-xl font-bold relative z-10
                  ${isDarkMode
                    ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                    : 'bg-purple-100 text-purple-600 border border-purple-200'}`}>
                  {i + 1}
                </div>
                <h3 className="font-bold text-base mb-2">{step.title}</h3>
                <p className={`text-sm leading-relaxed ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════ TELEGRAM BANNER ══════════ */}
      <section className="py-8 px-4">
        <div className={`max-w-3xl mx-auto rounded-2xl p-6 md:p-8 flex flex-col md:flex-row items-center gap-6 border
          ${isDarkMode
            ? 'bg-gradient-to-r from-blue-500/[0.06] to-purple-500/[0.06] border-blue-500/10'
            : 'bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200'}`}>
          <div className="w-14 h-14 rounded-2xl bg-[#2AABEE] flex items-center justify-center flex-shrink-0">
            <Send size={22} className="text-white" />
          </div>
          <div className="flex-grow text-center md:text-left">
            <h3 className="font-bold text-lg mb-1">{t.telegram.title}</h3>
            <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>{t.telegram.desc}</p>
          </div>
          <a href="https://t.me/ReklamAtlaBot" target="_blank" rel="noopener noreferrer"
            className="px-6 py-3 bg-[#2AABEE] hover:bg-[#229ED9] text-white rounded-xl font-medium text-sm transition-colors flex items-center gap-2 whitespace-nowrap">
            <Send size={16} /> {t.telegram.button}
          </a>
        </div>
      </section>

      {/* ══════════ SSS ══════════ */}
      <section className="py-12 px-4">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-8">{t.faq.title}</h2>
          <div className="space-y-3">
            {[
              { question: t.faq.q1, answer: t.faq.a1 },
              { question: t.faq.q2, answer: t.faq.a2 },
              { question: t.faq.q3, answer: t.faq.a3 },
              { question: t.faq.q4, answer: t.faq.a4 },
              { question: t.faq.q5, answer: t.faq.a5 },
            ].map((item, i) => (
              <FAQItem key={i} {...item} isDarkMode={isDarkMode} />
            ))}
          </div>
        </div>
      </section>

      {/* ══════════ FOOTER ══════════ */}
      <footer className={`w-full py-10 border-t text-center z-20
        ${isDarkMode ? 'bg-black/30 border-white/5 text-gray-600' : 'bg-white border-gray-200 text-gray-400'}`}>
        <div className="flex justify-center gap-8 mb-4 text-sm font-medium">
          <Link href="/privacy" className="hover:text-purple-400 transition">{t.footer.privacy}</Link>
          <Link href="/terms" className="hover:text-purple-400 transition">{t.footer.terms}</Link>
          <a href="mailto:support@reklamatla.com" className="hover:text-purple-400 transition">{t.footer.contact}</a>
        </div>
        <p className="text-xs">&copy; 2026 ReklamAtla.com — {t.footer.rights}</p>
      </footer>
    </main>
  );
}