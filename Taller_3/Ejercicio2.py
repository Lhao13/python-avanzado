from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import random
import re
from urllib.parse import quote_plus

# visualization deps (optional)
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOT_LIBS = True
except Exception:
    HAS_PLOT_LIBS = False
    pd = plt = sns = None


def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120 Safari/537.36"
    )
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    return driver


# ------------------------------
# Normalizar precio (devuelve float)
# ------------------------------

def norm_price_str(p: str):
    if not p:
        return None
    s = re.sub(r"[^\d\.,]", "", p)
    if "," in s and "." not in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        return float(s)
    except:
        return None


# Ajustar la función `extract_rating` para manejar ratings nulos y limitar valores

def extract_rating(soup):
    """Try common selectors to extract a star rating as float and raw string."""
    rating_raw = None
    rating = None

    # common selectors/meta
    candidates = [
        "meta[itemprop='ratingValue']",
        "meta[name='og:rating']",
        "span.a-icon-alt",
        "i.a-icon-star span",
        ".reviews-summary .average-rating",
        ".stars-reviews-count",
        ".ui-pdp-review__rating--average",
        ".reviews-seeAll .average",
        ".prod-ProductCTA--primary .stars"
    ]

    for sel in candidates:
        el = soup.select_one(sel)
        if el:
            if el.name == 'meta':
                rating_raw = el.get('content')
            else:
                rating_raw = el.get_text(strip=True)
            break

    # fallback: try to find patterns like '4.5 out of 5' or '4.5/5' in text
    if rating_raw is None:
        txt = soup.get_text(" ", strip=True)
        m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:out of|/|de)\s*5", txt, re.IGNORECASE)
        if m:
            rating_raw = m.group(0)
            try:
                rating = float(m.group(1))
            except:
                rating = None

    # if we have rating_raw but not parsed numeric, try to parse a number from it
    if rating_raw is not None and rating is None:
        m2 = re.search(r"([0-9]+(?:\.[0-9]+)?)", rating_raw)
        if m2:
            try:
                rating = float(m2.group(1))
            except:
                rating = None

    # Si el rating es None, colocarlo como 0
    if rating is None:
        rating = 0

    # Limitar ratings mayores a 5
    if rating > 5:
        rating = 5

    return rating, rating_raw


def amazon_search(driver, query):
    url = f"https://www.amazon.com/s?k={quote_plus(query)}"

    driver.get(url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "lxml")

    results = []
    items = soup.select("div.s-result-item[data-asin]")[:10]  # Limit to first 10 results
    for r in items:
        asin = r.get("data-asin")
        if asin:
            a = r.select_one("a.a-link-normal.s-no-outline")
            if a and a.get("href"):
                results.append("https://www.amazon.com" + a.get("href"))

    return results


def amazon_parse(driver, url):
    driver.get(url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "lxml")

    title = None
    t = soup.find(id="productTitle")
    if t:
        title = t.get_text(strip=True)

    price = None
    price_raw = None
    for sel in ["#priceblock_ourprice", "#priceblock_dealprice", ".a-offscreen"]:
        el = soup.select_one(sel)
        if el:
            price_raw = el.get_text(strip=True)
            parsed = norm_price_str(price_raw)
            # aceptar floats: si parsed es None -> "precio no encontrado", else usar float
            if parsed is None:
                price = "precio no encontrado"
            else:
                price = parsed
            break

    avail = None
    a = soup.find(id="availability")
    if a:
        avail = a.get_text(strip=True)

    # Rating
    rating, rating_raw = extract_rating(soup)

    return {
        "site": "Amazon",
        "url": url,
        "title": title,
        "price": price,
        "price_raw": price_raw,
        "availability": avail,
        "rating": rating,
        "rating_raw": rating_raw
    }


# ------------------------------
# MERCADOLIBRE 
# ------------------------------


def mercadolibre_search(driver, query):
    # candidate search URLs (try listado domain first, then main domain)
    candidates = [
        f"https://listado.mercadolibre.com.ec/{quote_plus(query)}",
        f"https://listado.mercadolibre.com.ec/{quote_plus(query)}#D[A:{quote_plus(query)}]",
        f"https://www.mercadolibre.com.ec/search?q={quote_plus(query)}",
        f"https://listado.mercadolibre.com.ec/search?q={quote_plus(query)}",
    ]

    results = []

    for url in candidates:
        try:
            driver.get(url)
            # pequeño sleep para que cargue JS/tracking
            time.sleep(2 + random.random() * 1.5)
            soup = BeautifulSoup(driver.page_source, "lxml")

            # Collect up to 10 product links
            links = soup.select("a.ui-search-link")[:10]
            for link in links:
                if link and link.get("href"):
                    results.append(link.get("href"))

            if results:
                break  # Stop after finding results

        except Exception:
            continue

    return results


def mercadolibre_parse(driver, url):
    # abrir el URL tal cual (puede ser absoluto o relativo)
    try:
        driver.get(url)
    except Exception:
        # en caso de href parcial, intentar normalizar
        if url.startswith("/"):
            driver.get("https://www.mercadolibre.com.ec" + url)
        else:
            driver.get(url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "lxml")

    # Title
    title = None
    t = soup.select_one("h1.ui-pdp-title")
    if t:
        title = t.get_text(strip=True)
    else:
        t = soup.find("h1")
        if t:
            title = t.get_text(strip=True)

    # Price detection: probar varios selectores y también meta tags
    price_raw = None
    price = None

    candidates = [
        ".andes-money-amount__fraction",            # común
        ".price-tag-fraction",                      # alternativa
        ".ui-pdp-price__second-line .andes-money-amount__fraction",
        ".ui-pdp-price__second-line .price-tag-fraction",
        "meta[itemprop='price']",
        "meta[property='product:price:amount']"
    ]

    for sel in candidates:
        el = soup.select_one(sel)
        if el:
            # si es meta
            if el.name == "meta":
                price_raw = el.get("content")
            else:
                price_raw = el.get_text(strip=True)
            parsed = norm_price_str(price_raw)
            if parsed is None:
                price = "precio no encontrado"
            else:
                price = parsed
            break

    # si no encontramos price_raw, intentar ensamblar fracción + decimales
    if price_raw is None:
        frac = soup.select_one(".andes-money-amount__fraction")
        dec = soup.select_one(".andes-money-amount__decimals")
        if frac:
            frac_text = frac.get_text(strip=True)
            if dec:
                dec_text = dec.get_text(strip=True)
                combined = f"{frac_text}.{dec_text}"
            else:
                combined = frac_text
            parsed = norm_price_str(combined)
            if parsed is None:
                price = "precio no encontrado"
            else:
                price = parsed
            price_raw = combined

    # Availability attempts
    availability = None
    a1 = soup.select_one(".ui-pdp-buybox__quantity__available")
    if a1:
        availability = a1.get_text(strip=True)
    else:
        a2 = soup.select_one(".ui-pdp-variation__availability, .ui-pdp-product-info__availability")
        if a2:
            availability = a2.get_text(strip=True)

    # Rating
    rating, rating_raw = extract_rating(soup)

    return {
        "site": "MercadoLibre",
        "url": url,
        "title": title,
        "price": price,
        "price_raw": price_raw,
        "availability": availability,
        "rating": rating,
        "rating_raw": rating_raw
    }


# Global variable to accumulate results
accumulated_results = []

def visualize_results(results):
    """Generar gráficos individuales por producto."""
    if not HAS_PLOT_LIBS:
        print("Visualization libraries not installed. To enable plotting run: pip install pandas matplotlib seaborn")
        return

    df = pd.DataFrame(results)

    # Normalizar columna de precios: asegurar valores numéricos, eliminar no numéricos
    df['price_numeric'] = pd.to_numeric(df['price'], errors='coerce')

    # Eliminar productos sin precio
    df = df.dropna(subset=['price_numeric'])

    # Limitar precios mayores a 5000 dólares
    df.loc[df['price_numeric'] > 5000, 'price_numeric'] = 5000

    # Generar gráficos por cada producto
    for query in df['query'].unique():
        product_df = df[df['query'] == query]

        if product_df.empty:
            print(f"No hay datos para el producto: {query}")
            continue

        print(f"Generando gráficos para el producto: {query}")

        # Crear figura con 3 subplots
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle(f'Gráficos para: {query}', fontsize=16)

        # Gráfico de distribución de precios
        try:
            sns.violinplot(x='site', y='price_numeric', data=product_df, ax=axes[0])
            axes[0].set_title('Distribución de precios por plataforma')
            axes[0].set_xlabel('Plataforma')
            axes[0].set_ylabel('Precio')
        except Exception as e:
            axes[0].text(0.5, 0.5, 'No hay datos de precio', ha='center', va='center')
            axes[0].set_axis_off()

        # Gráfico de valoración vs precio
        scatter_df = product_df.dropna(subset=['rating'])
        if not scatter_df.empty:
            sns.scatterplot(x='rating', y='price_numeric', hue='site', data=scatter_df, s=80, ax=axes[1], palette='tab10')
            axes[1].set_title('Precio vs Valoración (rating)')
            axes[1].set_xlabel('Rating (estrellas)')
            axes[1].set_ylabel('Precio')
        else:
            axes[1].text(0.5, 0.5, 'No hay datos de price & rating', ha='center', va='center')
            axes[1].set_axis_off()

        # Gráfico de correlación Amazon vs MercadoLibre usando sólo precios de este producto
        amazon_prices = product_df[product_df['site'] == 'Amazon']['price_numeric'].tolist()
        ml_prices = product_df[product_df['site'] == 'MercadoLibre']['price_numeric'].tolist()
        matched_len = min(len(amazon_prices), len(ml_prices))
        if matched_len >= 2:
            matched_df = pd.DataFrame({
                'Amazon': amazon_prices[:matched_len],
                'MercadoLibre': ml_prices[:matched_len]
            })
            corr = matched_df.corr()
            sns.heatmap(corr, annot=True, vmin=-1, vmax=1, cmap='coolwarm', ax=axes[2])
            pearson = corr.loc['Amazon', 'MercadoLibre']
            axes[2].set_title(f'Correlación Amazon vs MercadoLibre (r={pearson:.2f})')
        else:
            axes[2].text(0.5, 0.5, 'Datos insuficientes para correlación', ha='center', va='center')
            axes[2].set_axis_off()

        plt.tight_layout()
        plt.show()


def print_results_table(results):
    """Print a compact table of results to the console."""
    if not results:
        print("No results to display")
        return

    # choose columns to show and ensure existence
    cols = ["site", "query", "title", "price", "rating", "availability"]
    # compute column widths
    rows = []
    max_title = 40
    for r in results:
        title = r.get('title') or ''
        # truncate long titles
        if len(title) > max_title:
            title = title[: max_title - 3] + '...'
        row = [str(r.get('site', '')), str(r.get('query', '')), title, str(r.get('price', '')), str(r.get('rating', '')), str(r.get('availability', ''))]
        rows.append(row)

    widths = [max(len(str(c)), max((len(row[i]) for row in rows), default=0)) for i, c in enumerate(cols)]

    # header
    hdr = " | ".join(c.ljust(widths[i]) for i, c in enumerate(cols))
    sep = "-+-".join('-' * widths[i] for i in range(len(cols)))
    print("\nRESULTADOS TABLA:\n")
    print(hdr)
    print(sep)
    for row in rows:
        print(" | ".join(row[i].ljust(widths[i]) for i in range(len(cols))))
    print()


# ------------------------------
# MAIN
# ------------------------------

def monitor_and_visualize():
    global accumulated_results
    products = [
        "dji mini 3",
    ]

    driver = get_driver()
    results = []

    for q in products:
        print(f"\n=== PRODUCTO: {q}")

        # AMAZON
        amazon_urls = amazon_search(driver, q)
        for au in amazon_urls:
            print("Amazon → encontrado")
            r = amazon_parse(driver, au)
            r['query'] = q
            results.append(r)

        # MERCADOLIBRE
        mercadolibre_urls = mercadolibre_search(driver, q)
        for mu in mercadolibre_urls:
            print("MercadoLibre → encontrado")
            r = mercadolibre_parse(driver, mu)
            r['query'] = q
            results.append(r)

        time.sleep(1 + random.random() * 2)

    driver.quit()

    accumulated_results.extend(results)

    print("\n\n========= RESULTADOS ACUMULADOS =========\n")
    print_results_table(accumulated_results)

    visualize_results(accumulated_results)

# ------------------------------
# EJECUCIÓN
# ------------------------------
if __name__ == "__main__":
    print("Iniciando monitoreo...")
    monitor_and_visualize()  # Ejecutar una sola vez
