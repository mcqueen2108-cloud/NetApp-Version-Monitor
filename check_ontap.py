import requests
import re
import os
from bs4 import BeautifulSoup

# URL de la documentación de NetApp ONTAP
URL = "https://mysupport.netapp.com/site/products/all/details/ontap9/downloads-tab"

# Cabecera para simular un navegador web y evitar bloqueos
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    pagina = requests.get(URL, headers=headers, timeout=15)
    html_content = pagina.text
except Exception as e:
    print(f"Error al conectar con la página: {e}")
    exit()

# Analizamos el HTML completo para buscar en el texto y también en las URLs de los enlaces (href)
soup = BeautifulSoup(html_content, 'html.parser')
todo_el_texto = soup.get_text()
enlaces = [a.get('href', '') for a in soup.find_all('a')]

# Juntamos todo para asegurarnos de capturar parches que estén ocultos en botones o menús
texto_a_buscar = todo_el_texto + " " + " ".join(enlaces)

# REGEX DINÁMICA: Busca cualquier versión 9.X.X seguido opcionalmente de espacios/guiones y el parche P
# Ejemplo: Captura '9.16.1P13', '9.16.1 P13', '9.16.2-P1', etc.
patron = r'9\.\d+\.\d+(?:\s*|-*)P\d+'
hallazgos = re.findall(patron, texto_a_buscar, re.IGNORECASE)

if not hallazgos:
    print("No se encontró ninguna versión con parche P en la página.")
    exit()

# Limpieza y normalización: Convertimos cualquier variante como '9.16.1-P13' en '9.16.1P13'
versiones_limpias = []
for v in hallazgos:
    v_normalizada = re.sub(r'(?:\s*|-*)P', 'P', v.upper())
    versiones_limpias.append(v_normalizada)

# FUNCIÓN DE ORDENAMIENTO COMPONENTE POR COMPONENTE:
# Convierte '9.16.1P13' en una tupla de números enteros (9, 16, 1, 13) para que Python sepa ordenarlo lógicamente
def clave_ordenamiento(v):
    numeros = re.findall(r'\d+', v)
    return tuple(int(n) for n in numeros)

# Obtenemos la versión más reciente absoluta de la Web
ultima = sorted(list(set(versiones_limpias)), key=clave_ordenamiento)[-1]

# Intentamos leer la última versión que teníamos registrada localmente
try:
    with open("ultima_version.txt") as f:
        instalada = f.read().strip()
except FileNotFoundError:
    instalada = "" 

print("Última registrada en el repositorio:", instalada)
print("Versión más reciente detectada en la Web:", ultima)

hay_actualizacion = "false"

# Si es una versión nueva (o si el archivo estaba vacío), actualizamos el registro
if instalada != ultima:
    print(f"¡Nueva ramificación/parche encontrado: {ultima}!")
    hay_actualizacion = "true"

    with open("ultima_version.txt", "w") as f:
        f.write(ultima)

# Le pasamos las variables de resultado a GitHub Actions a través de GITHUB_OUTPUT
if "GITHUB_OUTPUT" in os.environ:
    with open(os.environ["GITHUB_OUTPUT"], "a") as env:
        env.write(f"actualizado={hay_actualizacion}\n")
        env.write(f"version={ultima}\n")

print("Monitoreo completado con éxito.")
