import { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { blogPosts } from "../data";
import { ArrowLeft, Calendar, Clock, Zap, Shield, ArrowRight } from "lucide-react";

// --- Static Params for Build ---
export function generateStaticParams() {
    return blogPosts.map((post) => ({ slug: post.slug }));
}

// --- Dynamic SEO Metadata ---
export function generateMetadata({
    params,
}: {
    params: { slug: string };
}): Metadata {
    const post = blogPosts.find((p) => p.slug === params.slug);
    if (!post) return { title: "Bulunamadı" };

    return {
        title: post.metaTitle,
        description: post.metaDescription,
        keywords: post.keywords,
        openGraph: {
            title: post.metaTitle,
            description: post.metaDescription,
            type: "article",
            publishedTime: post.date,
        },
        twitter: {
            card: "summary_large_image",
            title: post.metaTitle,
            description: post.metaDescription,
        },
        alternates: {
            canonical: `/blog/${post.slug}`,
        },
    };
}

// --- Simple Markdown Renderer ---
function renderContent(content: string) {
    const lines = content.trim().split("\n");
    const elements: React.ReactNode[] = [];
    let inTable = false;
    let tableRows: string[][] = [];
    let tableHeader: string[] = [];
    let inList = false;
    let listItems: string[] = [];

    const parseInline = (text: string): React.ReactNode => {
        // Bold
        const parts = text.split(/(\*\*[^*]+\*\*)/g);
        return parts.map((part, i) => {
            if (part.startsWith("**") && part.endsWith("**")) {
                return (
                    <strong key={i} className="text-white font-semibold">
                        {part.slice(2, -2)}
                    </strong>
                );
            }
            // Links
            const linkParts = part.split(/(\[[^\]]+\]\([^)]+\))/g);
            return linkParts.map((lp, j) => {
                const linkMatch = lp.match(/\[([^\]]+)\]\(([^)]+)\)/);
                if (linkMatch) {
                    return (
                        <Link
                            key={`${i}-${j}`}
                            href={linkMatch[2]}
                            className="text-purple-400 hover:text-purple-300 underline underline-offset-2"
                        >
                            {linkMatch[1]}
                        </Link>
                    );
                }
                // Inline code
                const codeParts = lp.split(/(`.+?`)/g);
                return codeParts.map((cp, k) => {
                    if (cp.startsWith("`") && cp.endsWith("`")) {
                        return (
                            <code
                                key={`${i}-${j}-${k}`}
                                className="bg-white/5 px-1.5 py-0.5 rounded text-purple-300 text-sm"
                            >
                                {cp.slice(1, -1)}
                            </code>
                        );
                    }
                    return cp;
                });
            });
        });
    };

    const flushList = () => {
        if (inList && listItems.length > 0) {
            elements.push(
                <ul
                    key={`list-${elements.length}`}
                    className="space-y-2 my-4 pl-5 list-disc"
                >
                    {listItems.map((item, i) => (
                        <li key={i} className="text-gray-400 text-sm leading-relaxed">
                            {parseInline(item)}
                        </li>
                    ))}
                </ul>
            );
            listItems = [];
            inList = false;
        }
    };

    const flushTable = () => {
        if (inTable && tableRows.length > 0) {
            elements.push(
                <div
                    key={`table-${elements.length}`}
                    className="overflow-x-auto my-6 rounded-xl border border-white/5"
                >
                    <table className="w-full text-sm">
                        {tableHeader.length > 0 && (
                            <thead>
                                <tr className="bg-white/5">
                                    {tableHeader.map((h, i) => (
                                        <th
                                            key={i}
                                            className="px-4 py-3 text-left font-medium text-gray-300 border-b border-white/5"
                                        >
                                            {h}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                        )}
                        <tbody>
                            {tableRows.map((row, i) => (
                                <tr
                                    key={i}
                                    className="border-b border-white/5 last:border-0"
                                >
                                    {row.map((cell, j) => (
                                        <td key={j} className="px-4 py-3 text-gray-400">
                                            {parseInline(cell)}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            );
            tableRows = [];
            tableHeader = [];
            inTable = false;
        }
    };

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        // Table row
        if (line.trim().startsWith("|")) {
            flushList();
            const cells = line
                .split("|")
                .filter(Boolean)
                .map((c) => c.trim());
            if (
                cells.every((c) => /^[-:]+$/.test(c))
            ) {
                continue; // separator row
            }
            if (!inTable) {
                inTable = true;
                tableHeader = cells;
            } else {
                tableRows.push(cells);
            }
            continue;
        }
        if (inTable) flushTable();

        // Headings
        if (line.startsWith("## ")) {
            flushList();
            elements.push(
                <h2
                    key={i}
                    className="text-xl md:text-2xl font-bold mt-10 mb-4 text-white border-b border-white/5 pb-3"
                >
                    {line.slice(3)}
                </h2>
            );
            continue;
        }
        if (line.startsWith("### ")) {
            flushList();
            elements.push(
                <h3 key={i} className="text-lg font-bold mt-8 mb-3 text-gray-200">
                    {line.slice(4)}
                </h3>
            );
            continue;
        }

        // Horizontal rule
        if (line.trim() === "---") {
            flushList();
            elements.push(
                <hr key={i} className="my-8 border-white/5" />
            );
            continue;
        }

        // List items
        if (line.trim().startsWith("- ")) {
            inList = true;
            listItems.push(line.trim().slice(2));
            continue;
        }
        if (
            line.trim().match(/^\d+\.\s/)
        ) {
            inList = true;
            listItems.push(line.trim().replace(/^\d+\.\s/, ""));
            continue;
        }
        if (inList) flushList();

        // Empty line
        if (line.trim() === "") continue;

        // Paragraph
        elements.push(
            <p
                key={i}
                className="text-gray-400 text-sm sm:text-base leading-relaxed my-3"
            >
                {parseInline(line)}
            </p>
        );
    }

    flushList();
    flushTable();
    return elements;
}

// --- Article Page ---
export default function BlogArticlePage({
    params,
}: {
    params: { slug: string };
}) {
    const post = blogPosts.find((p) => p.slug === params.slug);
    if (!post) return notFound();

    const otherPosts = blogPosts
        .filter((p) => p.slug !== post.slug)
        .slice(0, 3);

    // JSON-LD Structured Data
    const jsonLd = {
        "@context": "https://schema.org",
        "@type": "Article",
        headline: post.title,
        description: post.metaDescription,
        datePublished: post.date,
        author: {
            "@type": "Organization",
            name: "ReklamAtla",
        },
        publisher: {
            "@type": "Organization",
            name: "ReklamAtla",
        },
        keywords: post.keywords.join(", "),
    };

    return (
        <main className="min-h-screen bg-[#0a0a0f] text-white">
            {/* JSON-LD */}
            <script
                type="application/ld+json"
                dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
            />

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
                        href="/blog"
                        className="text-sm text-gray-400 hover:text-purple-400 transition-colors flex items-center gap-1"
                    >
                        <ArrowLeft size={14} /> Blog
                    </Link>
                </div>
            </header>

            {/* Article */}
            <article className="pt-24 pb-16 px-4 max-w-3xl mx-auto">
                {/* Meta info */}
                <div className="flex items-center gap-4 text-xs text-gray-500 mb-4">
                    <span className="flex items-center gap-1">
                        <Calendar size={12} /> {post.date}
                    </span>
                    <span className="flex items-center gap-1">
                        <Clock size={12} /> {post.readTime}
                    </span>
                </div>

                {/* Title */}
                <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold leading-tight mb-6">
                    {post.title}
                </h1>

                {/* Keywords */}
                <div className="flex flex-wrap gap-2 mb-8">
                    {post.keywords.map((kw) => (
                        <span
                            key={kw}
                            className="px-2.5 py-1 bg-purple-500/10 text-purple-400 rounded-lg text-xs font-medium"
                        >
                            {kw}
                        </span>
                    ))}
                </div>

                {/* Content */}
                <div className="prose-custom">{renderContent(post.content)}</div>

                {/* CTA Box */}
                <div className="mt-12 p-6 rounded-2xl bg-gradient-to-r from-purple-500/[0.06] to-fuchsia-500/[0.06] border border-purple-500/10 text-center">
                    <div className="flex justify-center mb-3">
                        <Shield size={32} className="text-purple-400" />
                    </div>
                    <h3 className="font-bold text-lg mb-2">
                        Hemen Bypass Et!
                    </h3>
                    <p className="text-gray-400 text-sm mb-4">
                        Kısaltılmış linkinizi yapıştırın, reklamları atlayın, güvenle
                        hedefe ulaşın.
                    </p>
                    <Link
                        href="/"
                        className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-500 text-white font-medium rounded-xl transition-colors"
                    >
                        ReklamAtla&apos;ya Git <ArrowRight size={16} />
                    </Link>
                </div>
            </article>

            {/* Related Articles */}
            {otherPosts.length > 0 && (
                <section className="px-4 pb-16 max-w-3xl mx-auto">
                    <h2 className="text-xl font-bold mb-6 text-gray-300">
                        Diğer Yazılar
                    </h2>
                    <div className="grid gap-4">
                        {otherPosts.map((op) => (
                            <Link
                                key={op.slug}
                                href={`/blog/${op.slug}`}
                                className="block p-5 rounded-xl border border-white/5 hover:border-purple-500/20 bg-white/[0.02] hover:bg-white/[0.04] transition-all"
                            >
                                <h3 className="font-bold text-sm mb-1 hover:text-purple-400 transition-colors">
                                    {op.title}
                                </h3>
                                <p className="text-xs text-gray-500">{op.excerpt}</p>
                            </Link>
                        ))}
                    </div>
                </section>
            )}

            {/* Footer */}
            <footer className="py-8 border-t border-white/5 text-center text-gray-600 text-xs">
                <p>&copy; 2026 ReklamAtla.com — Tüm hakları saklıdır.</p>
            </footer>
        </main>
    );
}
