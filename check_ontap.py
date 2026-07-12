import requests
import re
import os
from bs4 import BeautifulSoup

URL = "https://mysupport.netapp.com/site/products/all/details/ontap9/downloads-tab"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    pagina = requests.get(URL, headers=headers, timeout=15)
    html_content = pagina.text
except Exception as e:
    print(f"Error al conectar con la página: {e}")
    exit()

soup = BeautifulSoup(html_content, 'html.parser')

# Extraemos texto y enlaces relevantes
textos = [soup.get_text()]
for tag in soup.find_all(['a', 'title', 'meta']):
    textos.append(tag.get_text())
    if tag.get('href'):
        textos.append(tag.get('href'))

texto_a_buscar = " ".join(textos)

# Regex estricta para buscar los parches de la rama 9.16.1
patron_con_p = r'9\.16\.1(?:\s*|-*)[pP](\d+)'
hallazgos_p = re.findall(patron_con_p, texto_a_buscar)

if hallazgos_p:
    max_p = max(int(p) for p in hallazgos_p)
    ultima_web = f"9.16.1P{max_p}"
else:
    # Si la web no expone el parche dinámicamente en el índice, usamos el último conocido
    print("No se visualizaron parches dinámicos con 'P' en el índice general.")
    ultima_web = "9.16.1P11" 

# --- AQUÍ CORREGIMOS EL NOMBRE DE TU ARCHIVO ---
archivo_registro = "NetApp-Version-Monitor.txt"

try:
    with open(archivo_registro) as f:
        instalada = f.read().strip()
except FileNotFoundError:
    instalada = "" 

print(f"Tu versión registrada en {archivo_registro}: {instalada}")
print("Versión detectada/asignada para la Web:", ultima_web)

hay_actualizacion = "false"

# Si el archivo está alineado con la web, no hace nada
if instalada == ultima_web:
    print("Todo al día. Tu infraestructura está alineada con la versión detectada.")
elif instalada == "":
    print(f"El archivo '{archivo_registro}' está vacío o no se encuentra. No se enviará alerta.")
else:
    # Si hay una diferencia, extraemos el número del parche para validar que sea mayor
    def extraer_numero_p(v):
        match = re.search(r'[pP](\d+)', v)
        return int(match.group(1)) if match else 0

    if extraer_numero_p(ultima_web) > extraer_numero_p(instalada):
        print(f"¡Nueva actualización real detectada en la Web: {ultima_web}!")
        hay_actualizacion = "true"
    else:
        print("La versión de la web es igual o menor a la registrada. No se requiere acción.")

# Pasamos las variables a GitHub Actions
if "GITHUB_OUTPUT" in os.environ:
    with open(os.environ["GITHUB_OUTPUT"], "a") as env:
        env.write(f"actualizado={hay_actualizacion}\n")
        env.write(f"version={ultima_web}\n")
