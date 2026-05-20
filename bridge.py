"""
bridge.py — Servidor interno para ArcGIS Pro
GeoSIG Ingenieros EIRL

CÓMO USAR: en la ventana Python de ArcGIS Pro, ejecutar:
    exec(open(r"C:\GIS\mcp\bridge.py").read())

Corre en segundo plano. No bloquea ArcGIS Pro.
Puerto: 6789
"""

import threading
import json
import io
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler


class _Handler(BaseHTTPRequestHandler):

    # ── silenciar logs del servidor HTTP en la consola de ArcGIS Pro ──
    def log_message(self, format, *args):
        pass

    def _responder(self, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _leer_body(self) -> dict:
        largo = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(largo)) if largo else {}

    # ── GET /ping  ─────────────────────────────────────────────────────
    def do_GET(self):
        if self.path == "/ping":
            try:
                aprx = arcpy.mp.ArcGISProject("CURRENT")
                mapa = aprx.activeMap
                self._responder({
                    "ok": True,
                    "proyecto": aprx.filePath,
                    "mapa_activo": mapa.name if mapa else None,
                })
            except Exception as e:
                self._responder({"ok": False, "error": str(e)})

        elif self.path == "/capas":
            try:
                aprx = arcpy.mp.ArcGISProject("CURRENT")
                mapa = aprx.activeMap
                capas = []
                if mapa:
                    for lyr in mapa.listLayers():
                        info = {
                            "nombre": lyr.name,
                            "visible": lyr.visible,
                            "tipo": lyr.type if hasattr(lyr, "type") else "N/A",
                        }
                        if lyr.supports("DATASOURCE"):
                            info["fuente"] = lyr.dataSource
                        capas.append(info)
                self._responder({"ok": True, "mapa": mapa.name if mapa else None, "capas": capas})
            except Exception as e:
                self._responder({"ok": False, "error": str(e)})

        else:
            self.send_response(404)
            self.end_headers()

    # ── POST /run  ─────────────────────────────────────────────────────
    def do_POST(self):
        if self.path != "/run":
            self.send_response(404)
            self.end_headers()
            return

        body = self._leer_body()
        codigo = body.get("codigo", "").strip()
        if not codigo:
            self._responder({"ok": False, "error": "Sin código"})
            return

        # Namespace: arcpy disponible + proyecto y mapa activos frescos
        preambulo = (
            "import arcpy, os, sys, json, math\n"
            "arcpy.env.overwriteOutput = True\n"
            "aprx = arcpy.mp.ArcGISProject('CURRENT')\n"
            "mapa = aprx.activeMap\n"
        )

        # Workspace opcional
        workspace = body.get("workspace", "")
        if workspace:
            preambulo += f'arcpy.env.workspace = r"{workspace}"\n'

        codigo_final = preambulo + "\n" + codigo

        # Capturar stdout
        buf = io.StringIO()
        sys_stdout_orig = sys.stdout
        sys.stdout = buf

        try:
            exec(compile(codigo_final, "<mcp>", "exec"), {
                "arcpy": arcpy,
                "__builtins__": __builtins__,
            })
            salida = buf.getvalue()
            self._responder({"ok": True, "salida": salida})

        except Exception as exc:
            import traceback
            self._responder({
                "ok": False,
                "error": str(exc),
                "detalle": traceback.format_exc(),
                "salida_parcial": buf.getvalue(),
            })
        finally:
            sys.stdout = sys_stdout_orig


def _iniciar_servidor(puerto=6789):
    servidor = HTTPServer(("127.0.0.1", puerto), _Handler)
    servidor.serve_forever()


# ── Arrancar en hilo de fondo ───────────────────────────────────────────
_hilo = threading.Thread(target=_iniciar_servidor, daemon=True)
_hilo.start()

print(f"✅ ArcGIS MCP Bridge corriendo en http://127.0.0.1:6789")
print(f"   Proyecto activo: {arcpy.mp.ArcGISProject('CURRENT').filePath}")
print(f"   Ahora abre Claude Desktop y empieza a chatear.")
