import requests
import re
import os

URL = "https://docs.netapp.com/us-en/ontap/release-notes/index.html"

pagina = requests.get(URL)
texto = pagina.text

# OPTIMIZACIÓN: El '\d+' asegura que capture números de dos o más dígitos (como 11 y 13)
versiones = re.findall(r'9\.16\.1P\d+', texto)

if not versiones:
    print("No se encontró ninguna versión")
    exit()

# OPTIMIZACIÓN: Función clave para ordenar numéricamente por el parche final
def extraer_parche(v):
    # Extrae el número después de la 'P' y lo convierte a entero para ordenar bien (ej: 13 > 9)
    match = re.search(r'P(\d+)', v)
    return int(match.group(1)) if match else 0

# Ordena de menor a mayor usando el número del parche y toma la última v[ -1 ]
ultima = sorted(list(set(versiones)), key=extraer_parche)[-1]

try:
    with open("ultima_version.txt") as f:
        instalada = f.read().strip()
except FileNotFoundError:
    instalada = "" 

print("Instalada en registro:", instalada)
print("Disponible en la Web:", ultima)

hay_actualizacion = "false"

if instalada != ultima:
    print("¡Nueva versión encontrada!")
    hay_actualizacion = "true"

    with open("ultima_version.txt", "w") as f:
        f.write(ultima)

# Comunicar a GitHub Actions
if "GITHUB_OUTPUT" in os.environ:
    with open(os.environ["GITHUB_OUTPUT"], "a") as env:
        env.write(f"actualizado={hay_actualizacion}\n")
        env.write(f"version={ultima}\n")

print("Proceso finalizado.")
