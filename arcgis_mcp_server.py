"""
arcgis_mcp_server.py — Servidor MCP para Claude Desktop
GeoSIG Ingenieros EIRL

Claude Desktop lanza este archivo. Se comunica con bridge.py
que corre dentro de ArcGIS Pro (puerto 6789).

Configurar en claude_desktop_config.json:
{
  "mcpServers": {
    "arcgis_pro": {
      "command": "C:\\...\\arcgispro-py3\\python.exe",
      "args": ["C:\\GIS\\mcp\\arcgis_mcp_server.py"]
    }
  }
}
"""

import sys
import json
import logging
import urllib.request
import urllib.error
from mcp.server.fastmcp import FastMCP

logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="[arcgis-mcp] %(message)s")
log = logging.getLogger()

BRIDGE = "http://127.0.0.1:6789"
TIMEOUT = 300  # segundos — suficiente para geoprocesos pesados

mcp = FastMCP(
    name="arcgis-pro",
    instructions=(
        "Asistente GIS conectado a ArcGIS Pro en tiempo real. "
        "Puede ejecutar geoprocesos, leer y crear capas, calcular "
        "parámetros morfométricos e hidrológicos, y redactar texto "
        "técnico para proyectos en Perú (ANA, SENAMHI, MIDAGRI). "
        "Siempre verifica las capas activas antes de operar. "
        "Usa ejecutar_arcpy para cualquier operación en el mapa."
    )
)


# ── utilidad interna ────────────────────────────────────────────────────

def _llamar_bridge(metodo: str, ruta: str, datos: dict = None) -> dict:
    """Llama al bridge HTTP dentro de ArcGIS Pro."""
    url = BRIDGE + ruta
    try:
        if metodo == "GET":
            req = urllib.request.Request(url)
        else:
            payload = json.dumps(datos or {}).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"}
            )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))

    except urllib.error.URLError:
        return {
            "ok": False,
            "error": (
                "No se pudo conectar al bridge (puerto 6789). "
                "¿Ejecutaste bridge.py en la ventana Python de ArcGIS Pro? "
                "Comando: exec(open(r'C:\\GIS\\mcp\\bridge.py').read())"
            )
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── HERRAMIENTA 1 — Estado del proyecto activo ─────────────────────────

@mcp.tool()
def estado_proyecto() -> str:
    """
    Devuelve el nombre del proyecto abierto en ArcGIS Pro,
    el mapa activo y todas las capas con su fuente de datos.
    Úsala siempre al inicio de una sesión de trabajo o cuando
    necesites saber qué hay cargado en el mapa.
    """
    ping = _llamar_bridge("GET", "/ping")
    if not ping.get("ok"):
        return f"❌ {ping.get('error')}"

    capas_resp = _llamar_bridge("GET", "/capas")
    if not capas_resp.get("ok"):
        return f"❌ {capas_resp.get('error')}"

    proyecto = ping.get("proyecto", "N/A")
    mapa = ping.get("mapa_activo", "N/A")
    capas = capas_resp.get("capas", [])

    lineas = [
        f"📁 Proyecto : {proyecto}",
        f"🗺  Mapa activo: {mapa}",
        f"📋 Capas ({len(capas)}):",
    ]
    for c in capas:
        vis = "👁" if c.get("visible") else "○"
        fuente = c.get("fuente", "")
        lineas.append(f"  {vis} {c['nombre']}  [{c.get('tipo','')}]")
        if fuente:
            lineas.append(f"      {fuente}")

    return "\n".join(lineas)


# ── HERRAMIENTA 2 — Ejecutar código ArcPy ──────────────────────────────

@mcp.tool()
def ejecutar_arcpy(codigo: str, workspace: str = "") -> str:
    """
    Ejecuta cualquier código Python/ArcPy dentro de ArcGIS Pro.

    El código tiene acceso directo a:
      - arcpy  (todas las herramientas de geoprocesamiento)
      - aprx   (arcpy.mp.ArcGISProject("CURRENT"))
      - mapa   (aprx.activeMap)

    Úsala para:
      - Crear buffers, clips, uniones, reproyecciones
      - Delimitar cuencas (Fill → FlowDir → FlowAcc → Watershed)
      - Calcular campos, crear feature classes
      - Agregar capas al mapa activo
      - Cualquier automatización con arcpy

    Parámetros:
        codigo    : Código Python a ejecutar. No incluir 'import arcpy'
                    ni definir aprx/mapa — ya están disponibles.
        workspace : Ruta opcional a GDB o carpeta para arcpy.env.workspace.
    """
    res = _llamar_bridge("POST", "/run", {
        "codigo": codigo,
        "workspace": workspace
    })

    if res.get("ok"):
        salida = res.get("salida", "").strip()
        return f"✅ Ejecutado correctamente." + (f"\n\n{salida}" if salida else "")
    else:
        msg = f"❌ Error: {res.get('error', 'desconocido')}"
        detalle = res.get("detalle", "")
        parcial = res.get("salida_parcial", "")
        if detalle:
            msg += f"\n\nTraceback:\n{detalle}"
        if parcial:
            msg += f"\n\nSalida parcial:\n{parcial}"
        return msg


# ── PUNTO DE ENTRADA ────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("Servidor MCP iniciado. Esperando conexión de Claude Desktop...")
    log.info("Bridge esperado en: %s", BRIDGE)
    mcp.run(transport="stdio")
