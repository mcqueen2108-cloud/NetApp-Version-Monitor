import requests
import re

URL = "https://docs.netapp.com/us-en/ontap/release-notes/index.html"

pagina = requests.get(URL)
texto = pagina.text

# Busca patrones como 9.16.1P1, 9.16.1P2, etc.
versiones = re.findall(r'9\.16\.1P\d+', texto)

if not versiones:
    print("No se encontró ninguna versión")
    exit()

ultima = sorted(versiones)[-1]

# OPTIMIZACIÓN: Manejo de la ausencia del archivo inicial
try:
    with open("ultima_version.txt") as f:
        instalada = f.read().strip()
except FileNotFoundError:
    instalada = ""  # Si el archivo no existe, se inicializa vacío [cite: 35]

print("Instalada:", instalada)
print("Disponible:", ultima)

if instalada != ultima:
    print("Nueva versión encontrada")

    with open("ultima_version.txt", "w") as f:
        f.write(ultima)

    # Lanza la excepción para alertar a GitHub Actions sobre el cambio
    raise Exception(f"Nueva versión disponible {ultima}")

print("Todo actualizado")
