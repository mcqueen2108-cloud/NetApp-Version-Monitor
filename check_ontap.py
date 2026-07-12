import requests
import re
import os
from bs4 import BeautifulSoup

# URL de la documentación de NetApp ONTAP
URL = "https://docs.netapp.com/us-en/ontap/release-notes/index.html"

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
todo_el_texto = soup.get_text()
enlaces = [a.get('href', '') for a in soup.find_all('a')]

# Combinamos todo el texto visible y las URLs de los enlaces
texto_a_buscar = todo_el_texto + " " + " ".join(enlaces)

# REGEX ESTRICTA: Busca únicamente '9.16.1' seguido opcionalmente de espacios/guiones y el parche P
patron_con_p = r'9\.16\.1(?:\s*|-*)[pP]\d+'
hallazgos = re.findall(patron_con_p, texto_a_buscar)

# PLAN DE RESPALDO: Si no encuentra parches con P, busca el texto '9.16.1' a secas
if not hallazgos:
    print("No se encontró formato con 'P' para 9.16.1, buscando versión general...")
    patron_general = r'9\.16\.1'
    hallazgos = re.findall(patron_general, texto_a_buscar)

if not hallazgos:
    print("No se encontró ninguna mención de la versión 9.16.1 en la página.")
    exit()

# Limpieza y normalización de las versiones encontradas
versiones_limpias = []
for v in hallazgos:
    if 'p' in v.lower():
        v_normalizada = re.sub(r'(?:\s*|-*)[pP]', 'P', v)
        versiones_limpias.append(v_normalizada)
    else:
        # Si solo dice '9.16.1', le asignamos P0 para poder comparar
        versiones_limpias.append("9.16.1P0")

# FUNCIÓN DE ORDENAMIENTO COMPONENTE POR COMPONENTE
def clave_ordenamiento(v):
    numeros = re.findall(r'\d+', v)
    return tuple(int(n) for n in numeros)

# Obtenemos la versión más reciente absoluta de la rama 9.16.1
ultima = sorted(list(set(versiones_limpias)), key=clave_ordenamiento)[-1]

try:
    with open("ultima_version.txt") as f:
        instalada = f.read().strip()
except FileNotFoundError:
    instalada = "" 

print("Última registrada en el repositorio:", instalada)
print("Versión más reciente detectada en la Web:", ultima)

hay_actualizacion = "false"

if instalada != ultima:
    print(f"¡Nueva actualización/parche encontrado para 9.16.1: {ultima}!")
    hay_actualizacion = "true"

    with open("ultima_version.txt", "w") as f:
        f.write(ultima)

# Le pasamos las variables de resultado a GitHub Actions a través de GITHUB_OUTPUT
if "GITHUB_OUTPUT" in os.environ:
    with open(os.environ["GITHUB_OUTPUT"], "a") as env:
        env.write(f"actualizado={hay_actualizacion}\n")
        env.write(f"version={ultima}\n")

print("Monitoreo completado con éxito.")
