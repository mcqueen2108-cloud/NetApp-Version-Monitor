import re
import os
import sys
from playwright.sync_api import sync_playwright

URL_HTML = "https://mysupport.netapp.com/site/products/all/details/ontap9/downloads-tab"

# Solo nos interesa la rama 9.16.1PX
RAMA = "9.16.1"
PATRON = re.compile(rf'{re.escape(RAMA)}(?:[pP]|\s+[pP]|-+[pP])(\d+)')

ARCHIVO_REGISTRO = "NetApp-Version-Monitor.txt"
DEBUG_DIR = "debug_output"


def guardar_evidencia(page, sufijo: str):
    """Guarda screenshot + HTML + texto visible con un sufijo, para depurar cada etapa."""
    try:
        page.screenshot(path=os.path.join(DEBUG_DIR, f"pagina_{sufijo}.png"), full_page=True)
    except Exception as e:
        print(f"No se pudo tomar screenshot ({sufijo}): {e}")
    try:
        with open(os.path.join(DEBUG_DIR, f"pagina_{sufijo}.html"), "w", encoding="utf-8") as f:
            f.write(page.content())
    except Exception as e:
        print(f"No se pudo guardar el HTML ({sufijo}): {e}")
    try:
        texto = page.inner_text("body")
        with open(os.path.join(DEBUG_DIR, f"texto_{sufijo}.txt"), "w", encoding="utf-8") as f:
            f.write(texto)
        return texto
    except Exception as e:
        print(f"No se pudo capturar texto ({sufijo}): {e}")
        return ""


def cerrar_banner_cookies(page):
    """
    El banner de cookies de NetApp vive aparentemente en un shadow DOM cerrado
    (no aparece en innerText del body). Probamos varias estrategias, cada una
    con timeout corto, sin fallar el script si ninguna funciona.
    """
    estrategias = [
        lambda: page.get_by_role("button", name="Accept all").click(timeout=4000),
        lambda: page.get_by_text("Accept all", exact=True).click(timeout=4000),
        lambda: page.locator("button:has-text('Accept all')").first.click(timeout=4000),
    ]
    for estrategia in estrategias:
        try:
            estrategia()
            print("Banner de cookies cerrado.")
            return True
        except Exception:
            continue

    # Último recurso: clic por coordenadas fijas, basado en el layout visto
    # en el screenshot de depuración (viewport 1280x720 por defecto de Playwright).
    try:
        page.mouse.click(391, 623)
        print("Intenté cerrar el banner de cookies por coordenadas (último recurso).")
        return True
    except Exception as e:
        print(f"No se pudo cerrar el banner de cookies por ninguna vía: {e}")
        return False


def obtener_texto_renderizado(url: str) -> str:
    os.makedirs(DEBUG_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            ),
        )

        page.goto(url, timeout=60000, wait_until="domcontentloaded")

        try:
            page.wait_for_function("document.body.innerText.length > 300", timeout=30000)
        except Exception:
            pass

        page.wait_for_timeout(2000)
        guardar_evidencia(page, "01_inicial")

        cerrar_banner_cookies(page)
        page.wait_for_timeout(1000)
        guardar_evidencia(page, "02_post_cookies")

        # Buscar y usar el campo de filtro de versión
        texto_final = ""
        try:
            campo = page.locator("#filterInput")
            campo.wait_for(state="visible", timeout=15000)
            campo.click()
            campo.type(RAMA, delay=120)  # delay simula tecleo real para disparar el binding de Angular
            page.wait_for_timeout(2500)  # margen para que cargue el autocompletar
            texto_final = guardar_evidencia(page, "03_post_busqueda")
        except Exception as e:
            print(f"No se pudo interactuar con el campo de versión (#filterInput): {e}")
            # seguimos con lo que tengamos del paso anterior como último recurso
            texto_final = page.inner_text("body")

        browser.close()
        return texto_final


def extraer_parches(texto: str):
    return [int(p) for p in PATRON.findall(texto)]


def leer_version_registrada(path: str) -> str:
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def escribir_output_github(actualizado: str, version: str):
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as env:
            env.write(f"actualizado={actualizado}\n")
            env.write(f"version={version}\n")


def main():
    print(f"Conectando (con navegador headless) a: {URL_HTML}")
    try:
        texto = obtener_texto_renderizado(URL_HTML)
    except Exception as e:
        print(f"ERROR al renderizar la página: {e}")
        sys.exit(1)

    parches_encontrados = extraer_parches(texto)

    if not parches_encontrados:
        print(
            f"No se encontró ningún parche de la rama {RAMA} en la página renderizada. "
            "Revisa los archivos en debug_output/ (paso 03_post_busqueda) para ver "
            "qué se alcanzó a mostrar tras escribir en el campo de versión."
        )
        sys.exit(1)

    parche_maximo_web = max(parches_encontrados)
    ultima_web = f"{RAMA}P{parche_maximo_web}"

    instalada = leer_version_registrada(ARCHIVO_REGISTRO)

    print(f"Tu versión registrada en el repositorio ({ARCHIVO_REGISTRO}): {instalada or '(vacío)'}")
    print(f"Última versión detectada en la Web para la rama {RAMA}: {ultima_web}")

    hay_actualizacion = "false"

    if instalada == "":
        print("El archivo de registro está vacío. No se enviará alerta hasta que guardes una versión inicial.")
    else:
        match_instalada = re.search(r'[pP](\d+)', instalada)
        if not match_instalada:
            print(f"ADVERTENCIA: no pude interpretar el número de parche en '{instalada}'.")
            sys.exit(1)

        num_instalada = int(match_instalada.group(1))

        if parche_maximo_web > num_instalada:
            print(f"¡Nueva versión superior detectada en la Web!: {ultima_web}")
            hay_actualizacion = "true"
        else:
            print("Todo al día. No hay parches más nuevos que los que tienes registrados.")

    escribir_output_github(hay_actualizacion, ultima_web)


if __name__ == "__main__":
    main()
