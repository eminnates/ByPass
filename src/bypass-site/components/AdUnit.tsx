"use client";

import { useEffect, useRef } from 'react';

// #region agent log
const log = (location: string, message: string, data: any, hypothesisId: string) => {
    fetch('http://127.0.0.1:7243/ingest/362f5994-0160-415c-b13f-4aa330764abd', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            location,
            message,
            data,
            timestamp: Date.now(),
            sessionId: 'debug-session',
            runId: 'run1',
            hypothesisId
        })
    }).catch(() => { });
};
// #endregion

interface AdUnitProps {
    client: string;
    slot: string;
    format?: 'auto' | 'fluid' | 'rectangle';
    responsive?: string;
    style?: React.CSSProperties;
}

const AdUnit = ({ client, slot, format = 'auto', responsive = 'true', style }: AdUnitProps) => {
    // #region agent log
    const adRef = useRef<HTMLModElement>(null);
    // #endregion
    const isLoaded = useRef(false); // Reklamın tekrar tekrar yüklenmesini önler

    useEffect(() => {
        // #region agent log
        log('AdUnit.tsx:useEffect', 'AdUnit useEffect triggered', { hasRef: !!adRef.current, isLoaded: isLoaded.current }, 'C');
        // #endregion
        // Sadece reklam alanı görünürse ve daha önce yüklenmediyse çalıştır
        if (adRef.current && !isLoaded.current) {
            // #region agent log
            const width = adRef.current.offsetWidth;
            const height = adRef.current.offsetHeight;
            log('AdUnit.tsx:useEffect', 'AdUnit dimensions check', { width, height, willLoad: !(width === 0 && height === 0) }, 'C');
            // #endregion
            // Eğer genişlik 0 ise yüklemeye çalışma (Hatayı önler)
            if (adRef.current.offsetWidth === 0 && adRef.current.offsetHeight === 0) {
                return;
            }

            try {
                (window.adsbygoogle = window.adsbygoogle || []).push({});
                isLoaded.current = true;
                // #region agent log
                log('AdUnit.tsx:useEffect', 'AdSense push successful', { client, slot }, 'C');
                // #endregion
            } catch (e) {
                // #region agent log
                log('AdUnit.tsx:useEffect', 'AdSense error', { error: String(e) }, 'C');
                // #endregion
                console.error("AdSense hatası:", e);
            }
        }
    }, []);

    return (
        <div style={{ width: '100%', height: '100%', minWidth: '200px', ...style }}>
            <ins
                ref={adRef}
                className="adsbygoogle"
                style={{ display: 'block', width: '100%', height: '100%' }}
                data-ad-client={client}
                data-ad-slot={slot}
                data-ad-format={format}
                data-full-width-responsive={responsive}
            />
        </div>
    );
};

export default AdUnit;