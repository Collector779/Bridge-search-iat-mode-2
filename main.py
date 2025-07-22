import time
import requests
import random
import html
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed # dodane as shit

URL = "https://bridges.torproject.org/bridges?transport=obfs4"
PLIK_WYJSCIA = "mostekiat=2.txt"
PROXY_LIST_URL = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=https&timeout=2000&country=all&ssl=all&anonymity=all" 
LICZBA_WATKOW = 5

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 Chrome/91.0.4472.120 Mobile Safari/537.36"
]

ACCEPT_HEADERS = [
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "text/html,application/xml;q=0.9,*/*;q=0.8",
    "text/html;q=0.9,image/avif,image/webp,*/*;q=0.8"
]

LANG_HEADERS = [
    "en-US,en;q=0.5",
    "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
    "en;q=0.8",
    "fr-FR,fr;q=0.9,en;q=0.8"
]

def losowy_user_agent():
    return random.choice(USER_AGENTS)

def losowe_naglowki():
    headers = {
        "User-Agent": losowy_user_agent(),
        "Accept": random.choice(ACCEPT_HEADERS),
        "Accept-Language": random.choice(LANG_HEADERS),
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    return dict(random.sample(list(headers.items()), len(headers)))

def pobierz_losowe_proxy():
    try:
        print(f"[DEBUG] Pobieram listę proxy z {PROXY_LIST_URL}")
        resp = requests.get(PROXY_LIST_URL, timeout=20)
        proxy_list = resp.text.strip().split('\n')
        pattern = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}:(3128|8080|443)$")
        proxy_list = [p.strip() for p in proxy_list if pattern.match(p.strip())]
        print(f"[DEBUG] Liczba pobranych HTTPS proxy: {len(proxy_list)}")
        if not proxy_list:
            print("[DEBUG] Proxy LISTA PUSTA! Zawartość odpowiedzi:")
            print(resp.text[:500])
            print("Lista proxy pusta lub brak poprawnych wpisów.")
            return None
        proxy = random.choice(proxy_list)
        print(f"[DEBUG] Wylosowane proxy: {proxy}")
        return {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}",
        }
    except Exception as e:
        print(f"[DEBUG] Błąd przy pobieraniu proxy: {e}")
        return None

def pobierz_mostki(proxy=None):
    session = requests.Session()
    try:
        headers = losowe_naglowki()
        session.headers.update(headers)
        if proxy:
            print(f"[DEBUG] Pobieram mostki przez proxy: {proxy}")
        else:
            print(f"[DEBUG] Pobieram mostki bez proxy...")
        response = session.get(URL, proxies=proxy, timeout=15)
        print(f"[DEBUG] Kod odpowiedzi HTTP: {response.status_code}")
        response.raise_for_status()
    except Exception as e:
        print(f"[DEBUG] Błąd przy połączeniu ({proxy}): {e}")
        return [], []

    soup = BeautifulSoup(response.text, "html.parser")
    bridge_div = soup.find("div", {"id": "bridgelines"})
    if not bridge_div:
        print("[DEBUG] Nie znaleziono div-a o id='bridgelines'!")
        print("[DEBUG] Fragment HTML:\n", response.text[:700])
        return [], []

    print(f"[DEBUG] Zawartość bridge_div:\n{bridge_div.text.strip()}")
    lines = [html.unescape(line.strip()) for line in bridge_div.text.splitlines() if line.strip().startswith("obfs4")]
    print(f"[DEBUG] Ilość znalezionych linii z obfs4: {len(lines)}")
    wszystkie_mostki = []
    iat2_mostki = []

    for line in lines:
        print(f"[DEBUG] Mostek: {line}")
        wszystkie_mostki.append(line)
        if "iat-mode=2" in line:
            iat2_mostki.append(line)

    print(f"[DEBUG] Mostki z iat-mode=2: {len(iat2_mostki)}")
    print(f"[DEBUG] Pozostałe mostki: {len(wszystkie_mostki)}")

    return iat2_mostki, wszystkie_mostki

def zapisz_do_pliku(mostki):
    try:
        with open(PLIK_WYJSCIA, "a", encoding="utf-8") as f:
            for m in mostki:
                f.write(m + "\n")
        print(f"Zapisano {len(mostki)} mostek/mostki do pliku.")
        for m in mostki:
            print("   ", m)
    except Exception as e:
        print(f"Błąd przy zapisie do pliku: {e}")

def procesuj_proxy():
    proxy = pobierz_losowe_proxy()
    if proxy is None:
        print("Brak działającego proxy.")
        return []
    return pobierz_mostki(proxy=proxy)

def main():
    while True:
        print(f"\nSprawdzam nowe mostki obfs4 w {LICZBA_WATKOW} wątkach...\n")

        mostki_iat2 = []
        mostki_inne = []

        with ThreadPoolExecutor(max_workers=LICZBA_WATKOW) as executor:
            futures = [executor.submit(procesuj_proxy) for _ in range(LICZBA_WATKOW)]
            for future in as_completed(futures):
                iat2, wszystkie = future.result()
                if iat2:
                    mostki_iat2.extend(iat2)
                elif wszystkie:
                    mostki_inne.extend(wszystkie)

        if mostki_iat2:
            print(f"Znaleziono łącznie {len(mostki_iat2)} mostków z iat-mode=2.")
            zapisz_do_pliku(mostki_iat2)
        elif mostki_inne:
            print("Nie znaleziono mostków z iat-mode=2, ale znaleziono inne obfs4:")
            for m in mostki_inne:
                print("   ", m)
        else:
            print("Nie znaleziono żadnych mostków obfs4.")

        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPrzerwano ręcznie. Kończę działanie.")