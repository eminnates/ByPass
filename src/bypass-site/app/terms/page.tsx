"use client";

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { Moon, Sun, Coffee, Plug, ChevronDown } from 'lucide-react';

// --- DİL VE İÇERİK VERİTABANI ---
const translations: any = {
    tr: {
        nav: { home: "Ana Sayfa", coffee: "Kahve Ismarla", discord: "Discord" },
        terms: {
            title: "Kullanım Şartları",
            updated: "Son Güncelleme: 13.01.2026",
            intro: "Bypass.link hizmetini kullanarak, aşağıdaki kullanım şartlarını kabul etmiş sayılırsınız.",
            h1: "1. Hizmetin Kullanımı",
            p1: "Bypass.link, link kısaltma servislerindeki bekleme sürelerini atlamaya yardımcı olan bir araçtır. Sadece yasal amaçlar için kullanılmalıdır.",
            h2: "2. Sorumluluk Reddi",
            p2: "Hizmet 'olduğu gibi' sunulmaktadır. Bypass.link, hedef linklerin güvenliğinden sorumlu tutulamaz.",
            h3: "3. Değişiklikler",
            p3: "Yönetim, bu şartları önceden haber vermeksizin değiştirme hakkını saklı tutar.",
            h4: "4. Yetkili Yargı",
            p4: "Bu şartlar Türkiye Cumhuriyeti yasalarına tabidir ve Konya Mahkemeleri yetkilidir."
        },
        footer: "Tüm Hakları Saklıdır."
    },
    en: {
        nav: { home: "Home", coffee: "Buy Coffee", discord: "Discord" },
        terms: {
            title: "Terms of Use",
            updated: "Last Updated: 01/13/2026",
            intro: "By using the Bypass.link service, you agree to the following terms of use.",
            h1: "1. Use of Service",
            p1: "Bypass.link is a tool to bypass waiting times. It must be used for legal purposes only.",
            h2: "2. Disclaimer",
            p2: "The service is provided 'as-is'. We are not responsible for the safety of destination links.",
            h3: "3. Changes",
            p3: "Management reserves the right to change these terms without prior notice.",
            h4: "4. Jurisdiction",
            p4: "These terms are subject to the laws of the Republic of Turkey (Konya Courts)."
        },
        footer: "All Rights Reserved."
    },
    de: { nav: { home: "Startseite", coffee: "Kaffee Kaufen", discord: "Discord" }, terms: { title: "Nutzungsbedingungen", updated: "Datum: 13.01.2026", intro: "Durch die Nutzung stimmen Sie zu...", h1: "1. Nutzung", p1: "Nur für legale Zwecke.", h2: "2. Haftungsausschluss", p2: "Dienst wird 'wie besehen' bereitgestellt.", h3: "3. Änderungen", p3: "Änderungen vorbehalten.", h4: "4. Gerichtsbarkeit", p4: "Konya, Türkei." }, footer: "Alle Rechte vorbehalten." },
    es: { nav: { home: "Inicio", coffee: "Comprar Café", discord: "Discord" }, terms: { title: "Términos de Uso", updated: "Fecha: 13/01/2026", intro: "Al usar, usted acepta...", h1: "1. Uso", p1: "Solo fines legales.", h2: "2. Descargo", p2: "Tal cual.", h3: "3. Cambios", p3: "Sujeto a cambios.", h4: "4. Jurisdicción", p4: "Konya, Turquía." }, footer: "Reservados todos los derechos." },
    ru: { nav: { home: "Главная", coffee: "Купить кофе", discord: "Discord" }, terms: { title: "Условия использования", updated: "Дата: 13.01.2026", intro: "Используя сервис, вы соглашаетесь...", h1: "1. Использование", p1: "Только законные цели.", h2: "2. Отказ", p2: "Как есть.", h3: "3. Изменения", p3: "Могут быть изменены.", h4: "4. Юрисдикция", p4: "Конья, Турция." }, footer: "Все права защищены." },
};

const languages = [
    { code: 'tr', name: 'Türkçe', flag: '🇹🇷' },
    { code: 'en', name: 'English', flag: '🇺🇸' },
    { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
    { code: 'es', name: 'Español', flag: '🇪🇸' },
    { code: 'ru', name: 'Русский', flag: '🇷🇺' },
];

const AdUnit = ({ client, slot, format = "auto", style }: any) => {
    useEffect(() => { try { (window as any).adsbygoogle = (window as any).adsbygoogle || []; (window as any).adsbygoogle.push({}); } catch (e) { } }, []);
    return <ins className="adsbygoogle" style={style || { display: 'block' }} data-ad-client={client} data-ad-slot={slot} data-ad-format={format} data-full-width-responsive="true"></ins>;
};

// --- HEADER BİLEŞENİ ---
const Header = ({ isDarkMode, toggleTheme, currentLang, setLang, t }: any) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const selected = languages.find((l: any) => l.code === currentLang) || languages[0];

    useEffect(() => {
        const handleClickOutside = (event: any) => { if (dropdownRef.current && !dropdownRef.current.contains(event.target)) setIsOpen(false); };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    return (
        <header className={`fixed top-0 left-0 w-full h-16 border-b z-[60] flex items-center px-4 md:px-8 transition-colors duration-300 ${isDarkMode ? 'bg-black border-white/10' : 'bg-white border-gray-200 shadow-sm'}`}>
            <div className="max-w-7xl w-full mx-auto flex items-center justify-between">
                <Link href="/" className="flex items-center gap-2">
                    <div className={`w-10 h-10 border rounded flex items-center justify-center ${isDarkMode ? 'bg-[#121212] border-white/20' : 'bg-gray-100 border-gray-300'}`}>
                        <Plug size={20} className={isDarkMode ? "text-green-400" : "text-green-600"} />
                    </div>
                    <span className={`font-bold text-xl tracking-tight ml-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Bypass.link</span>
                </Link>

                {/* LİNKLER EKLENDİ */}
                <nav className="hidden md:flex items-center gap-6">
                    <Link href="/" className={`text-sm font-medium transition-colors ${isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-black'}`}>{t.nav.home}</Link>
                    <a href="https://buymeacoffee.com/" target="_blank" rel="noopener noreferrer" className={`text-sm font-medium transition-colors flex items-center gap-2 px-3 py-2 rounded-lg ${isDarkMode ? 'text-gray-300 hover:text-white hover:bg-white/5' : 'text-gray-600 hover:text-black hover:bg-gray-100'}`}>
                        <Coffee size={16} className="text-yellow-500" /> {t.nav.coffee}
                    </a>
                    <a href="https://discord.gg/davet-kodu" target="_blank" rel="noopener noreferrer" className={`text-sm font-medium transition-colors flex items-center gap-2 px-3 py-2 rounded-lg ${isDarkMode ? 'text-gray-300 hover:text-white hover:bg-white/5' : 'text-gray-600 hover:text-black hover:bg-gray-100'}`}>
                        <svg className="w-5 h-5 text-[#5865F2]" viewBox="0 0 24 24" fill="currentColor"><path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.419-2.1568 2.419zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.419-2.1568 2.419z" /></svg>
                        {t.nav.discord}
                    </a>
                </nav>

                <div className="flex items-center gap-3">
                    <div className="relative" ref={dropdownRef}>
                        <button onClick={() => setIsOpen(!isOpen)} className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 border ${isDarkMode ? 'bg-[#18181b] border-white/10 text-gray-200 hover:bg-white/5' : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'}`}>
                            <span className="text-lg">{selected.flag}</span>
                            <span className="hidden sm:block">{selected.name}</span>
                            <ChevronDown size={16} />
                        </button>
                        {isOpen && (
                            <div className={`absolute top-full right-0 mt-2 w-48 rounded-xl border shadow-xl overflow-hidden z-[70] ${isDarkMode ? 'bg-[#18181b] border-white/10' : 'bg-white border-gray-200'}`}>
                                <div className="py-1">
                                    {languages.map((lang: any) => (
                                        <button key={lang.code} onClick={() => { setLang(lang.code); setIsOpen(false); }} className={`w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors ${currentLang === lang.code ? (isDarkMode ? 'bg-green-500/10 text-green-400' : 'bg-green-50 text-green-600') : (isDarkMode ? 'text-gray-300 hover:bg-white/5' : 'text-gray-700 hover:bg-gray-50')}`}>
                                            <span className="text-xl">{lang.flag}</span> <span className="font-medium">{lang.name}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                    <button onClick={toggleTheme} className="hover:scale-110 transition-transform focus:outline-none p-2">
                        {isDarkMode ? <Moon size={20} className="text-orange-300" fill="currentColor" /> : <Sun size={20} className="text-orange-500" fill="currentColor" />}
                    </button>
                </div>
            </div>
        </header>
    );
};

export default function TermsPage() {
    const [isDarkMode, setIsDarkMode] = useState(true);
    const [lang, setLang] = useState('tr');
    // SEÇİLEN DİL İÇERİĞİNİ GÜNCELLE
    const t = translations[lang] || translations['tr'];
    const toggleTheme = () => setIsDarkMode(!isDarkMode);

    return (
        <main className={`min-h-screen flex flex-col items-center relative transition-colors duration-300 ${isDarkMode ? 'bg-[#0f0f11] text-white' : 'bg-[#f8f9fa] text-gray-900'}`}>

            <Header isDarkMode={isDarkMode} toggleTheme={toggleTheme} currentLang={lang} setLang={setLang} t={t} />

            {/* REKLAMLAR */}
            <div className={`fixed top-16 z-50 w-full md:w-1/2 md:left-1/2 md:-translate-x-1/2 h-[90px] border-b overflow-hidden ${isDarkMode ? 'bg-black border-white/10' : 'bg-gray-100 border-gray-300'}`}>
                <AdUnit client="ca-pub-XXXXXXXXXX" slot="XXXXXXX" format="horizontal" style={{ display: 'block', height: '90px' }} />
            </div>
            <div className={`hidden xl:flex fixed left-0 top-[154px] bottom-0 w-[200px] border-r overflow-hidden ${isDarkMode ? 'bg-black border-white/10' : 'bg-gray-100 border-gray-300'}`}>
                <AdUnit client="ca-pub-XXXXXXXXXX" slot="XXXXXXX" format="vertical" />
            </div>
            <div className={`hidden xl:flex fixed right-0 top-[154px] bottom-0 w-[200px] border-l overflow-hidden ${isDarkMode ? 'bg-black border-white/10' : 'bg-gray-100 border-gray-300'}`}>
                <AdUnit client="ca-pub-XXXXXXXXXX" slot="XXXXXXX" format="vertical" />
            </div>

            {/* İÇERİK ALANI (DİNAMİK VERİ İLE DEĞİŞTİ) */}
            <div className="w-full max-w-4xl px-4 pt-[220px] pb-12 z-10">
                <div className={`p-8 md:p-12 rounded-3xl border ${isDarkMode ? 'bg-[#121214] border-white/5' : 'bg-white border-gray-200 shadow-sm'}`}>
                    <h1 className="text-3xl md:text-4xl font-bold mb-8 text-green-500">{t.terms.title}</h1>

                    <div className={`space-y-6 leading-relaxed ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                        <p className="font-medium opacity-70">{t.terms.updated}</p>

                        <p>{t.terms.intro}</p>

                        <h3 className={`text-xl font-bold mt-6 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{t.terms.h1}</h3>
                        <p>{t.terms.p1}</p>

                        <h3 className={`text-xl font-bold mt-6 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{t.terms.h2}</h3>
                        <p>{t.terms.p2}</p>

                        <h3 className={`text-xl font-bold mt-6 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{t.terms.h3}</h3>
                        <p>{t.terms.p3}</p>

                        <h3 className={`text-xl font-bold mt-6 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{t.terms.h4}</h3>
                        <p>{t.terms.p4}</p>
                    </div>
                </div>
            </div>

            <footer className="py-8 text-center text-xs opacity-50">
                &copy; 2026 Bypass.link - {t.footer}
            </footer>
        </main>
    );
}