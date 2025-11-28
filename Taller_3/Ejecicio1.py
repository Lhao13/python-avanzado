
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import unicodedata
import datetime
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# -------------------------
# Configuración inicial
# -------------------------
# Suprimir InsecureRequestWarning (solo pruebas)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

urls = {
    "El universo": "https://www.eluniverso.com/",
    "La Hora": "https://www.lahora.com.ec/",
    "Extra": "https://www.extra.ec/",
    "Primicias": "https://www.primicias.ec/",
}

# Intervalo de refresco en segundos (30 minutos)
REFRESH_INTERVAL = 30 * 60

# Palabras clave para la serie temporal (ajusta según interés)
PALABRAS_CLAVE = ["ecuador", "presidente", "elecciones", "gobierno", "economia"]

# Palabras especiales para eliminar manualmente (lowercase, sin tildes)
BLACKLIST = {"asi", "dice", "pone", "como", "quien", "este", "esta", "estos", "estas", "todos", "todas", "mas"}

tildes = {
        'á': 'a',
        'é': 'e',
        'í': 'i',
        'ó': 'o',
        'ú': 'u',
        'Á': 'A',
        'É': 'E',
        'Í': 'I',
        'Ó': 'O',
        'Ú': 'U'
    }

# Cargar stopwords NLTK 
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords', quiet=True)
stop_words = set(stopwords.words('spanish'))


# Normalización: eliminar tildes y signos diacríticos
def quitar_tildes(texto):
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return texto

# Filtrado: eliminar palabras con números o muy cortas, blacklist, stopwords
def limpiar_palabra(p):
    if not p:
        return ''
    p = p.lower()
    p = quitar_tildes(p)

    # eliminar números
    if re.search(r'\d', p):
        return ''

    if len(p) <= 2:
        return ''
    if p in stop_words:
        return ''
    if p in BLACKLIST:
        return ''
    
    # reemplazar tildes manualmente (por si acaso)
    for tilde, sin_tilde in tildes.items():
        p = p.replace(tilde, sin_tilde)

    # pasar a minúsculas
    p=p.lower()
    return p

# Extraer texto 'visible' de la portada porsiacaso
def extraer_texto_portada(url):
    try:
        resp = requests.get(url, headers=HEADERS, verify=False, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(["script", "style", "noscript", "iframe"]):
            tag.decompose()
        texto = soup.get_text(separator=" ", strip=True)
        texto = ' '.join(texto.split())
        return texto
    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP {e} en {url}")
    except Exception as e:
        print(f"Error conexión {e} en {url}")
    return ""

#extraer titulares concretos
def extraer_titulares_generico(url):
    # intenta recoger h1,h2,h3 y enlaces con texto
    try:
        resp = requests.get(url, headers=HEADERS, verify=False, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(["script", "style", "noscript", "iframe"]):
            tag.decompose()
        nodes = []
        nodes += [n.get_text(strip=True) for n in soup.find_all(['h1','h2','h3']) if n.get_text(strip=True)]
        nodes += [a.get_text(strip=True) for a in soup.find_all('a') if a.get_text(strip=True) and len(a.get_text(strip=True))>20]
        # dedup preserving order
        seen = set(); out = []
        for t in nodes:
            if t not in seen:
                seen.add(t); out.append(t)
        return out
    except Exception:
        return []

# -------------------------
# Historial de palabras con timestamp
# -------------------------

# DataFrame con columnas: timestamp (datetime), palabra (str), medio (str), origen (titular o portada)
historial = pd.DataFrame(columns=["timestamp","palabra","medio","origen"])

# -------------------------
# Función de procesamiento de una iteración
# -------------------------

def recolectar_y_procesar():
    global historial
    nuevos_titulares = {}  # guardamos titulares por medio (para mostrar)
    ahora = datetime.datetime.now()
    palabras_iteracion = []  # palabras solo de esta iteración
    for medio, url in urls.items():
        print(f"[{ahora.strftime('%Y-%m-%d %H:%M:%S')}] Extrayendo {medio} ...")
        titulares = extraer_titulares_generico(url)
        if not titulares:
            texto = extraer_texto_portada(url)
            titulares = [texto] if texto else []
        nuevos_titulares[medio] = titulares
        for t in titulares:
            palabras = re.findall(r"\b\w+\b", t.lower())
            for p in palabras:
                pl = limpiar_palabra(p)
                if pl:
                    historial = pd.concat([historial, pd.DataFrame([{
                        "timestamp": ahora, "palabra": pl, "medio": medio, "origen": t[:200]
                    }])], ignore_index=True)
                    palabras_iteracion.append(pl)
        time.sleep(random.uniform(0.5, 1.0))
    return nuevos_titulares, palabras_iteracion, ahora

# -------------------------
# Función para dibujar el dashboard (2x2)
# -------------------------

def dibujar_dashboard(nuevos_titulares, palabras_iteracion, timestamp_iteracion):
    plt.clf()
    fig, axes = plt.subplots(2,2, figsize=(14,10))
    ax1, ax2, ax3, ax4 = axes.flatten()
    plt.subplots_adjust(hspace=0.4, wspace=0.3)

    # 1) Nube de palabras SOLO del intervalo actual
    texto = " ".join(palabras_iteracion) if palabras_iteracion else "vacio"
    wc = WordCloud(width=1000, height=600, background_color='white', max_words=100)
    wc.generate(texto)
    ax1.imshow(wc, interpolation='bilinear')
    ax1.axis("off")
    ax1.set_title("Nube de palabras (titulares, intervalo actual)")

    # 2) Barras top 15 SOLO del intervalo actual
    counter = Counter(palabras_iteracion)
    top = counter.most_common(15)
    if top:
        df_top = pd.DataFrame(top, columns=["Palabra","Frecuencia"])
        sns.barplot(data=df_top, x="Frecuencia", y="Palabra", ax=ax2)
        ax2.set_title("Top 15 palabras (intervalo actual)")
    else:
        ax2.text(0.5,0.5,"No hay datos", ha="center")
        ax2.axis("off")

    # 3) Serie temporal para palabras clave (acumulado, cada 30 minutos)
    if not historial.empty:
        df_time = historial.copy()
        df_time['timestamp'] = pd.to_datetime(df_time['timestamp'])
        df_time.set_index('timestamp', inplace=True)
        inicio = df_time.index.min()
        fin = df_time.index.max()
        idx = pd.date_range(start=inicio.floor('30T'), end=fin.ceil('30T'), freq='30T')
        df_counts = pd.DataFrame(index=idx)
        for palabra in PALABRAS_CLAVE:
            palabra_sin = quitar_tildes(palabra.lower())
            mask = df_time['palabra'] == palabra_sin
            s = df_time[mask].groupby(pd.Grouper(freq='30T')).size().reindex(idx, fill_value=0)
            df_counts[palabra] = s
        df_counts.plot(ax=ax3, marker='o', linewidth=1)
        ax3.set_title("Serie temporal (frecuencia cada 30 minutos) - palabras clave (acumulado)")
        ax3.set_xlabel("Tiempo")
        ax3.set_ylabel("Frecuencia")
        ax3.legend(title="Palabra")
    else:
        ax3.text(0.5,0.5,"Sin datos temporales aún", ha="center")
        ax3.axis("off")

    # 4) Resumen textual: totales y últimos titulares
    resumen = []
    resumen.append(f"Última actualización: {timestamp_iteracion.strftime('%Y-%m-%d %H:%M:%S')}")
    resumen.append(f"Palabras en intervalo actual: {len(palabras_iteracion)}")
    resumen.append("")
    resumen.append("Últimos titulares extraídos (por medio):")
    for medio, lista in nuevos_titulares.items():
        if lista:
            resumen.append(f"- {medio}: {len(lista)} items (ej.: {lista[0][:80]}...)")
        else:
            resumen.append(f"- {medio}: 0 items")
    ax4.axis('off')
    ax4.text(0, 1, "\n".join(resumen), va='top', fontsize=10, family='monospace')

    plt.suptitle("Dashboard en tiempo real - Titulares (actualiza cada 30 minutos)", fontsize=14)
    plt.pause(0.1)
    plt.show(block=False)

# -------------------------
# Loop principal
# -------------------------
def main_loop():
    print("Iniciando recolección en tiempo real. Presiona Ctrl+C para detener.")
    try:
        while True:
            nuevos, palabras_iteracion, timestamp_iteracion = recolectar_y_procesar()
            if not historial.empty:
                historial['timestamp'] = pd.to_datetime(historial['timestamp'])
                historial.dropna(subset=['palabra'], inplace=True)
            dibujar_dashboard(nuevos, palabras_iteracion, timestamp_iteracion)
            for i in range(int(REFRESH_INTERVAL / 5)):
                time.sleep(5)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDetenido por usuario.")
        return

if __name__ == "__main__":
    main_loop()
