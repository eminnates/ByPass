"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState, useRef } from "react";

const API_BASE = "/api";

/**
 * Share Target Sayfası
 * 
 * Kullanıcı mobilde bir link paylaşırsa (Paylaş → ReklamAtla),
 * bu sayfa otomatik olarak link'i bypass edip hedefe yönlendirir.
 * Hiçbir input girilmesine gerek yok.
 */
function ShareContent() {
    const searchParams = useSearchParams();
    const [status, setStatus] = useState("init");
    const [message, setMessage] = useState("Link analiz ediliyor...");
    const [resolvedUrl, setResolvedUrl] = useState("");
    const [error, setError] = useState("");
    const hasStarted = useRef(false);

    useEffect(() => {
        if (hasStarted.current) return;
        hasStarted.current = true;

        // Share Target'tan gelen parametreleri al
        const sharedUrl = searchParams.get("url");
        const sharedText = searchParams.get("text");
        const sharedTitle = searchParams.get("title");

        // URL'yi çıkar (bazen text parametresinde gelir)
        const url = extractUrl(sharedUrl || sharedText || sharedTitle || "");

        if (!url) {
            setError("Geçerli bir link bulunamadı.");
            setStatus("error");
            return;
        }

        // Otomatik bypass başlat
        startBypass(url);
    }, [searchParams]);

    function extractUrl(text: string): string | null {
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        const match = text.match(urlRegex);
        return match ? match[0] : null;
    }

    async function startBypass(url: string) {
        setStatus("bypassing");
        setMessage("⚡ Bypass uygulanıyor...");

        try {
            const resp = await fetch(`${API_BASE}/bypass`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url }),
            });

            const data = await resp.json();

            // Anında sonuç (cache)
            if (data.status === "success" && data.resolved_url) {
                setMessage("✅ Yönlendiriliyor...");
                setStatus("redirecting");
                setResolvedUrl(data.resolved_url);
                window.location.href = data.resolved_url;
                return;
            }

            // Kuyrukta — polling başlat
            if (data.id) {
                setMessage("🔍 Link çözülüyor...");
                pollResult(data.id);
            } else {
                setError("Beklenmeyen yanıt.");
                setStatus("error");
            }
        } catch {
            setError("Sunucuya bağlanılamadı.");
            setStatus("error");
        }
    }

    async function pollResult(id: number) {
        const MAX = 60;
        for (let i = 0; i < MAX; i++) {
            await new Promise((r) => setTimeout(r, 2000));

            try {
                const resp = await fetch(`${API_BASE}/status/${id}`);
                const data = await resp.json();

                if (data.status === "success" && data.resolved_url) {
                    setMessage("✅ Yönlendiriliyor...");
                    setStatus("redirecting");
                    setResolvedUrl(data.resolved_url);
                    window.location.href = data.resolved_url;
                    return;
                }

                if (data.status === "failed") {
                    const reasons: Record<string, string> = {
                        link_not_found: "Link bulunamadı (404).",
                        timeout: "İşlem zaman aşımına uğradı.",
                    };
                    setError(reasons[data.fail_reason] || "Bypass başarısız.");
                    setStatus("error");
                    return;
                }

                // Kuyruk pozisyonu
                if (data.queue_position && data.queue_position > 0) {
                    setMessage(`⏳ Kuyrukta: ${data.queue_position}. sıra`);
                } else {
                    setMessage("⚡ Bypass uygulanıyor...");
                }
            } catch {
                setError("Bağlantı koptu.");
                setStatus("error");
                return;
            }
        }

        setError("İşlem zaman aşımına uğradı.");
        setStatus("error");
    }

    return (
        <main className="min-h-screen flex flex-col items-center justify-center bg-[#0f0f11] text-white px-6">
            <div className="max-w-md w-full text-center space-y-8">
                {/* Logo */}
                <div>
                    <h1 className="text-3xl font-extrabold italic">
                        <span className="text-purple-500">ReklamAtla</span>
                    </h1>
                </div>

                {/* Durum Animasyonu */}
                {status !== "error" && (
                    <div className="space-y-6">
                        {/* Spinner */}
                        <div className="flex justify-center">
                            <div className="relative">
                                <div className="w-16 h-16 border-4 border-purple-500/20 rounded-full" />
                                <div className="absolute top-0 w-16 h-16 border-4 border-transparent border-t-purple-500 rounded-full animate-spin" />
                                {status === "redirecting" && (
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <span className="text-xl">✓</span>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Mesaj */}
                        <p className="text-gray-400 text-lg animate-pulse">{message}</p>

                        {/* Progress bar */}
                        <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-purple-600 to-purple-400 rounded-full transition-all duration-1000"
                                style={{
                                    width:
                                        status === "init" ? "10%" :
                                            status === "bypassing" ? "50%" :
                                                status === "redirecting" ? "100%" : "30%",
                                }}
                            />
                        </div>
                    </div>
                )}

                {/* Hata Durumu */}
                {status === "error" && (
                    <div className="space-y-6">
                        <div className="w-16 h-16 mx-auto rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center">
                            <span className="text-2xl">✕</span>
                        </div>
                        <p className="text-red-400 font-medium">{error}</p>
                        <div className="flex gap-3 justify-center">
                            <button
                                onClick={() => window.location.reload()}
                                className="px-6 py-3 bg-purple-600 hover:bg-purple-500 rounded-xl font-medium transition-colors"
                            >
                                Tekrar Dene
                            </button>
                            <a
                                href="/"
                                className="px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl font-medium transition-colors"
                            >
                                Ana Sayfa
                            </a>
                        </div>
                    </div>
                )}

                {/* Manuel link (yönlendirme çalışmazsa) */}
                {resolvedUrl && (
                    <a
                        href={resolvedUrl}
                        className="inline-flex items-center gap-2 text-purple-400 hover:text-purple-300 text-sm underline transition-colors"
                    >
                        Otomatik yönlendirme çalışmazsa tıklayın →
                    </a>
                )}
            </div>
        </main>
    );
}

export default function SharePage() {
    return (
        <Suspense
            fallback={
                <main className="min-h-screen flex items-center justify-center bg-[#0f0f11] text-white">
                    <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full" />
                </main>
            }
        >
            <ShareContent />
        </Suspense>
    );
}
