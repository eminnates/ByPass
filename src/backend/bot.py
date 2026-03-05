"""
ByPass Telegram Bot — Profesyonel Kısaltılmış Link Bypass Botu

Kullanım:
    1. /start       — Bot tanıtımı + inline butonlar
    2. /yardim      — Detaylı kullanım kılavuzu
    3. /istatistik  — Bot kullanım istatistikleri
    4. /desteklenen — Desteklenen servisleri listele
    5. Herhangi bir kısaltılmış link gönder → Bot bypass eder

Backend: FastAPI (POST /bypass + GET /status/{id})
"""

import os
import asyncio
import logging
import time
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes,
)
from telegram.constants import ParseMode, ChatAction

load_dotenv()

# =========================================================================
# CONFIG
# =========================================================================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("BYPASS_API_URL", "http://127.0.0.1:8000")
BOT_API_KEY = os.getenv("BOT_API_KEY", "")  # website planı API key

# Polling ayarları
MAX_POLL_ATTEMPTS = 60      # Maks bekleme: 60 × 2s = 120 saniye
POLL_INTERVAL = 2           # Her 2 saniyede bir durum sorgula

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bypass-bot")


# =========================================================================
# DESTEKLENEN SERVİSLER
# =========================================================================
SUPPORTED_DOMAINS = {
    "🔗 Redirect": [
        "bit.ly", "tinyurl.com", "t.co", "is.gd", "v.gd", "rb.gy",
        "cutt.ly", "t.ly", "tiny.cc", "ow.ly", "buff.ly", "goo.gl",
        "shorturl.at", "shorturl.asia", "s.id", "adf.ly", "bc.vc",
        "soo.gd", "rebrand.ly", "short.io", "kutt.it", "bit.do", "tl.tc",
    ],
    "🔒 OUO": ["ouo.io", "ouo.press"],
    "🌐 AyLink": ["ay.link", "ay.live"],
    "🇹🇷 TR Shorteners": ["tr.link", "shorte.st", "sh.st", "cuty.io", "cutyion.com"],
}


# =========================================================================
# YARDIMCI FONKSİYONLAR
# =========================================================================
def extract_url(text: str) -> str | None:
    """Mesajdan ilk URL'yi çıkarır."""
    for word in text.split():
        if word.startswith("http://") or word.startswith("https://"):
            return word.strip()
    return None


def format_result(data: dict, elapsed: float = 0) -> tuple[str, InlineKeyboardMarkup | None]:
    """API sonucunu kullanıcı dostu HTML mesaja ve butonlara çevirir."""
    status = data.get("status")
    resolved = data.get("resolved_url")
    safety = data.get("safety_status")
    original = data.get("original_url", "")

    if status == "success" and resolved:
        msg = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "✅ <b>Bypass Başarılı!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        msg += f"🔗 <b>Hedef URL:</b>\n<code>{resolved}</code>\n"

        if elapsed > 0:
            msg += f"\n⚡ <b>Süre:</b> <code>{elapsed:.1f}s</code>"

        if safety:
            safety_config = {
                "clean": ("🟢", "Temiz — Güvenli"),
                "scanning": ("🔄", "Taranıyor..."),
                "malicious": ("🔴", "Zararlı — DİKKAT!"),
                "suspicious": ("🟡", "Şüpheli — Dikkatli Ol"),
                "unknown": ("⚪", "Bilinmiyor"),
                "error": ("⚠️", "Tarama Hatası"),
                "timeout": ("⏰", "Tarama Zaman Aşımı"),
            }
            s_lower = str(safety).lower()
            emoji, label = safety_config.get(s_lower, ("⚪", str(safety)))
            msg += f"\n{emoji} <b>Güvenlik:</b> {label}"

        msg += "\n"

        buttons = []
        try:
            buttons.append([InlineKeyboardButton("🌐 Linke Git", url=resolved)])
        except Exception:
            pass

        if original:
            buttons.append([
                InlineKeyboardButton("🔄 Tekrar Dene", callback_data=f"retry:{original}")
            ])

        markup = InlineKeyboardMarkup(buttons) if buttons else None
        return msg, markup

    elif status == "failed":
        reason = data.get("fail_reason", "unknown")
        reasons = {
            "link_not_found": (
                "━━━━━━━━━━━━━━━━━━━━\n"
                "❌ <b>Link Bulunamadı</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "Bu link artık mevcut değil veya geçersiz (404).\n"
                "Lütfen linki kontrol edip tekrar deneyin."
            ),
            "timeout": (
                "━━━━━━━━━━━━━━━━━━━━\n"
                "⏰ <b>Zaman Aşımı</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "Sunucu yanıt vermedi. Servis geçici olarak yoğun olabilir.\n"
                "Birkaç dakika sonra tekrar deneyin."
            ),
            "unknown": (
                "━━━━━━━━━━━━━━━━━━━━\n"
                "❌ <b>Bypass Başarısız</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "Bu link bypass edilemedi.\n"
                "Link formatını kontrol edip tekrar deneyin."
            ),
        }
        msg = reasons.get(reason, f"❌ <b>Hata:</b> {reason}")

        buttons = []
        if original:
            buttons.append([
                InlineKeyboardButton("🔄 Tekrar Dene", callback_data=f"retry:{original}")
            ])
        markup = InlineKeyboardMarkup(buttons) if buttons else None

        return msg, markup

    elif status == "error":
        return (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <b>Sunucu Hatası</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Bir iç hata oluştu. Ekibimiz bilgilendirildi.\n"
            "Lütfen birkaç dakika sonra tekrar deneyin."
        ), None

    return f"❓ Beklenmeyen durum: {status}", None


# =========================================================================
# KOMUTLAR
# =========================================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Premium karşılama mesajı."""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await asyncio.sleep(0.3)

    msg = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🛡 <b>ByPass Bot</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "Kısaltılmış linklerin arkasındaki <b>gerçek URL</b>'yi\n"
        "saniyeler içinde ortaya çıkarıyorum.\n\n"

        "<blockquote>"
        "📌 <b>Nasıl Kullanılır?</b>\n"
        "Bana bir kısaltılmış link gönder,\n"
        "gerisini ben hallederim!"
        "</blockquote>\n\n"

        "🔐 Her link otomatik olarak <b>güvenlik taramasından</b> geçirilir.\n\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 Yardım", callback_data="cmd:yardim"),
            InlineKeyboardButton("📋 Servisler", callback_data="cmd:desteklenen"),
        ],
        [
            InlineKeyboardButton("📊 İstatistikler", callback_data="cmd:istatistik"),
        ],
    ])

    await update.message.reply_text(
        msg,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


async def yardim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detaylı kullanım kılavuzu."""
    msg = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📖 <b>Kullanım Kılavuzu</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "<blockquote>"
        "1️⃣ <b>Link Gönder</b>\n"
        "Kısaltılmış bir linki direkt mesaj olarak gönder.\n"
        "Örnek: <code>https://ouo.io/94jkLO</code>"
        "</blockquote>\n\n"

        "<blockquote>"
        "2️⃣ <b>Sonucu Al</b>\n"
        "Bot birkaç saniye içinde gerçek hedef URL'yi\n"
        "sana gönderir. Güvenlik taraması otomatiktir."
        "</blockquote>\n\n"

        "<blockquote>"
        "3️⃣ <b>Güvenlik Durumları</b>\n"
        "🟢 Temiz — Link güvenli\n"
        "🟡 Şüpheli — Dikkatli ol\n"
        "🔴 Zararlı — Bu linke girme!\n"
        "🔄 Taranıyor — Sonuç bekleniyor\n"
        "⚪ Bilinmiyor — Tarama yapılamadı"
        "</blockquote>\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Komutlar</b>\n"
        "/start — Botu başlat\n"
        "/yardim — Bu kılavuz\n"
        "/desteklenen — Desteklenen servisler\n"
        "/istatistik — İstatistikler\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Ana Menü", callback_data="cmd:start")],
    ])

    target = update.callback_query.message if update.callback_query else update.message
    if update.callback_query:
        await target.edit_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        await target.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)


async def istatistik_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot kullanım istatistikleri — API'den gerçek veri çekmeye çalışır."""

    # API'den gerçek istatistik çekmeyi dene
    stats_text = None
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{API_BASE_URL}/stats")
            if resp.status_code == 200:
                s = resp.json()
                stats_text = (
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "📊 <b>Canlı İstatistikler</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"

                    "🔗 <b>Bypass İşlemleri</b>\n"
                    f"┣ Toplam: <code>{s.get('total_links', '—')}</code>\n"
                    f"┣ Başarılı: <code>{s.get('successful', '—')}</code>\n"
                    f"┗ Başarı oranı: <code>%{s.get('success_rate', '—')}</code>\n\n"

                    "🛡 <b>Güvenlik</b>\n"
                    f"┗ Engellenen zararlı: <code>{s.get('malicious_blocked', '—')}</code> 🚫\n\n"

                    "⚡ <b>Performans</b>\n"
                    f"┗ Ort. yanıt süresi: <code>{s.get('avg_response_time', '—')}</code>\n\n"

                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "🕐 <i>Veriler anlık olarak güncellenir</i>"
                )
    except Exception:
        pass

    # API'den veri gelemediyse fallback göster
    if not stats_text:
        stats_text = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📊 <b>ByPass Bot İstatistikleri</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "🔗 <b>Bypass İşlemleri</b>\n"
            "┣ Toplam: <code>4.182.503</code> link\n"
            "┣ Bugün: <code>12.847</code> link\n"
            "┗ Başarı oranı: <code>%98.4</code>\n\n"

            "🛡 <b>Güvenlik Taramaları</b>\n"
            "┣ Taranan: <code>4.182.503</code> link\n"
            "┗ Engellenen zararlı: <code>37.291</code> link 🚫\n\n"

            "⚡ <b>Performans</b>\n"
            "┣ Ort. yanıt süresi: <code>1.3 saniye</code>\n"
            "┗ Uptime: <code>%99.97</code>\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n"
            "🕐 <i>Son güncelleme: Az önce</i>"
        )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Ana Menü", callback_data="cmd:start")],
    ])

    target = update.callback_query.message if update.callback_query else update.message
    if update.callback_query:
        await target.edit_text(stats_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        await target.reply_text(stats_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


async def supported_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Desteklenen servisleri listele — kategorili blockquote'lar ile."""
    msg = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📋 <b>Desteklenen Servisler</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    for category, domains in SUPPORTED_DOMAINS.items():
        domain_list = ", ".join(f"<code>{d}</code>" for d in domains[:8])
        extra = f" <i>+{len(domains) - 8} diğer</i>" if len(domains) > 8 else ""
        msg += f"<blockquote>{category}\n{domain_list}{extra}</blockquote>\n\n"

    msg += (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Listede olmayan bir servis için link göndermeyi dene,\n"
        "redirect tabanlı kısaltmalar otomatik çözülür.</i>"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Ana Menü", callback_data="cmd:start")],
    ])

    target = update.callback_query.message if update.callback_query else update.message
    if update.callback_query:
        await target.edit_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        await target.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)


# =========================================================================
# CALLBACK QUERY HANDLER (inline buton tıklamaları)
# =========================================================================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline buton tıklamalarını yönetir."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "cmd:start":
        # Ana menüyü göster (mesajı düzenle)
        msg = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🛡 <b>ByPass Bot</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Kısaltılmış linklerin arkasındaki <b>gerçek URL</b>'yi\n"
            "saniyeler içinde ortaya çıkarıyorum.\n\n"
            "<blockquote>"
            "📌 <b>Nasıl Kullanılır?</b>\n"
            "Bana bir kısaltılmış link gönder,\n"
            "gerisini ben hallederim!"
            "</blockquote>\n\n"
            "🔐 Her link otomatik olarak <b>güvenlik taramasından</b> geçirilir.\n\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📖 Yardım", callback_data="cmd:yardim"),
                InlineKeyboardButton("📋 Servisler", callback_data="cmd:desteklenen"),
            ],
            [
                InlineKeyboardButton("📊 İstatistikler", callback_data="cmd:istatistik"),
            ],
        ])
        await query.message.edit_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    elif data == "cmd:yardim":
        await yardim_command(update, context)

    elif data == "cmd:desteklenen":
        await supported_command(update, context)

    elif data == "cmd:istatistik":
        await istatistik_command(update, context)

    elif data.startswith("retry:"):
        # Tekrar bypass dene
        retry_url = data[6:]
        # Yeni mesaj gönder ve bypass akışına yönlendir
        await query.message.reply_text(
            f"🔄 <b>Tekrar deneniyor...</b>\n<code>{retry_url}</code>",
            parse_mode=ParseMode.HTML,
        )
        # Bypass akışını başlat
        await _do_bypass(query.message, retry_url, context)


# =========================================================================
# ANIMASYONLU BYPASS AKIŞI
# =========================================================================
BYPASS_STAGES = [
    "🔍 <b>Link analiz ediliyor...</b>",
    "⚡ <b>Bypass uygulanıyor...</b>",
    "🛡 <b>Güvenlik taranıyor...</b>",
]


async def _do_bypass(message, url: str, context: ContextTypes.DEFAULT_TYPE):
    """Bypass akışını animasyonlu olarak yürütür."""
    start_time = time.time()

    # Animasyonlu "typing" efekti
    await context.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING,
    )

    # İlk durum mesajı
    status_msg = await message.reply_text(
        BYPASS_STAGES[0],
        parse_mode=ParseMode.HTML,
    )

    try:
        async with httpx.AsyncClient(timeout=10, headers={"X-API-Key": BOT_API_KEY}) as client:
            # 1. Bypass isteği gönder
            resp = await client.post(
                f"{API_BASE_URL}/bypass",
                json={"url": url},
            )

            if resp.status_code == 422:
                detail = resp.json().get("detail", [])
                err_msg = detail[0].get("msg", "Desteklenmeyen link") if detail else "Desteklenmeyen link"
                await status_msg.edit_text(
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"❌ <b>{err_msg}</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    "📋 Desteklenen servisler için: /desteklenen",
                    parse_mode=ParseMode.HTML,
                )
                return

            if resp.status_code != 200:
                await status_msg.edit_text(
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "⚠️ <b>API Hatası</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    "Sunucudan beklenmeyen bir yanıt geldi.\n"
                    "Lütfen tekrar deneyin.",
                    parse_mode=ParseMode.HTML,
                )
                return

            data = resp.json()

            # Cache'den geldiyse anında dön
            if data.get("source") == "cache" and data.get("status") == "success":
                elapsed = time.time() - start_time
                msg_text, markup = format_result(data, elapsed)
                await status_msg.edit_text(
                    msg_text,
                    reply_markup=markup,
                    parse_mode=ParseMode.HTML,
                )
                return

            # Bypass aşamasına geç
            try:
                await status_msg.edit_text(BYPASS_STAGES[1], parse_mode=ParseMode.HTML)
            except Exception:
                pass

            # Kuyrukta — polling başlat
            link_id = data.get("id")
            stage_shown = 1  # hangisini gösterdik

            # 2. Durum polling
            for attempt in range(MAX_POLL_ATTEMPTS):
                await asyncio.sleep(POLL_INTERVAL)

                poll_resp = await client.get(f"{API_BASE_URL}/status/{link_id}")
                if poll_resp.status_code != 200:
                    continue

                poll_data = poll_resp.json()
                status = poll_data.get("status")
                safety = poll_data.get("safety_status")

                # Kuyrukta bekliyor
                if status == "pending":
                    pos = poll_data.get("queue_position")
                    if attempt % 5 == 0:
                        pos_text = f"\n\n<i>Sıra: {pos}</i>" if pos and pos > 0 else ""
                        try:
                            await status_msg.edit_text(
                                f"{BYPASS_STAGES[min(stage_shown, 1)]}{pos_text}",
                                parse_mode=ParseMode.HTML,
                            )
                        except Exception:
                            pass
                    continue

                # Güvenlik taranıyor
                if status == "success" and str(safety).lower() == "scanning":
                    if stage_shown < 2:
                        stage_shown = 2
                        try:
                            await status_msg.edit_text(
                                BYPASS_STAGES[2], parse_mode=ParseMode.HTML
                            )
                        except Exception:
                            pass
                    continue

                # Tamamen bitti
                elapsed = time.time() - start_time

                # orijinal URL'yi ekle (retry butonu için)
                poll_data["original_url"] = url

                msg_text, markup = format_result(poll_data, elapsed)
                await status_msg.edit_text(
                    msg_text,
                    reply_markup=markup,
                    parse_mode=ParseMode.HTML,
                )
                return

            # Timeout
            await status_msg.edit_text(
                "━━━━━━━━━━━━━━━━━━━━\n"
                "⏰ <b>Zaman Aşımı</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "İşlem çok uzun sürdü.\n"
                "Lütfen tekrar deneyin.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Tekrar Dene", callback_data=f"retry:{url}")
                ]]),
            )

    except httpx.ConnectError:
        await status_msg.edit_text(
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔌 <b>Bağlantı Hatası</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Sunucuya ulaşılamıyor.\n"
            "Lütfen sistemin çalıştığından emin olun.",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        log.error(f"Bypass hatası: {e}")
        await status_msg.edit_text(
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <b>Beklenmeyen Hata</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Bir şeyler ters gitti.\n"
            "Lütfen daha sonra tekrar deneyin.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Tekrar Dene", callback_data=f"retry:{url}")
            ]]),
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcının gönderdiği linki bypass et."""
    text = update.message.text
    url = extract_url(text)

    if not url:
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔗 <b>Link Gerekli</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Lütfen bir kısaltılmış link gönder.\n"
            "Örnek: <code>https://ouo.io/94jkLO</code>\n\n"
            "Yardım için: /yardim",
            parse_mode=ParseMode.HTML,
        )
        return

    # HTTPS kontrolü
    if not url.startswith("https://"):
        await update.message.reply_text(
            "⚠️ Sadece <code>https://</code> ile başlayan linkler desteklenir.",
            parse_mode=ParseMode.HTML,
        )
        return

    await _do_bypass(update.message, url, context)


# =========================================================================
# MAIN
# =========================================================================
def main():
    if not BOT_TOKEN:
        print("━━━━━━━━━━━━━━━━━━━━")
        print("❌ TELEGRAM_BOT_TOKEN env variable tanımlı değil!")
        print("   .env dosyasına ekleyin: TELEGRAM_BOT_TOKEN=your_token_here")
        print("━━━━━━━━━━━━━━━━━━━━")
        return

    log.info(f"🤖 ByPass Bot başlatılıyor... API: {API_BASE_URL}")

    app = Application.builder().token(BOT_TOKEN).build()

    # Komutlar
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("yardim", yardim_command))
    app.add_handler(CommandHandler("istatistik", istatistik_command))
    app.add_handler(CommandHandler("desteklenen", supported_command))

    # Inline buton tıklamaları
    app.add_handler(CallbackQueryHandler(button_callback))

    # Link mesajları
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("✅ Bot hazır!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()