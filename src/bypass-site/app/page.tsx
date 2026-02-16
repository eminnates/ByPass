"use client";

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import {
  Clipboard, ArrowRight, Zap, CheckCircle, Shield,
  Moon, Sun, Coffee, Plug, ChevronDown, ChevronUp,
  CheckCircle as CheckIcon, Globe, Loader2, Users, Activity
} from 'lucide-react';

// --- TERCÜME VERİTABANI (DİL PAKETİ) ---
const translations: any = {
  tr: {
    nav: { home: "Ana Sayfa", coffee: "Kahve Ismarla", discord: "Discord" },
    hero: {
      placeholder: "Başlamak için bir bağlantı girin...",
      button: "ATLA",
      autoRedirect: "Otomatik Yönlendirme",
      processing: "Çözülüyor...",
      success: "Bypass Başarılı!",
      go: "Git"
    },
    stats: { bypassed: "Bugün Çözülen Link", active: "Aktif Kullanıcı" },
    features: {
      site: { title: "Desteklenen Siteler", desc: "Linkvertise, Lootlabs, Mboost ve dahası." },
      speed: { title: "Anında Yanıt", desc: "Bekleme süresi olmadan direkt hedefe ulaşın." },
      secure: { title: "Güvenli Geçiş", desc: "Zararlı reklamlardan cihazınızı koruyun." }
    },
    faq: {
      title: "Merak Edilenler",
      q1: "Paylaşılan Linkler (Pastes) Destekleniyor mu?", a1: "Evet, servisimiz popüler paste servislerini destekler.",
      q2: "Hangi web siteleri destekleniyor?", a2: "Linkvertise, Lootlabs, Mboost, Sub2get ve daha birçok popüler servis.",
      q3: "Hata alırsam ne yapmalıyım?", a3: "Bir hata ile karşılaşırsanız sayfayı yenilemeyi deneyin.", note: "NOT: Hata devam ederse Discord'a gelin.",
      q4: "Bypass.link ücretsiz mi?", a4: "Evet, servisimiz tamamen ücretsizdir.",
      q5: "Discord botu var mı?", a5: "Şu an için aktif bir botumuz bulunmamaktadır."
    },
    footer: { privacy: "Gizlilik Politikası", terms: "Kullanım Şartları", contact: "İletişim", rights: "Tüm hakları saklıdır." }
  },
  en: {
    nav: { home: "Home", coffee: "Buy Coffee", discord: "Discord" },
    hero: {
      placeholder: "Paste a link to start...",
      button: "BYPASS",
      autoRedirect: "Auto Redirect",
      processing: "Bypassing...",
      success: "Bypass Successful!",
      go: "Go"
    },
    stats: { bypassed: "Links Bypassed Today", active: "Active Users" },
    features: {
      site: { title: "Supported Sites", desc: "Linkvertise, Lootlabs, Mboost and more." },
      speed: { title: "Instant Response", desc: "Reach the destination without waiting." },
      secure: { title: "Safe Bypass", desc: "Protect your device from malicious ads." }
    },
    faq: {
      title: "Frequently Asked",
      q1: "Are Paste Links Supported?", a1: "Yes, we support popular paste services.",
      q2: "Which websites are supported?", a2: "Linkvertise, Lootlabs, Mboost, Sub2get and many more.",
      q3: "What if I get an error?", a3: "Try refreshing the page if you encounter an error.", note: "NOTE: Join Discord if error persists.",
      q4: "Is Bypass.link free?", a4: "Yes, our service is completely free.",
      q5: "Is there a Discord bot?", a5: "We do not have an active bot at the moment."
    },
    footer: { privacy: "Privacy Policy", terms: "Terms of Use", contact: "Contact", rights: "All rights reserved." }
  },
  de: {
    nav: { home: "Startseite", coffee: "Kaffee Kaufen", discord: "Discord" },
    hero: { placeholder: "Link hier einfügen...", button: "UMGEHEN", processing: "Verarbeitung...", autoRedirect: "Auto-Weiterleitung", success: "Bypass Erfolgreich!", go: "Los" },
    stats: { bypassed: "Heute Umgangen", active: "Aktive Nutzer" },
    features: {
      site: { title: "Unterstützte Seiten", desc: "Linkvertise, Lootlabs, Mboost und mehr." },
      speed: { title: "Sofortige Antwort", desc: "Ziel ohne Wartezeit erreichen." },
      secure: { title: "Sicherer Bypass", desc: "Schützen Sie Ihr Gerät vor Werbung." }
    },
    faq: {
      title: "Häufig Gestellt",
      q1: "Werden Paste-Links unterstützt?", a1: "Ja, wir unterstützen gängige Dienste.",
      q2: "Welche Webseiten?", a2: "Linkvertise, Lootlabs, Mboost und viele mehr.",
      q3: "Was tun bei Fehlern?", a3: "Versuchen Sie, die Seite neu zu laden.", note: "HINWEIS: Kommen Sie bei Fehlern auf Discord.",
      q4: "Ist es kostenlos?", a4: "Ja, unser Service ist komplett kostenlos.",
      q5: "Gibt es einen Discord-Bot?", a5: "Derzeit haben wir keinen aktiven Bot."
    },
    footer: { privacy: "Datenschutz", terms: "Nutzungsbedingungen", contact: "Kontakt", rights: "Alle Rechte vorbehalten." }
  },
  es: {
    nav: { home: "Inicio", coffee: "Comprar Café", discord: "Discord" },
    hero: { placeholder: "Pega un enlace aquí...", button: "SALTAR", processing: "Procesando...", autoRedirect: "Redirección Auto", success: "¡Bypass Exitoso!", go: "Ir" },
    stats: { bypassed: "Saltados Hoy", active: "Usuarios Activos" },
    features: {
      site: { title: "Sitios Soportados", desc: "Linkvertise, Lootlabs, Mboost y más." },
      speed: { title: "Respuesta Instantánea", desc: "Llega al destino sin esperar." },
      secure: { title: "Salto Seguro", desc: "Protege tu dispositivo de anuncios." }
    },
    faq: {
      title: "Preguntas Frecuentes",
      q1: "¿Enlaces Paste soportados?", a1: "Sí, soportamos servicios populares.",
      q2: "¿Qué sitios web?", a2: "Linkvertise, Lootlabs, Mboost y muchos más.",
      q3: "¿Error?", a3: "Intenta recargar la página.", note: "NOTA: Únete a Discord si persiste.",
      q4: "¿Es gratis?", a4: "Sí, es completamente gratis.",
      q5: "¿Hay bot de Discord?", a5: "No tenemos un bot activo actualmente."
    },
    footer: { privacy: "Privacidad", terms: "Términos", contact: "Contacto", rights: "Reservados todos los derechos." }
  },
  ru: {
    nav: { home: "Главная", coffee: "Купить кофе", discord: "Discord" },
    hero: { placeholder: "Вставьте ссылку...", button: "ОБОЙТИ", processing: "Обработка...", autoRedirect: "Авто-перенаправление", success: "Обход Успешен!", go: "Перейти" },
    stats: { bypassed: "Обойдено сегодня", active: "Активные пользователи" },
    features: {
      site: { title: "Поддерживаемые сайты", desc: "Linkvertise, Lootlabs, Mboost и другие." },
      speed: { title: "Мгновенный ответ", desc: "Достигайте цели без ожидания." },
      secure: { title: "Безопасный обход", desc: "Защитите устройство от рекламы." }
    },
    faq: {
      title: "Частые вопросы",
      q1: "Поддерживаются ли Paste?", a1: "Да, мы поддерживаем популярные сервисы.",
      q2: "Какие сайты?", a2: "Linkvertise, Lootlabs, Mboost и многие другие.",
      q3: "Ошибка?", a3: "Попробуйте обновить страницу.", note: "ПРИМЕЧАНИЕ: Зайдите в Discord при ошибке.",
      q4: "Это бесплатно?", a4: "Да, сервис полностью бесплатен.",
      q5: "Есть ли бот?", a5: "На данный момент бота нет."
    },
    footer: { privacy: "Конфиденциальность", terms: "Условия", contact: "Контакты", rights: "Все права защищены." }
  },
};

// Varsayılan dil listesi (Diğer dillerin translation objesinde olduğundan emin olun)
const languages = [
  { code: 'tr', name: 'Türkçe', flag: '🇹🇷' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
];

// --- ADSENSE REKLAM BİLEŞENİ ---
const AdUnit = ({ client, slot, format = "auto", style }: any) => {
  useEffect(() => {
    try {
      // @ts-ignore
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch (e) {
      console.error("Adsense yükleme hatası:", e);
    }
  }, []);

  return (
    <ins
      className="adsbygoogle"
      style={style || { display: 'block' }}
      data-ad-client={client}
      data-ad-slot={slot}
      data-ad-format={format}
      data-full-width-responsive="true"
    ></ins>
  );
};

// --- DİL SEÇİCİ BİLEŞENİ ---
const LanguageSelector = ({ currentLang, setLang, isDarkMode }: any) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: any) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selected = languages.find(l => l.code === currentLang) || languages[0];

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 border
        ${isDarkMode
            ? 'bg-[#18181b] border-white/10 text-gray-200 hover:bg-white/5'
            : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
          }`}
      >
        <span className="text-lg">{selected.flag}</span>
        <span className="hidden sm:block">{selected.name}</span>
        <ChevronDown size={16} className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className={`absolute top-full right-0 mt-2 w-48 rounded-xl border shadow-xl overflow-hidden z-[70] animate-in fade-in zoom-in-95 duration-200
          ${isDarkMode ? 'bg-[#18181b] border-white/10' : 'bg-white border-gray-200'}
        `}>
          <div className="py-1">
            {languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => {
                  setLang(lang.code);
                  setIsOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors
                  ${currentLang === lang.code
                    ? (isDarkMode ? 'bg-purple-500/10 text-purple-400' : 'bg-purple-50 text-purple-600')
                    : (isDarkMode ? 'text-gray-300 hover:bg-white/5' : 'text-gray-700 hover:bg-gray-50')
                  }
                `}
              >
                <span className="text-xl">{lang.flag}</span>
                <span className="font-medium">{lang.name}</span>
                {currentLang === lang.code && <CheckIcon size={14} className="ml-auto" />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// --- HEADER BİLEŞENİ ---
const Header = ({ isDarkMode, toggleTheme, currentLang, setLang, t }: any) => (
  <header className={`fixed top-0 left-0 w-full h-16 border-b z-[60] flex items-center px-4 md:px-8 transition-colors duration-300 
    ${isDarkMode ? 'bg-black border-white/10' : 'bg-white border-gray-200 shadow-sm'}`}>
    <div className="max-w-7xl w-full mx-auto flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className={`w-10 h-10 border rounded flex items-center justify-center ${isDarkMode ? 'bg-[#121212] border-white/20' : 'bg-gray-100 border-gray-300'}`}>
          <Plug size={20} className={isDarkMode ? "text-purple-400" : "text-purple-600"} />
        </div>
        <span className="font-bold text-xl tracking-tight ml-2">Bypass.link</span>
      </div>

      <nav className="hidden md:flex items-center gap-6">
        <a href="#" className={`text-sm font-medium border-b-2 pb-1 transition-colors ${isDarkMode ? 'text-white border-white' : 'text-gray-900 border-gray-900'}`}>{t.nav.home}</a>

        <a href="https://buymeacoffee.com/" target="_blank" rel="noopener noreferrer" className={`text-sm font-medium transition-colors flex items-center gap-2 px-3 py-2 rounded-lg ${isDarkMode ? 'text-gray-300 hover:text-white hover:bg-white/5' : 'text-gray-600 hover:text-black hover:bg-gray-100'}`}>
          <Coffee size={16} className="text-yellow-500" /> {t.nav.coffee}
        </a>

        <a href="https://discord.gg/davet-kodu" target="_blank" rel="noopener noreferrer" className={`text-sm font-medium transition-colors flex items-center gap-2 px-3 py-2 rounded-lg ${isDarkMode ? 'text-gray-300 hover:text-white hover:bg-white/5' : 'text-gray-600 hover:text-black hover:bg-gray-100'}`}>
          {/* Discord SVG */}
          <svg className="w-5 h-5 text-[#5865F2]" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.419-2.1568 2.419zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.419-2.1568 2.419z" />
          </svg>
          {t.nav.discord}
        </a>
      </nav>

      <div className="flex items-center gap-3">
        <LanguageSelector currentLang={currentLang} setLang={setLang} isDarkMode={isDarkMode} />

        <div className="h-6 w-[1px] bg-gray-300 dark:bg-white/10 mx-1"></div>

        <button onClick={toggleTheme} className="hover:scale-110 transition-transform focus:outline-none p-2">
          {isDarkMode ? <Moon size={20} className="text-orange-300" fill="currentColor" /> : <Sun size={20} className="text-orange-500" fill="currentColor" />}
        </button>
      </div>
    </div>
  </header>
);

// --- SSS BİLEŞENİ ---
const FAQItem = ({ question, answer, isNote, isDarkMode }: any) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className={`mb-3 border rounded-xl overflow-hidden transition-all duration-300 ${isDarkMode ? 'bg-[#121214] border-white/5' : 'bg-white border-gray-200 shadow-sm'}`}>
      <button onClick={() => setIsOpen(!isOpen)} className="w-full px-6 py-5 flex items-center justify-between text-left hover:bg-white/5 transition-colors">
        <span className={`font-medium ${isDarkMode ? 'text-gray-200' : 'text-gray-800'}`}>{question}</span>
        {isOpen ? <ChevronUp size={20} className="text-purple-400" /> : <ChevronDown size={20} className="text-gray-500" />}
      </button>
      <div className={`transition-all duration-300 ease-in-out ${isOpen ? 'max-h-[500px] opacity-100 p-6 pt-0' : 'max-h-0 opacity-0 overflow-hidden'}`}>
        <div className={`text-sm leading-relaxed ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          {answer}
          {isNote && (
            <div className="mt-4 p-4 rounded-lg bg-purple-500/5 border border-purple-500/20">
              <p className="text-xs font-bold text-purple-400 uppercase tracking-wider mb-1">NOT:</p>
              <p className="text-xs italic text-purple-400/80">{isNote}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default function Home() {
  // --- STATE YÖNETİMİ ---
  const [url, setUrl] = useState('');
  const [autoRedirect, setAutoRedirect] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [lang, setLang] = useState('tr');

  // Backend Entegrasyonu State'leri
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [resultLink, setResultLink] = useState('');
  const [error, setError] = useState('');
  const [queuePosition, setQueuePosition] = useState<number | null>(null);
  const [safetyStatus, setSafetyStatus] = useState<string | null>(null);
  const [bypassId, setBypassId] = useState<number | null>(null);
  const [stats, setStats] = useState({ links: 14205, users: 342 });

  const toggleTheme = () => setIsDarkMode(!isDarkMode);
  const t = translations[lang] || translations['tr']; // Hata önlemek için fallback

  // --- API İSTEK FONKSİYONU ---
  const handleBypass = async () => {
    if (!url) return;

    setIsLoading(true);
    setError('');
    setResultLink('');
    setSafetyStatus(null);
    setBypassId(null);
    setStatusMessage('Sunucuya bağlanılıyor...');

    try {
      // 1. İSTEK: İşlemi Başlat
      const response = await fetch('http://127.0.0.1:8000/bypass', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
      });

      const data = await response.json();

      if (data.status === 'success') {
        finishProcess(data.resolved_url, data.id, data.safety_status);
      } else if (data.status === 'started' || data.status === 'pending') {
        if (data.queue_position != null) setQueuePosition(data.queue_position);
        pollStatus(data.id || data.check_id);
      } else {
        setError('Beklenmedik bir hata oluştu.');
        setIsLoading(false);
      }

    } catch (err) {
      setError('Sunucuya erişilemedi. Backend çalışıyor mu?');
      setIsLoading(false);
    }
  };

  // --- SÜREKLİ DURUM SORMA (POLLING) ---
  const pollStatus = (id: number) => {
    setStatusMessage('Link çözülüyor, lütfen bekleyin...');
    let attempts = 0;
    const MAX_ATTEMPTS = 40; // 40 × 3s = 120sn max

    const interval = setInterval(async () => {
      if (++attempts > MAX_ATTEMPTS) {
        clearInterval(interval);
        setError('İşlem zaman aşımına uğradı. Lütfen tekrar deneyin.');
        setIsLoading(false);
        setQueuePosition(null);
        return;
      }

      try {
        const res = await fetch(`http://127.0.0.1:8000/status/${id}`);
        const data = await res.json();

        // Kuyruk pozisyonunu güncelle
        if (data.queue_position != null) {
          setQueuePosition(data.queue_position);
          if (data.queue_position === 0) {
            setStatusMessage('Linkiniz şu an işleniyor...');
          } else {
            setStatusMessage(`Sırada ${data.queue_position}. sıradasınız...`);
          }
        }

        if (data.status === 'success') {
          clearInterval(interval);
          setQueuePosition(null);
          finishProcess(data.resolved_url, id, data.safety_status);
        } else if (data.status === 'failed' || data.status === 'error') {
          clearInterval(interval);
          setQueuePosition(null);

          // fail_reason'a göre özel hata mesajı
          if (data.fail_reason === 'link_not_found') {
            setError('Bu link artık geçerli değil veya kaldırılmış (404).');
          } else if (data.fail_reason === 'timeout') {
            setError('İşlem zaman aşımına uğradı. Lütfen tekrar deneyin.');
          } else {
            setError('Link çözülemedi. Lütfen tekrar deneyin.');
          }

          setIsLoading(false);
        }
      } catch (e) {
        clearInterval(interval);
        setQueuePosition(null);
        setError('Bağlantı koptu.');
        setIsLoading(false);
      }
    }, 3000);
  };

  // --- İŞLEM BİTİŞİ ---
  const finishProcess = (finalUrl: string, linkId?: number, initialSafety?: string) => {
    setResultLink(finalUrl);
    setIsLoading(false);
    setStatusMessage(t.hero.success);
    setSafetyStatus(initialSafety || null);
    if (linkId) setBypassId(linkId);

    // VT taraması arka planda devam ediyorsa polling başlat
    if (initialSafety === 'scanning' && linkId) {
      pollSafety(linkId);
    }

    if (autoRedirect) {
      setStatusMessage('Yönlendiriliyor...');
      setTimeout(() => {
        window.location.href = finalUrl;
      }, 1500);
    }
  };

  // --- GÜVENLİK DURUMU POLLING ---
  const pollSafety = (linkId: number) => {
    const safetyInterval = setInterval(async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/status/${linkId}`);
        const data = await res.json();
        if (data.safety_status && data.safety_status !== 'scanning') {
          setSafetyStatus(data.safety_status);
          clearInterval(safetyInterval);
        }
      } catch {
        clearInterval(safetyInterval);
      }
    }, 3000);
    // 30 saniye sonra durdur
    setTimeout(() => clearInterval(safetyInterval), 30000);
  };

  const faqData = [
    { question: t.faq.q1, answer: t.faq.a1 },
    { question: t.faq.q2, answer: t.faq.a2 },
    { question: t.faq.q3, answer: t.faq.a3, isNote: t.faq.note },
    { question: t.faq.q4, answer: t.faq.a4 },
    { question: t.faq.q5, answer: t.faq.a5 }
  ];

  // İstatistik animasyonu
  useEffect(() => {
    const interval = setInterval(() => {
      setStats(prev => ({
        links: prev.links + Math.floor(Math.random() * 3) + 1,
        users: prev.users + Math.floor(Math.random() * 4) - 1
      }));
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <main className={`min-h-screen flex flex-col items-center relative overflow-x-hidden transition-colors duration-300 ${isDarkMode ? 'bg-[#0f0f11] text-white' : 'bg-[#f8f9fa] text-gray-900'}`}>

      <style jsx global>{`
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: ${isDarkMode ? '#0a0a0c' : '#f1f5f9'}; }
        ::-webkit-scrollbar-thumb {
          background: ${isDarkMode ? 'linear-gradient(to bottom, #a855f7, #9333ea)' : '#c084fc'};
          border-radius: 20px;
        }
        * { scrollbar-width: thin; scrollbar-color: ${isDarkMode ? '#a855f7 #0a0a0c' : '#c084fc #f1f5f9'}; }
      `}</style>

      {/* HEADER */}
      <Header
        isDarkMode={isDarkMode}
        toggleTheme={toggleTheme}
        currentLang={lang}
        setLang={setLang}
        t={t}
      />

      {/* REKLAM ALANLARI */}
      <div className={`fixed top-16 z-50 w-full md:w-1/2 md:left-1/2 md:-translate-x-1/2 h-[90px] border-b overflow-hidden ${isDarkMode ? 'bg-black border-white/10' : 'bg-gray-100 border-gray-300'}`}>
        <AdUnit client="ca-pub-XXXXXXXXXX" slot="XXXXXXX" format="horizontal" style={{ display: 'block', height: '90px' }} />
      </div>

      <div className={`hidden xl:flex fixed left-0 top-[154px] bottom-0 w-[200px] border-r overflow-hidden ${isDarkMode ? 'bg-black border-white/10' : 'bg-gray-100 border-gray-300'}`}>
        <AdUnit client="ca-pub-XXXXXXXXXX" slot="XXXXXXX" format="vertical" />
      </div>

      <div className={`hidden xl:flex fixed right-0 top-[154px] bottom-0 w-[200px] border-l overflow-hidden ${isDarkMode ? 'bg-black border-white/10' : 'bg-gray-100 border-gray-300'}`}>
        <AdUnit client="ca-pub-XXXXXXXXXX" slot="XXXXXXX" format="vertical" />
      </div>

      {/* ANA İÇERİK */}
      <div className="w-full max-w-5xl px-4 pt-[220px] pb-12 z-10 flex flex-col items-center justify-center">
        <div className="text-center mb-12 relative">
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight italic">
            <span className="text-purple-500 drop-shadow-[0_0_20px_rgba(168,85,247,0.6)]">Bypass</span>.link
          </h1>
          {isDarkMode && <div className="absolute -top-10 left-1/2 -translate-x-1/2 w-64 h-32 bg-purple-600/20 blur-[100px] rounded-full" />}
        </div>

        <div className="w-full max-w-4xl space-y-6">
          <div className={`flex flex-col md:flex-row gap-3 p-3 rounded-2xl transition-all duration-300 ${isDarkMode ? 'bg-[#18181b]' : 'bg-white shadow-xl border border-gray-100'}`}>
            <div className={`flex-grow flex items-center rounded-xl px-4 py-1 ${isDarkMode ? 'bg-black/40' : 'bg-gray-50'}`}>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder={t.hero.placeholder}
                disabled={isLoading}
                className="w-full bg-transparent py-4 outline-none text-lg disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <button
                onClick={() => navigator.clipboard.readText().then(setUrl)}
                disabled={isLoading}
                className="p-2 hover:text-purple-400 transition-colors disabled:opacity-50"
              >
                <Clipboard size={22} />
              </button>
            </div>
            <button
              onClick={handleBypass}
              disabled={isLoading || !url}
              className={`md:w-64 text-white font-bold py-4 px-8 rounded-xl transition-all flex items-center justify-center gap-3 text-lg shadow-lg active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed
                ${isLoading ? 'bg-gray-600 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-500'}
              `}
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="animate-spin" size={22} />
                  <span>{t.hero.processing}</span>
                </div>
              ) : (
                <>
                  {t.hero.button} <ArrowRight size={22} />
                </>
              )}
            </button>
          </div>

          {/* İSTATİSTİK ALANI */}
          <div className="flex flex-wrap justify-center gap-6 md:gap-12 mt-2 px-4 animate-in fade-in slide-in-from-top-2 duration-700">
            <div className="flex items-center gap-3">
              <div className="relative"><Activity size={20} className="text-purple-500" /><span className="absolute -top-1 -right-1 w-2 h-2 bg-purple-500 rounded-full animate-ping" /></div>
              <div className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>{t.stats.bypassed}: <span className={`font-bold ml-1 text-lg ${isDarkMode ? 'text-white' : 'text-black'}`}>{stats.links.toLocaleString()}</span></div>
            </div>
            <div className="h-6 w-[1px] bg-gray-700/50 hidden md:block"></div>
            <div className="flex items-center gap-3">
              <div className="relative"><Users size={20} className="text-blue-500" /></div>
              <div className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>{t.stats.active}: <span className={`font-bold ml-1 text-lg ${isDarkMode ? 'text-white' : 'text-black'}`}>{stats.users.toLocaleString()}</span></div>
            </div>
          </div>

          {/* --- SONUÇ VE DURUM ALANI --- */}

          {/* Hata Mesajı */}
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-xl text-red-400 text-center font-medium animate-in fade-in">
              {error}
            </div>
          )}

          {/* Durum Mesajı (Sadece yüklenirken ve hata yoksa) */}
          {isLoading && !error && (
            <div className="text-center space-y-2">
              <div className="text-sm text-gray-400 animate-pulse">
                {statusMessage}
              </div>
              {queuePosition != null && queuePosition > 0 && (
                <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium ${isDarkMode ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20' : 'bg-yellow-50 text-yellow-600 border border-yellow-200'}`} >
                  <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
                  Kuyrukta {queuePosition}. sırada
                </div>
              )}
              {queuePosition === 0 && (
                <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium ${isDarkMode ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20' : 'bg-purple-50 text-purple-600 border border-purple-200'}`}>
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" />
                  Şu an işleniyor
                </div>
              )}
            </div>
          )}

          {/* BAŞARILI SONUÇ KARTI */}
          {resultLink && (
            <div className={`p-6 rounded-2xl border animate-in zoom-in-95 duration-300 flex flex-col gap-4
              ${isDarkMode ? 'bg-purple-900/10 border-purple-500/30' : 'bg-purple-50 border-purple-200'}`}>

              <div className="flex items-center justify-between">
                <span className="font-bold text-purple-500 flex items-center gap-2">
                  <CheckCircle size={20} /> {t.hero.success}
                </span>
                <div className="flex items-center gap-2">
                  {safetyStatus === 'scanning' && (
                    <span className="text-xs text-yellow-400 flex items-center gap-1 animate-pulse">
                      <Shield size={14} /> Güvenlik taranıyor...
                    </span>
                  )}
                  {safetyStatus === 'Clean' && (
                    <span className="text-xs text-green-400 flex items-center gap-1">
                      <Shield size={14} /> Güvenli ✓
                    </span>
                  )}
                  {safetyStatus === 'Malicious' && (
                    <span className="text-xs text-red-400 flex items-center gap-1 font-bold">
                      <Shield size={14} /> ⚠️ Tehlikeli!
                    </span>
                  )}
                  {safetyStatus === 'Suspicious' && (
                    <span className="text-xs text-orange-400 flex items-center gap-1">
                      <Shield size={14} /> Şüpheli
                    </span>
                  )}
                  {safetyStatus === 'Error' && (
                    <span className="text-xs text-gray-400 flex items-center gap-1">
                      <Shield size={14} /> Taranamadı
                    </span>
                  )}
                  {autoRedirect && <span className="text-xs text-gray-400 animate-pulse">Otomatik yönlendiriliyor...</span>}
                </div>
              </div>

              <div className={`flex items-center gap-2 p-3 rounded-lg ${isDarkMode ? 'bg-black/40' : 'bg-white border'}`}>
                <input
                  readOnly
                  value={resultLink}
                  className="bg-transparent w-full outline-none text-sm text-gray-500"
                />
                <a
                  href={resultLink}
                  target="_blank"
                  rel="noreferrer"
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-sm rounded-lg font-medium transition-colors whitespace-nowrap flex items-center gap-2"
                >
                  {t.hero.go} <Globe size={16} />
                </a>
              </div>
            </div>
          )}

          <div className="flex items-center justify-center gap-6">
            <div className="flex items-center gap-3 cursor-pointer group" onClick={() => setAutoRedirect(!autoRedirect)}>
              <div className={`w-10 h-5 rounded-full p-1 transition-colors ${autoRedirect ? 'bg-purple-600' : 'bg-gray-600'}`}>
                <div className={`w-3 h-3 bg-white rounded-full transition-transform ${autoRedirect ? 'translate-x-5' : 'translate-x-0'}`} />
              </div>
              <span className={`text-sm font-medium transition-colors ${isDarkMode ? 'text-gray-400 group-hover:text-white' : 'text-gray-600 group-hover:text-black'}`}>{t.hero.autoRedirect}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ÖZELLİKLER */}
      <div className="w-full max-w-5xl px-4 py-12 grid grid-cols-1 md:grid-cols-3 gap-6 z-20">
        {[
          { icon: <CheckCircle className="text-purple-400" />, title: t.features.site.title, desc: t.features.site.desc },
          { icon: <Zap className="text-yellow-400" />, title: t.features.speed.title, desc: t.features.speed.desc },
          { icon: <Shield className="text-fuchsia-400" />, title: t.features.secure.title, desc: t.features.secure.desc }
        ].map((f, i) => (
          <div key={i} className={`p-8 rounded-3xl border transition-all ${isDarkMode ? 'bg-[#121214] border-white/5 hover:border-purple-500/30' : 'bg-white border-gray-100 shadow-md hover:border-purple-300'}`}>
            <div className="mb-4">{f.icon}</div>
            <h3 className="text-xl font-bold mb-2">{f.title}</h3>
            <p className="text-sm opacity-60 leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>

      {/* SSS BÖLÜMÜ */}
      <div className="w-full max-w-4xl px-4 pb-24 z-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">{t.faq.title}</h2>
          <div className="w-16 h-1 bg-purple-600 mx-auto rounded-full" />
        </div>
        <div className="space-y-2">
          {faqData.map((item, index) => (
            <FAQItem key={index} {...item} isDarkMode={isDarkMode} />
          ))}
        </div>
      </div>

      {/* FOOTER */}
      <footer className={`w-full py-12 border-t text-center text-xs z-20 ${isDarkMode ? 'bg-black border-white/5 text-gray-500' : 'bg-white border-gray-200 text-gray-400'}`}>
        <div className="flex justify-center gap-8 mb-6 text-sm font-medium">
          <Link href="/privacy" className="hover:text-purple-400 transition">
            {t.footer.privacy}
          </Link>
          <Link href="/terms" className="hover:text-purple-400 transition">
            {t.footer.terms}
          </Link>
          <a href="mailto:support@bypass.link" className="hover:text-purple-400 transition">{t.footer.contact}</a>
        </div>
        <p>&copy; 2026 Bypass.link Servisi. {t.footer.rights}</p>
      </footer>

    </main>
  );
}