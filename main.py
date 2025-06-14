import time
import requests
from bs4 import BeautifulSoup

URL = "https://bridges.torproject.org/bridges?transport=obfs4"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"
}
PLIK_WYJSCIA = "gotowemostki.txt"

def pobierz_mostki():
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"[!] Błąd podczas pobierania strony: {e}")
        return [], []

    text = response.text

    idx = text.find("Here are your bridge lines:")
    if idx == -1:
        print("[!] Nie znaleziono mostków na stronie.")
        return [], []

    fragment = text[idx:idx+2000]

    wszystkie_mostki = []
    iat2_mostki = []

    for line in fragment.splitlines():
        line = line.strip()
        if line.startswith("obfs4"):
            wszystkie_mostki.append(line)
            if "iat-mode=2" in line:
                iat2_mostki.append(line)

    return iat2_mostki, wszystkie_mostki


def zapisz_do_pliku(mostki):
    try:
        with open(PLIK_WYJSCIA, "w", encoding="utf-8") as f:
            for m in mostki:
                f.write(m + "\n")
        print(f"[💾] Zapisano {len(mostki)} mostek/mostki do pliku: {PLIK_WYJSCIA}")
        print("[📋] Zapisane mostki:")
        for m in mostki:
            print("   ", m)
    except Exception as e:
        print(f"[!] Błąd podczas zapisu do pliku: {e}")


def main():
    while True:
        print("[+] Pobieram mostki obfs4 z iat-mode=2...")
        iat2, wszystkie = pobierz_mostki()

        if iat2:
            print(f"[✔] Znaleziono {len(iat2)} mostek/mostki z iat-mode=2:")
            for m in iat2:
                print("   ", m)
            zapisz_do_pliku(iat2)
        else:
            print("[✘] Nie znaleziono mostków z iat-mode=2.")
            if wszystkie:
                print("[~] Dostępne mostki obfs4 (bez iat-mode=2):")
                for m in wszystkie:
                    print("   ", m)
            else:
                print("[✘] Nie znaleziono żadnych mostków obfs4.")

        print("Odswiezam za 30 minut...\n")
        try:
            time.sleep(1800)
        except KeyboardInterrupt:
            print("\n[!] Przerwano ręcznie. Kończę działanie.")
            break


if __name__ == "__main__":
    main()