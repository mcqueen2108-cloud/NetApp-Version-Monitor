import requests
import re

# Corrección: URL entre comillas
URL = "https://docs.netapp.com/us-en/ontap/release-notes/index.html"

pagina = requests.get(URL)
texto = pagina.text

# Corrección: El patrón regex debe ser un string válido. 
# Si buscas parches específicos como '9.16.1P1', '9.16.1P2', etc., usamos r'9\.16\.1P\d+'
versiones = re.findall(r'9\.16\.1P\d+', texto)

if not versiones:
    # Corrección: Texto entre comillas (Línea 13)
    print("No se encontró ninguna versión")
    exit()

ultima = sorted(versiones)[-1]

# Corrección: Nombre del archivo entre comillas y agregado el ':' al final del with
with open("ultima_version.txt") as f:
    instalada = f.read().strip()

# Corrección: Textos entre comillas
print("Instalada:", instalada)
print("Disponible:", ultima)

if instalada != ultima:
    print("Nueva versión encontrada")

    # Corrección: Nombre de archivo, modo 'w' entre comillas y el ':' faltante
    with open("ultima_version.txt", "w") as f:
        f.write(ultima)

    # Corrección: f-string correctamente estructurado entre comillas
    raise Exception(f"Nueva versión disponible {ultima}")

print("Todo actualizado")
