# ArcGIS Pro MCP Server

Connect **Claude Desktop** directly to **ArcGIS Pro** using the [Model Context Protocol (MCP)](https://modelcontextprotocol.io). Execute geoprocessing tasks, read active map layers, and run ArcPy code — all from a natural language chat interface, with no paid plugins required.

![Python](https://img.shields.io/badge/Python-arcgispro--py3-blue)
![ArcGIS Pro](https://img.shields.io/badge/ArcGIS%20Pro-3.x-green)
![Claude](https://img.shields.io/badge/Claude-Desktop-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## How It Works

```
ArcGIS Pro (open project)
  └── Python Window → exec(bridge.py)
      └── HTTP server on port 6789 ← has access to active map ("CURRENT")

Claude Desktop
  └── launches arcgis_mcp_server.py (MCP server)
      └── communicates with bridge via HTTP
          └── you chat in natural language → Claude runs geoprocesses
```

Two files. No add-ins. No paid plugins.

---

## Requirements

- ArcGIS Pro 3.x with a valid license
- Claude Desktop (Windows) — [download here](https://claude.ai/download)
- Claude Pro or Max subscription (required for MCP support)
- `mcp` Python package installed in `arcgispro-py3`

---

## Installation

### 1. Copy files

Create the folder `C:\GIS\mcp\` and place both files there:

```
C:\GIS\mcp\
    bridge.py
    arcgis_mcp_server.py
```

### 2. Install the `mcp` package

Open the **ArcGIS Pro Python Command Prompt**
(Start → ArcGIS → Python Command Prompt) and run:

```cmd
pip install mcp
```

Find your exact Python path (you'll need it in the next step):

```cmd
where python
```

It should look like:
```
C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe
```

### 3. Configure Claude Desktop

Open or create the file:
```
%APPDATA%\Claude\claude_desktop_config.json
```

Add the `mcpServers` block (adjust the Python path to match yours):

```json
{
  "mcpServers": {
    "arcgis_pro": {
      "command": "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3\\python.exe",
      "args": ["C:\\GIS\\mcp\\arcgis_mcp_server.py"]
    }
  }
}
```

> If you already have other MCP servers configured, add only the `"arcgis_pro"` block inside the existing `"mcpServers"` object.

Fully close Claude Desktop (Task Manager → End task), then reopen it.

Go to **Settings → Developer** — you should see `arcgis_pro` with a green **running** badge.

### 4. Start the bridge inside ArcGIS Pro

Every time you open ArcGIS Pro and want to use Claude:

1. Open your project
2. Open the Python Window: **View → Python Window**
3. Run this line:

```python
exec(open(r"C:\GIS\mcp\bridge.py").read())
```

You should see:
```
✅ ArcGIS MCP Bridge running on http://127.0.0.1:6789
   Project: D:\MyProject\MyProject.aprx
   Map: Map
   Now open Claude Desktop and start chatting.
```

---

## Usage Examples

Once connected, open a new chat in Claude Desktop and try:

```
What layers do I have in my active map?
```

```
Create a 500-meter buffer around the layer Red_Hidrica
and add the result to the map.
```

```
Delineate the watershed from DEM_ALOS using the outlet point
at UTM 18S coordinates: Easting 671450, Northing 8498220.
```

```
Calculate the Gravelius compactness coefficient for all
polygons in the Subcuencas layer and print the results.
```

```
Generate a Python script that calculates Kc, Rc, and Dd
for all sub-watersheds and exports the results to Excel.
```

---

## Available MCP Tools

| Tool | Description |
|---|---|
| `estado_proyecto` | Returns the active project path, active map name, and all layers with their data sources |
| `ejecutar_arcpy` | Executes any Python/ArcPy code inside ArcGIS Pro with access to the active project and map |

The `ejecutar_arcpy` tool has direct access to:
- `arcpy` — full geoprocessing library
- `aprx` — the active ArcGIS Pro project
- `mapa` — the active map

---

## Why No Add-in?

ArcGeek Tools offers a similar MCP connection as part of a paid toolbox ($35/year). This project replicates **only that connection functionality** using a lightweight bridge script — no add-in installation, no external dependencies beyond the `mcp` package.

The trade-off: you run one line in the Python Window at the start of each session instead of clicking a button in the ribbon.

---

## Troubleshooting

**Claude doesn't see the server (not shown in Developer settings)**
- Verify the JSON in `claude_desktop_config.json` is valid (no trailing commas)
- Close all Claude processes via Task Manager before reopening

**`No module named 'mcp'`**
- Run `pip install mcp` in the ArcGIS Pro Python Command Prompt (not a regular terminal)

**`Error: CURRENT` when running tools**
- Make sure you ran `bridge.py` from the ArcGIS Pro Python Window with a project already open
- The bridge must be started after the project is loaded

**Tool executes but no output**
- Use `print()` in your code to return results to Claude
- Example: `print(arcpy.management.GetCount("MyLayer")[0])`

---

## Project Structure

```
arcgis-pro-mcp-server/
│
├── bridge.py               # Runs inside ArcGIS Pro Python Window
│                           # Starts HTTP server on port 6789
│                           # Has access to active project and map
│
├── arcgis_mcp_server.py    # Launched by Claude Desktop as MCP server
│                           # Communicates with bridge via HTTP
│                           # Exposes tools to Claude
│
└── README.md
```

---

## Extending the Server

Add custom tools using the `@mcp.tool()` decorator in `arcgis_mcp_server.py`:

```python
@mcp.tool()
def mi_herramienta(parametro: str) -> str:
    """Description Claude will read to decide when to use this tool."""
    res = _llamar_bridge("POST", "/run", {
        "codigo": f'print("Processing: {parametro}")'
    })
    return res.get("salida", res.get("error", "No output"))
```

---

## Use Cases

This setup is particularly useful for:

- **Hydrological analysis** — watershed delineation, flow accumulation, IDF curves
- **Morphometric calculations** — Gravelius coefficient, drainage density, form factor
- **Soil mapping** — attribute calculation, cartographic unit classification
- **Technical reports** — generating descriptive text for GIS project documentation
- **ArcPy automation** — generating and running scripts from natural language

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

## Español

### ¿Qué es esto?

Un servidor MCP que conecta **Claude Desktop** con **ArcGIS Pro** sin plugins de pago. Permite ejecutar geoprocesos, leer capas del mapa activo y correr código ArcPy directamente desde el chat, en lenguaje natural.

### Instalación rápida

1. Copiar `bridge.py` y `arcgis_mcp_server.py` a `C:\GIS\mcp\`
2. Instalar el paquete: `pip install mcp` (en Python Command Prompt de ArcGIS Pro)
3. Configurar `%APPDATA%\Claude\claude_desktop_config.json` con la ruta a tu `python.exe`
4. En cada sesión, ejecutar en la ventana Python de ArcGIS Pro:
   ```python
   exec(open(r"C:\GIS\mcp\bridge.py").read())
   ```

### Desarrollado por

[GeoSIG Ingenieros EIRL](https://geosigingenieros.com.pe) — Ayacucho, Perú  
Especialistas en GIS, hidrología, morfometría y cartografía para entidades públicas en Perú.
