import { Metadata } from "next";
import Link from "next/link";
import { blogPosts } from "./data";
import { ArrowRight, Clock, Calendar, Zap } from "lucide-react";

export const metadata: Metadata = {
    title: "Blog — Reklam Atlama Rehberleri | ReklamAtla",
    description:
        "OUO.io bypass, AyLink reklam atlama, kısa link çözme rehberleri. Kısaltılmış linkler hakkında bilmeniz gereken her şey.",
    keywords: [
        "ouo bypass",
        "aylink reklam atlama",
        "kısa link çözme",
        "reklam atlama",
        "link kısaltıcı bypass",
    ],
    openGraph: {
        title: "Blog — Reklam Atlama Rehberleri | ReklamAtla",
        description:
            "OUO.io bypass, AyLink reklam atlama, kısa link çözme rehberleri.",
        type: "website",
    },
};

export default function BlogListPage() {
    return (
        <main className="min-h-screen bg-[#0a0a0f] text-white">
            {/* Header */}
            <header className="fixed top-0 w-full h-16 border-b z-[60] backdrop-blur-xl bg-[#0a0a0f]/80 border-white/5">
                <div className="max-w-6xl mx-auto h-full flex items-center justify-between px-4 md:px-8">
                    <Link href="/" className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center">
                            <Zap size={16} className="text-white" />
                        </div>
                        <span className="font-bold text-lg tracking-tight">
                            Reklam<span className="text-purple-500">Atla</span>
                        </span>
                    </Link>
                    <Link
                        href="/"
                        className="text-sm text-gray-400 hover:text-purple-400 transition-colors"
                    >
                        ← Ana Sayfa
                    </Link>
                </div>
            </header>

            {/* Hero */}
            <section className="pt-28 pb-10 px-4 text-center relative">
                <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[500px] h-[200px] bg-purple-600/10 blur-[100px] rounded-full pointer-events-none" />
                <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight mb-4 relative z-10">
                    Reklam Atlama{" "}
                    <span className="bg-gradient-to-r from-purple-400 to-fuchsia-500 bg-clip-text text-transparent">
                        Rehberleri
                    </span>
                </h1>
                <p className="text-gray-400 max-w-xl mx-auto text-base sm:text-lg">
                    Kısaltılmış linkler, güvenlik ipuçları ve bypass yöntemleri hakkında
                    kapsamlı Türkçe rehberler.
                </p>
            </section>

            {/* Blog Grid */}
            <section className="px-4 pb-20 max-w-5xl mx-auto">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {blogPosts.map((post) => (
                        <Link
                            key={post.slug}
                            href={`/blog/${post.slug}`}
                            className="group block p-6 rounded-2xl border bg-white/[0.02] border-white/5 hover:border-purple-500/20 hover:bg-white/[0.04] transition-all duration-300"
                        >
                            <div className="flex items-center gap-3 text-xs text-gray-500 mb-3">
                                <span className="flex items-center gap-1">
                                    <Calendar size={12} /> {post.date}
                                </span>
                                <span className="flex items-center gap-1">
                                    <Clock size={12} /> {post.readTime}
                                </span>
                            </div>

                            <h2 className="text-lg font-bold mb-2 group-hover:text-purple-400 transition-colors leading-snug">
                                {post.title}
                            </h2>

                            <p className="text-sm text-gray-500 leading-relaxed mb-4">
                                {post.excerpt}
                            </p>

                            <div className="flex flex-wrap gap-2 mb-4">
                                {post.keywords.slice(0, 3).map((kw) => (
                                    <span
                                        key={kw}
                                        className="px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded-md text-xs"
                                    >
                                        {kw}
                                    </span>
                                ))}
                            </div>

                            <span className="text-sm text-purple-500 font-medium flex items-center gap-1 group-hover:gap-2 transition-all">
                                Devamını Oku <ArrowRight size={14} />
                            </span>
                        </Link>
                    ))}
                </div>
            </section>

            {/* CTA */}
            <section className="px-4 pb-16 text-center">
                <div className="max-w-xl mx-auto p-8 rounded-2xl bg-gradient-to-r from-purple-500/[0.06] to-fuchsia-500/[0.06] border border-purple-500/10">
                    <h2 className="text-xl font-bold mb-3">
                        Hemen Linki Bypass Et
                    </h2>
                    <p className="text-gray-400 text-sm mb-5">
                        Kısaltılmış linkinizi yapıştırın, reklamları atlayın.
                    </p>
                    <Link
                        href="/"
                        className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-500 text-white font-medium rounded-xl transition-colors"
                    >
                        ReklamAtla&apos;ya Git <ArrowRight size={16} />
                    </Link>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-8 border-t border-white/5 text-center text-gray-600 text-xs">
                <p>&copy; 2026 ReklamAtla.com — Tüm hakları saklıdır.</p>
            </footer>
        </main>
    );
}
