import requests
import re
import os

# --- CONFIGURACIÓN ---
archivo_registro = "NetApp-Version-Monitor.txt"

# Leer la versión que tú tienes registrada actualmente en tu repositorio
try:
    with open(archivo_registro) as f:
        instalada = f.read().strip()
except FileNotFoundError:
    instalada = "9.16.1P11"  # Valor por defecto si se borra el archivo

print(f"Tu versión registrada en {archivo_registro}: {instalada}")

# Extraer el número actual de parche P que tienes guardado (ej: de '9.16.1P11' extrae el 11)
match_instalada = re.search(r'[pP](\d+)', instalada)
parche_actual = int(match_instalada.group(1)) if match_instalada else 11

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

print(f"Buscando si existen parches superiores a la P{parche_actual} en la web de NetApp...")

# Probamos los siguientes parches de forma ascendente (ej: si tienes P11, probará P12, P13, P14...)
parche_detectado = parche_actual
for intento in range(parche_actual + 1, parche_actual + 5):
    # Validamos si existe la URL específica de soporte/documentación para este parche
    url_prueba = f"https://docs.netapp.com/us-en/ontap/release-notes/changes-resolved-issues-9161p{intento}.html"
    
    try:
        respuesta = requests.head(url_prueba, headers=headers, timeout=10)
        # Si la página existe (código 200) significa que NetApp liberó y documentó ese parche
        if respuesta.status_code == 200:
            print(f"-> ¡Detectado parche activo en la web!: 9.16.1P{intento}")
            parche_detectado = intento
        else:
            # Si da 404 u otro error, es que ese parche aún no se publica o no tiene documentación pública
            break
    except Exception:
        break

ultima_web = f"9.16.1P{parche_detectado}"
print(f"Versión final determinada de la Web: {ultima_web}")

hay_actualizacion = "false"

# Comparamos el parche que descubrimos contra el que tú tienes instalado
if parche_detectado > parche_actual:
    print(f"¡Nueva actualización real detectada en la Web!: {ultima_web}")
    hay_actualizacion = "true"
else:
    print("Todo al día. Tu infraestructura está alineada con la versión detectada.")

# Pasamos los resultados a GitHub Actions
if "GITHUB_OUTPUT" in os.environ:
    with open(os.environ["GITHUB_OUTPUT"], "a") as env:
        env.write(f"actualizado={hay_actualizacion}\n")
        env.write(f"version={ultima_web}\n")
