import requests
import re

URL = httpsdocs.netapp.comus-enontaprelease-notesindex.html

pagina = requests.get(URL)

texto = pagina.text

versiones = re.findall(r'9.16.1Pd+', texto)

if not versiones :
    print(No se encontró ninguna versión)
    exit()

ultima = sorted(versiones)[-1]

with open(ultima_version.txt) as f
    instalada = f.read().strip()

print(Instalada, instalada)
print(Disponible, ultima)

if instalada != ultima :
    print(Nueva versión encontrada)

    with open(ultima_version.txt,w) as f
        f.write(ultima)

    raise Exception(fNueva versión disponible {ultima})

print(Todo actualizado)
