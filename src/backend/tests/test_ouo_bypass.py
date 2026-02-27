"""
OUO Bypass Test - Zincirleme (recursive) destekli
ouo domain'i çıkmaya devam ettiği sürece bypass'ı tekrarlıyor.
"""
import re
import time
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import urllib.request

OUO_DOMAINS = {"ouo.io", "ouo.press"}


def RecaptchaV3():
    ANCHOR_URL = 'https://www.google.com/recaptcha/api2/anchor?ar=1&k=6Lcr1ncUAAAAAH3cghg6cOTPGARa8adOf-y9zv2x&co=aHR0cHM6Ly9vdW8ucHJlc3M6NDQz&hl=en&v=pCoGBhjs9s8EhFOHJFe8cqis&size=invisible&cb=ahgyd1gkfkhe'
    url_base = 'https://www.google.com/recaptcha/'
    post_data = "v={}&reason=q&c={}&k={}&co={}"

    matches = re.findall(r'([api2|enterprise]+)/anchor\?(.*)', ANCHOR_URL)[0]
    url_base += matches[0] + '/'
    params_str = matches[1]

    anchor_url = url_base + 'anchor?' + params_str
    req = urllib.request.Request(anchor_url)
    with urllib.request.urlopen(req) as resp:
        anchor_html = resp.read().decode()

    token = re.findall(r'"recaptcha-token" value="(.*?)"', anchor_html)[0]
    params = dict(pair.split('=') for pair in params_str.split('&'))
    post_data = post_data.format(params["v"], token, params["k"], params["co"])

    reload_url = url_base + 'reload?k=' + params["k"]
    req = urllib.request.Request(reload_url, data=post_data.encode(),
                                headers={'content-type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req) as resp:
        reload_html = resp.read().decode()

    answer = re.findall(r'"rresp","(.*?)"', reload_html)[0]
    return answer


def is_ouo(url):
    """URL'nin ouo domain'i olup olmadığını kontrol eder."""
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
        return domain in OUO_DOMAINS
    except:
        return False


def ouo_bypass_single(client, url):
    """Tek bir ouo linkini bypass eder. Sonuç URL'yi döner."""
    # ouo.press kullan (Cloudflare daha yumuşak)
    work_url = url.replace("ouo.io", "ouo.press")
    p = urlparse(work_url)
    id_val = work_url.split('/')[-1]
    next_url = f"{p.scheme}://{p.hostname}/go/{id_val}"

    res = client.get(work_url, impersonate="chrome124")

    if res.status_code != 200:
        print(f"      ⚠️  HTTP {res.status_code}")
        return None

    has_form = '<form' in res.text.lower()
    if not has_form:
        print(f"      ⚠️  Form bulunamadı (Cloudflare?)")
        return None

    for step in range(2):
        if res.headers.get('Location'):
            return res.headers.get('Location')

        soup = BeautifulSoup(res.content, 'lxml')
        form = soup.find('form')
        if not form:
            print(f"      ⚠️  Adım {step+1}: form yok")
            return None

        inputs = form.find_all("input", {"name": re.compile(r"token$")})
        data = {inp.get('name'): inp.get('value') for inp in inputs}
        data['x-token'] = RecaptchaV3()

        h = {'content-type': 'application/x-www-form-urlencoded'}
        res = client.post(next_url, data=data, headers=h,
                          allow_redirects=False, impersonate="chrome124")
        next_url = f"{p.scheme}://{p.hostname}/xreallcygo/{id_val}"

    return res.headers.get('Location')


def ouo_bypass_recursive(url, max_depth=10):
    """
    ouo linkini bypass eder. Sonuç yine ouo ise, tekrar bypass eder.
    max_depth ile sonsuz döngüyü engeller.
    """
    client = requests.Session()
    client.headers.update({
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'cache-control': 'max-age=0',
        'referer': 'http://www.google.com/ig/adde?moduleurl=',
        'upgrade-insecure-requests': '1',
    })

    current_url = url
    chain = [url]
    total_start = time.time()

    for depth in range(1, max_depth + 1):
        step_start = time.time()
        print(f"   🔗 [{depth}] Bypass: {current_url}")

        result = ouo_bypass_single(client, current_url)
        step_time = time.time() - step_start

        if not result:
            print(f"      ❌ Bypass başarısız ({step_time:.2f}s)")
            return {
                'original_url': url,
                'final_url': None,
                'chain': chain,
                'depth': depth,
                'error': 'Bypass başarısız',
                'total_time': time.time() - total_start
            }

        chain.append(result)
        print(f"      ✅ -> {result} ({step_time:.2f}s)")

        if is_ouo(result):
            print(f"      🔄 Sonuç yine ouo! Tekrar bypass ediliyor...")
            current_url = result
        else:
            total_time = time.time() - total_start
            print(f"\n   🎯 Final URL'ye ulaşıldı! (toplam {total_time:.2f}s, {depth} adım)")
            return {
                'original_url': url,
                'final_url': result,
                'chain': chain,
                'depth': depth,
                'total_time': total_time
            }

    total_time = time.time() - total_start
    print(f"\n   ⚠️  Max derinliğe ulaşıldı ({max_depth})")
    return {
        'original_url': url,
        'final_url': chain[-1],
        'chain': chain,
        'depth': max_depth,
        'total_time': total_time,
        'warning': 'Max derinliğe ulaşıldı'
    }


# --- TEST ---
if __name__ == "__main__":
    test_urls = [
        "https://ouo.io/94jkLO",      # Zincirleme link (ouo -> ouo -> ?)
        "https://ouo.press/Zu7Vs5",    # Tekli link (ouo -> google)
    ]

    print("=" * 70)
    print("OUO BYPASS - ZİNCİRLEME (RECURSİVE) TEST")
    print("=" * 70)

    for url in test_urls:
        print(f"\n{'─'*70}")
        print(f"🔗 Test: {url}")
        print(f"{'─'*70}")

        try:
            result = ouo_bypass_recursive(url)
            print(f"\n   📋 Sonuç:")
            print(f"      Orijinal:   {result['original_url']}")
            print(f"      Final:      {result.get('final_url', 'N/A')}")
            print(f"      Zincir:     {' -> '.join(result['chain'])}")
            print(f"      Derinlik:   {result['depth']}")
            print(f"      Süre:       {result['total_time']:.2f}s")
            if result.get('error'):
                print(f"      Hata:       {result['error']}")
        except Exception as e:
            print(f"\n   💥 Beklenmeyen hata: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*70}")
    print("Test tamamlandı.")
