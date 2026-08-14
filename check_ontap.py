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


def obtener_texto_renderizado(url: str) -> str:
    """
    mysupport.netapp.com es una SPA (Angular): el HTML crudo llega vacío
    ("Loading..."). Necesitamos un navegador real (headless) para que el
    JavaScript pinte el contenido antes de leerlo.

    IMPORTANTE: no usamos wait_until="networkidle" porque este tipo de sitios
    (analytics, polling, chat widgets, etc.) casi nunca dejan de tener
    actividad de red, así que networkidle nunca se cumple y siempre truena
    en timeout. En su lugar: cargamos con "domcontentloaded" (rápido) y
    luego esperamos activamente a que el contenido real aparezca en el DOM.
    """
    os.makedirs(DEBUG_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            )
        )

        page.goto(url, timeout=60000, wait_until="domcontentloaded")

        # Esperamos activamente a que el contenido real de la SPA se pinte.
        # Si en 45s no aparece suficiente texto, seguimos de todas formas:
        # guardamos evidencia (screenshot + html) para poder diagnosticar.
        contenido_cargo = True
        try:
            page.wait_for_function(
                "document.body.innerText.length > 800",
                timeout=45000,
            )
        except Exception:
            contenido_cargo = False

        # Margen extra por si hay animaciones/renderizado tardío de listas
        page.wait_for_timeout(3000)

        texto = page.inner_text("body")

        # --- Evidencia de depuración, siempre se guarda ---
        try:
            page.screenshot(path=os.path.join(DEBUG_DIR, "pagina.png"), full_page=True)
        except Exception as e:
            print(f"No se pudo tomar screenshot: {e}")

        try:
            with open(os.path.join(DEBUG_DIR, "pagina.html"), "w", encoding="utf-8") as f:
                f.write(page.content())
        except Exception as e:
            print(f"No se pudo guardar el HTML: {e}")

        with open(os.path.join(DEBUG_DIR, "texto_visible.txt"), "w", encoding="utf-8") as f:
            f.write(texto)

        if not contenido_cargo:
            print("ADVERTENCIA: el contenido tardó más de lo esperado en aparecer; "
                  "revisa debug_output/ para ver qué se alcanzó a renderizar.")

        browser.close()
        return texto


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
        # No hacemos fallback silencioso a ningún valor inventado.
        # Si el chequeo falla, el workflow debe fallar (visible en Actions),
        # NO reportar falsamente "todo al día".
        sys.exit(1)

    parches_encontrados = extraer_parches(texto)

    if not parches_encontrados:
        print(
            f"No se encontró ningún parche de la rama {RAMA} en la página renderizada. "
            "Esto puede indicar que NetApp cambió el markup del sitio, o que la "
            "página no cargó completamente."
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
