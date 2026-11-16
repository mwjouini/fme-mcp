"""Workspace Tools: Workspace discovery, inspection, and execution."""

from __future__ import annotations

import base64
import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from fme_mcp_ultra.core.schema import MCPToolResponse
from fme_mcp_ultra.fme.fme_form_client import fme_form_client
from fme_mcp_ultra.security.audit_log import audit_logger
from fme_mcp_ultra.security.path_guard import path_guard


def fme_discover_workspaces(directory: str | None = None, recursive: bool = True) -> dict[str, Any]:
    """Discover all FME workspace files (.fmw) in an authorised directory.

    Args:
        directory: Directory to search (defaults to current working directory).
        recursive: Whether to scan subdirectories recursively.
    """
    search_dir = path_guard.validate_path(directory or ".", must_exist=True)
    pattern = "**/*.fmw" if recursive else "*.fmw"

    workspaces = []
    for f in search_dir.glob(pattern):
        try:
            stat = f.stat()
            workspaces.append(
                {
                    "name": f.name,
                    "path": str(f.resolve()),
                    "size_bytes": stat.st_size,
                    "last_modified": stat.st_mtime,
                }
            )
        except OSError:
            continue

    audit_logger.record_event("DISCOVER_WORKSPACES", "mcp-user", "fme_discover_workspaces")
    return MCPToolResponse(
        success=True,
        data={"count": len(workspaces), "directory": str(search_dir), "workspaces": workspaces},
    ).to_dict()


def fme_get_workspace(workspace_path: str) -> dict[str, Any]:
    """Retrieve detailed inspection metadata for a local workspace (.fmw).

    Args:
        workspace_path: Path to the .fmw workspace file.
    """
    inspection = fme_form_client.inspect_workspace(workspace_path)
    audit_logger.record_event(
        "INSPECT_WORKSPACE", "mcp-user", "fme_get_workspace", {"path": workspace_path}
    )
    return MCPToolResponse(success=True, data=inspection).to_dict()


def fme_get_workspace_parameters(workspace_path: str) -> dict[str, Any]:
    """Retrieve published parameters and default values for an FME workspace.

    Args:
        workspace_path: Path to the .fmw workspace file.
    """
    inspection = fme_form_client.inspect_workspace(workspace_path)
    params = inspection.get("published_parameters", [])
    return MCPToolResponse(
        success=True,
        data={"workspace_path": workspace_path, "parameters": params},
    ).to_dict()


def fme_run_workspace(
    workspace_path: str,
    parameters: dict[str, Any] | None = None,
    log_file: str | None = None,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    """Execute an FME workspace synchronously with user-provided parameters.

    Args:
        workspace_path: Path to the .fmw workspace file.
        parameters: Key-value dictionary of published parameter overrides.
        log_file: Optional path to save the execution log file.
        timeout_seconds: Maximum execution time before aborting (default 600s).
    """
    audit_logger.record_event(
        "RUN_WORKSPACE",
        "mcp-user",
        "fme_run_workspace",
        {"path": workspace_path, "params": parameters},
    )
    result = fme_form_client.run_workspace(
        workspace_path=workspace_path,
        parameters=parameters,
        log_file=log_file,
        timeout_seconds=timeout_seconds,
    )
    return MCPToolResponse(
        success=result["success"],
        duration_seconds=result.get("duration_seconds"),
        data=result,
    ).to_dict()


def fme_compare_workspaces(workspace_a: str, workspace_b: str) -> dict[str, Any]:
    """Compare two FME workspaces to identify differences in parameters, transformers, and readers/writers.

    Args:
        workspace_a: Path to the first .fmw workspace.
        workspace_b: Path to the second .fmw workspace.
    """
    info_a = fme_form_client.inspect_workspace(workspace_a)
    info_b = fme_form_client.inspect_workspace(workspace_b)

    tf_a = {t["name"]: t["count"] for t in info_a.get("transformers", [])}
    tf_b = {t["name"]: t["count"] for t in info_b.get("transformers", [])}

    all_tfs = set(tf_a.keys()).union(set(tf_b.keys()))
    tf_diffs = []
    for tf in sorted(all_tfs):
        count_a = tf_a.get(tf, 0)
        count_b = tf_b.get(tf, 0)
        if count_a != count_b:
            tf_diffs.append(
                {"transformer": tf, "workspace_a_count": count_a, "workspace_b_count": count_b}
            )

    return MCPToolResponse(
        success=True,
        data={
            "workspace_a": workspace_a,
            "workspace_b": workspace_b,
            "transformer_differences": tf_diffs,
            "readers_a": info_a.get("readers"),
            "readers_b": info_b.get("readers"),
            "writers_a": info_a.get("writers"),
            "writers_b": info_b.get("writers"),
        },
    ).to_dict()


def fme_enrich_geolocalisation(
    source_csv: str | None = None,
    output_geoloc_xlsx: str | None = None,
    output_non_geoloc_xlsx: str | None = None,
    output_gpkg: str | None = None,
) -> dict[str, Any]:
    """Execute the enriched geolocalisation pipeline with automatic BAN geocoding and GeoPackage output.

    Cleans coordinate typos (trailing commas, non-numeric strings), geocodes un-located controls
    via the French National Base Adresse Nationale (BAN) API, and exports to Excel and GeoPackage.

    Args:
        source_csv: Path to input CSV file (defaults to configured SMAS control tracking CSV).
        output_geoloc_xlsx: Target path for geolocalised controls Excel workbook.
        output_non_geoloc_xlsx: Target path for non-geolocalised controls Excel workbook.
        output_gpkg: Target path for OGC GeoPackage point layer in EPSG:2154 (Lambert-93).
    """
    import subprocess
    import sys

    cwd = Path.cwd()
    script_candidates = [
        cwd / "run_geolocalisation_ultra.py",
        cwd / "_scratch" / "run_geolocalisation_ultra.py",
        Path(__file__).resolve().parents[4] / "run_geolocalisation_ultra.py",
    ]
    script_path = next((p for p in script_candidates if p.exists()), None)
    if not script_path:
        return MCPToolResponse(
            success=False,
            error={
                "code": "SCRIPT_NOT_FOUND",
                "message": "Enrichment script run_geolocalisation_ultra.py not found",
            },
        ).to_dict()

    python_exe = sys.executable
    cmd = [python_exe, str(script_path)]

    audit_logger.record_event("ENRICH_GEOLOCALISATION", "mcp-user", "fme_enrich_geolocalisation")
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

    return MCPToolResponse(
        success=res.returncode == 0,
        data={
            "stdout": res.stdout,
            "stderr": res.stderr if res.returncode != 0 else None,
            "geoloc_xlsx": str(output_geoloc_xlsx or (cwd / "geolocalisé.xlsx")),
            "non_geoloc_xlsx": str(output_non_geoloc_xlsx or (cwd / "non_geolocalisé.xlsx")),
            "gpkg": str(output_gpkg or (cwd / "geolocalisé.gpkg")),
        },
    ).to_dict()


def fme_diagnose() -> dict[str, Any]:
    """Run comprehensive system diagnostic for FME Form & Flow.

    Verifies installation path, licensing, Python runtime, executable availability,
    running desktop processes (FME Workbench, FME Data Inspector), and loopback bridge.
    """
    audit_logger.record_event("DIAGNOSE", "mcp-user", "fme_diagnose")
    diag = fme_form_client.diagnose()
    return MCPToolResponse(success=True, data=diag).to_dict()


def fme_open_in_workbench(workspace_path: str) -> dict[str, Any]:
    """Launch or bring to focus FME Workbench GUI with the specified workspace.

    Args:
        workspace_path: Absolute or canonical relative path to the .fmw workspace file.
    """
    audit_logger.record_event(
        "OPEN_WORKBENCH", "mcp-user", "fme_open_in_workbench", parameters={"target": workspace_path}
    )
    res = fme_form_client.open_in_workbench(workspace_path)
    return MCPToolResponse(success=res.get("success", False), data=res).to_dict()


def fme_open_in_inspector(dataset_path: str) -> dict[str, Any]:
    """Launch FME Data Inspector GUI with the specified dataset for instant map/feature inspection.

    Args:
        dataset_path: Path to dataset (.gpkg, .xlsx, .shp, .geojson, .csv).
    """
    audit_logger.record_event(
        "OPEN_INSPECTOR", "mcp-user", "fme_open_in_inspector", parameters={"target": dataset_path}
    )
    res = fme_form_client.open_in_inspector(dataset_path)
    return MCPToolResponse(success=res.get("success", False), data=res).to_dict()


def fme_inspect_canvas(workspace_path: str) -> dict[str, Any]:
    """Extract structured visual canvas graph from an FME workspace (.fmw).

    Returns transformers with (X, Y) canvas positions, feature types, port links,
    and alerts on unconnected output ports (which may cause silent data loss).

    Args:
        workspace_path: Path to the .fmw workspace file.
    """
    audit_logger.record_event(
        "INSPECT_CANVAS", "mcp-user", "fme_inspect_canvas", parameters={"target": workspace_path}
    )
    canvas = fme_form_client.inspect_canvas(workspace_path)
    if "error" in canvas:
        return MCPToolResponse(
            success=False, error={"code": "PARSE_ERROR", "message": canvas["error"]}
        ).to_dict()
    return MCPToolResponse(success=True, data=canvas).to_dict()


def fme_preview_dataset(dataset_path: str, limit: int = 10) -> dict[str, Any]:
    """Preview features and schema from any dataset produced or consumed by FME.

    Supports GeoPackage, SQLite, Microsoft Excel (.xlsx), and Delimited Text (.csv).

    Args:
        dataset_path: Path to the dataset file.
        limit: Maximum number of sample features to return (default 10).
    """
    audit_logger.record_event(
        "PREVIEW_DATASET", "mcp-user", "fme_preview_dataset", parameters={"target": dataset_path}
    )
    preview = fme_form_client.preview_dataset(dataset_path, limit=limit)
    return MCPToolResponse(success=True, data=preview).to_dict()


# ==============================================================================
# PERFORMANCE AUDIT & MARKDOWN DOCUMENTATION TOOLS
# ==============================================================================

HEAVY_TRANSFORMER_CATALOG: dict[str, dict[str, str]] = {
    "AreaOnAreaOverlayer": {
        "category": "GEOMETRIC_OVERLAY",
        "severity": "CRITICAL",
        "impact": "Computes geometric intersections across all candidate polygons (O(N*M) complexity). Can cause exponential CPU time and RAM thrashing on large datasets.",
        "recommendation": "Pre-filter geometries with BoundingBoxFilter or spatial index, or split processing into tiles with Tiler.",
    },
    "LineOnLineOverlayer": {
        "category": "GEOMETRIC_OVERLAY",
        "severity": "HIGH",
        "impact": "Calculates n-way line intersection calculations. High computational complexity on dense network layers.",
        "recommendation": "Clip network to areas of interest or dissolve non-intersecting line segments prior to overlay.",
    },
    "PointOnAreaOverlayer": {
        "category": "GEOMETRIC_OVERLAY",
        "severity": "HIGH",
        "impact": "Performs point-in-polygon spatial testing across all records without prior spatial bounds.",
        "recommendation": "Ensure area layer is spatially indexed or pre-filtered with bounding envelopes.",
    },
    "Intersector": {
        "category": "GEOMETRIC_OVERLAY",
        "severity": "HIGH",
        "impact": "Computes node intersections for all geometries simultaneously, generating massive intermediate feature counts.",
        "recommendation": "Filter null/degenerate geometries before intersecting, and prune unneeded candidate features.",
    },
    "Clipper": {
        "category": "GEOMETRIC_OVERLAY",
        "severity": "MEDIUM",
        "impact": "Geometry clipping is CPU-intensive when clipping high-vertex features against complex polygons.",
        "recommendation": "Enable clipping spatial index or pre-filter candidate features with BoundingBoxFilter.",
    },
    "Dissolver": {
        "category": "BLOCKING_ACCUMULATOR",
        "severity": "HIGH",
        "impact": "Geometry union and boundary dissolution; buffers all input features in memory before releasing output.",
        "recommendation": "Use Group-By attributes to dissolve in batches, or ensure features are pre-sorted by boundary group.",
    },
    "NeighborFinder": {
        "category": "GEOMETRIC_OVERLAY",
        "severity": "HIGH",
        "impact": "Computes nearest neighbors using quadratic distance scans across all unindexed candidates.",
        "recommendation": "Specify Maximum Distance threshold and limit maximum candidates to inspect.",
    },
    "SpatialFilter": {
        "category": "GEOMETRIC_OVERLAY",
        "severity": "MEDIUM",
        "impact": "Spatial relationship predicates (Within, Intersects, Contains). High CPU overhead on dense layers.",
        "recommendation": "Filter candidate layers with bounding envelopes before detailed topological tests.",
    },
    "SpatialRelator": {
        "category": "GEOMETRIC_OVERLAY",
        "severity": "MEDIUM",
        "impact": "Calculates topological relations between requestors and suppliers in memory.",
        "recommendation": "Limit candidates and ensure requestor layers are filtered to valid bounds.",
    },
    "Sorter": {
        "category": "BLOCKING_ACCUMULATOR",
        "severity": "HIGH",
        "impact": "BLOCKING: Holds entire feature stream in memory until translation EOF before outputting.",
        "recommendation": "Sort at the database source level (ORDER BY) or use Group-By if sorting subsets.",
    },
    "FeatureMerger": {
        "category": "BLOCKING_ACCUMULATOR",
        "severity": "HIGH",
        "impact": "BLOCKING: Buffers all supplier features in memory to join requestor features.",
        "recommendation": "Prune unneeded attributes with AttributeKeeper before joining; enable Supplier Pre-sorted if input is ordered.",
    },
    "Aggregator": {
        "category": "BLOCKING_ACCUMULATOR",
        "severity": "HIGH",
        "impact": "BLOCKING: Accumulates features to build homogeneous groups or geometry collections.",
        "recommendation": "Specify Group-By attributes and verify feature order to avoid whole-stream buffering.",
    },
    "ListBuilder": {
        "category": "BLOCKING_ACCUMULATOR",
        "severity": "MEDIUM",
        "impact": "Accumulates incoming features into in-memory attribute lists, increasing heap consumption.",
        "recommendation": "Filter unneeded features before list aggregation and remove lists as soon as processed.",
    },
    "DuplicateFilter": {
        "category": "BLOCKING_ACCUMULATOR",
        "severity": "MEDIUM",
        "impact": "Maintains an in-memory hash table of unique key signatures for the entire translation.",
        "recommendation": "Prune tested attributes; if source is ordered, use adjacent feature testing.",
    },
    "StatisticsCalculator": {
        "category": "BLOCKING_ACCUMULATOR",
        "severity": "HIGH",
        "impact": "BLOCKING: Buffers all features to compute summary statistics (mean, median, stdev, percentiles).",
        "recommendation": "Calculate aggregates directly in database query if source is SQL.",
    },
    "InlineQuerier": {
        "category": "BLOCKING_ACCUMULATOR",
        "severity": "CRITICAL",
        "impact": "BLOCKING: Serializes all incoming feature streams into a temporary SQLite database on disk/RAM.",
        "recommendation": "Replace with FeatureMerger or DatabaseJoiner to avoid SQLite dump and indexing overhead.",
    },
    "PythonCaller": {
        "category": "EXTERNAL_IO_SCRIPT",
        "severity": "MEDIUM",
        "impact": "Per-feature Python invocation; potential single-threaded execution bottleneck in CPython runtime.",
        "recommendation": "Vectorize operations or process features in batches using close() rather than input().",
    },
    "HTTPCaller": {
        "category": "EXTERNAL_IO_SCRIPT",
        "severity": "HIGH",
        "impact": "Per-feature HTTP requests. Network round-trip latency heavily throttles translation throughput.",
        "recommendation": "Batch multiple records per payload or use concurrent connections if API supports it.",
    },
    "SQLExecutor": {
        "category": "DATABASE_QUERY",
        "severity": "HIGH",
        "impact": "Per-feature database queries (N+1 query anti-pattern) causing significant network and database latency.",
        "recommendation": "Use FeatureMerger with bulk database read or DatabaseJoiner instead of per-feature queries.",
    },
    "SQLCreator": {
        "category": "DATABASE_QUERY",
        "severity": "MEDIUM",
        "impact": "Direct SQL table extraction; unindexed source tables can cause slow initial feature reading.",
        "recommendation": "Ensure source tables have indexes on filtered columns and avoid SELECT *.",
    },
}


def _clean_html_text(text: str | None) -> str:
    """Strip HTML markup and unescape entities for clean markdown."""
    if not text:
        return ""
    s = html.unescape(text)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</p>", "\n\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</div>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _parse_fmw_xml(workspace_path: Path) -> tuple[ET.Element | None, str]:
    """Resiliently extract and parse the XML root from an FME .fmw workspace file."""
    xml_lines = []
    in_workspace = False
    try:
        with open(workspace_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("#! <?xml"):
                    in_workspace = True
                if in_workspace:
                    if line.startswith("#! "):
                        xml_lines.append(line[3:])
                    elif line.startswith("#!"):
                        xml_lines.append(line[2:])
                    if line.strip() == "#! </WORKSPACE>":
                        break
        if not xml_lines:
            return None, "No #! <WORKSPACE> XML block found in file."

        raw_xml = "".join(xml_lines)

        def replace_entity(m: re.Match[str]) -> str:
            ent = m.group(1)
            if ent in ("amp", "lt", "gt", "quot", "apos") or ent.startswith("#"):
                return m.group(0)
            if ent == "space":
                return " "
            if ent == "lf":
                return "\n"
            if ent == "openparen":
                return "("
            if ent == "closeparen":
                return ")"
            return " "

        sanitized = re.sub(r"&([a-zA-Z0-9_#]+);", replace_entity, raw_xml)
        root = ET.fromstring(sanitized)  # nosec B314
        return root, ""
    except Exception as e:
        return None, f"XML parsing error: {e}"


def _extract_workspace_components(root: ET.Element) -> dict[str, Any]:
    """Extract structured components from workspace XML root."""
    transformers: list[dict[str, Any]] = []
    for t in root.findall(".//TRANSFORMER"):
        t_id = t.get("IDENTIFIER", "")
        t_type = t.get("TYPE", "")
        t_pos = t.get("POSITION", "")
        t_enabled = t.get("ENABLED", "true").lower() == "true"
        t_name = ""
        for p in t.findall("XFORM_PARM"):
            if p.get("PARM_NAME") == "XFORMER_NAME":
                t_name = p.get("PARM_VALUE", "")
        out_ports = [p.get("NAME") or "" for p in t.findall("OUTPUT_FEAT")]

        coords = None
        if t_pos:
            try:
                parts = [float(x) for x in t_pos.split()]
                if len(parts) >= 2:
                    coords = (parts[0], parts[1])
            except ValueError:
                pass

        transformers.append(
            {
                "id": t_id,
                "name": t_name or t_type,
                "type": t_type,
                "position": t_pos,
                "coords": coords,
                "enabled": t_enabled,
                "output_ports": out_ports,
                "bookmark_id": None,
            }
        )

    bookmarks: list[dict[str, Any]] = []
    for bm_node in root.findall(".//BOOKMARK"):
        bm_id = bm_node.get("IDENTIFIER", "")
        bm_name = bm_node.get("NAME", f"Bookmark {bm_id}")
        bm_desc = _clean_html_text(bm_node.get("DESCRIPTION") or "")
        bm_color = bm_node.get("PALETTE_COLOR") or bm_node.get("COLOUR") or "Default"
        contents_ids = [x.strip() for x in bm_node.get("CONTENTS", "").split() if x.strip()]
        top_left = bm_node.get("TOP_LEFT", "")
        bottom_right = bm_node.get("BOTTOM_RIGHT", "")

        bbox = None
        if top_left and bottom_right:
            try:
                tl = [float(x) for x in top_left.split()]
                br = [float(x) for x in bottom_right.split()]
                if len(tl) >= 2 and len(br) >= 2:
                    bbox = {
                        "min_x": min(tl[0], br[0]),
                        "max_x": max(tl[0], br[0]),
                        "min_y": min(tl[1], br[1]),
                        "max_y": max(tl[1], br[1]),
                    }
            except ValueError:
                pass

        bookmarks.append(
            {
                "id": bm_id,
                "name": bm_name,
                "description": bm_desc,
                "color": bm_color,
                "contents_ids": contents_ids,
                "bounding_box": bbox,
                "top_left": top_left,
                "bottom_right": bottom_right,
                "enclosed_transformers": [],
                "enclosed_annotations": [],
            }
        )

    annotations: list[dict[str, Any]] = []
    for c in root.findall(".//COMMENT"):
        c_id = c.get("IDENTIFIER", "")
        raw_text = (
            c.get("COMMENT_VALUE") or c.get("DESCRIPTION") or c.get("VALUE") or c.get("TEXT") or ""
        )
        if not raw_text:
            raw_text = "".join(c.itertext()).strip()
        clean_text = _clean_html_text(raw_text)
        pos = c.get("POSITION") or c.get("TOP_LEFT") or ""
        coords = None
        if pos:
            try:
                parts = [float(x) for x in pos.split()]
                if len(parts) >= 2:
                    coords = (parts[0], parts[1])
            except ValueError:
                pass

        annotations.append(
            {
                "id": c_id,
                "text": clean_text,
                "position": pos,
                "coords": coords,
                "bookmark_id": None,
            }
        )

    # Associate transformers & annotations with enclosing bookmarks
    for bm in bookmarks:
        c_set = set(bm["contents_ids"])
        for tr in transformers:
            if tr["id"] in c_set:
                bm["enclosed_transformers"].append(tr)
                tr["bookmark_id"] = bm["id"]
            elif tr["bookmark_id"] is None and bm["bounding_box"] and tr["coords"]:
                tx, ty = tr["coords"]
                b = bm["bounding_box"]
                if b["min_x"] <= tx <= b["max_x"] and b["min_y"] <= ty <= b["max_y"]:
                    bm["enclosed_transformers"].append(tr)
                    tr["bookmark_id"] = bm["id"]

        for ann in annotations:
            if ann["id"] in c_set:
                bm["enclosed_annotations"].append(ann)
                ann["bookmark_id"] = bm["id"]
            elif ann["bookmark_id"] is None and bm["bounding_box"] and ann["coords"]:
                ax, ay = ann["coords"]
                b = bm["bounding_box"]
                if b["min_x"] <= ax <= b["max_x"] and b["min_y"] <= ay <= b["max_y"]:
                    bm["enclosed_annotations"].append(ann)
                    ann["bookmark_id"] = bm["id"]

    links: list[dict[str, Any]] = []
    for lk in root.findall(".//FEAT_LINK"):
        links.append(
            {
                "id": lk.get("IDENTIFIER", ""),
                "source_node": lk.get("SOURCE_NODE", ""),
                "source_port": lk.get("SOURCE_PORT_DESC") or lk.get("SOURCE_PORT_NAME") or "",
                "target_node": lk.get("TARGET_NODE", ""),
                "target_port": lk.get("TARGET_PORT_DESC") or lk.get("TARGET_PORT_NAME") or "",
                "enabled": lk.get("ENABLED", "true").lower() == "true",
            }
        )

    datasets: list[dict[str, Any]] = []
    for ds in root.findall(".//DATASET"):
        role = ds.get("ROLE", "").upper()
        fmt = ds.get("FORMAT", "")
        name = ds.get("DATASET", "") or ds.get("NAME", "")
        if role or fmt:
            datasets.append({"role": role, "format": fmt, "dataset": name})

    parameters: list[dict[str, Any]] = []
    user_parms = root.find(".//USER_PARAMETERS")
    if user_parms is not None and "FORM" in user_parms.attrib:
        try:
            form_json = base64.b64decode(user_parms.attrib["FORM"]).decode("utf-8")
            data = json.loads(form_json)
            for p in data.get("parameters", []):
                parameters.append(
                    {
                        "name": p.get("name", ""),
                        "prompt": p.get("prompt", p.get("name", "")),
                        "type": p.get("type", p.get("valueType", "string")),
                        "default_value": str(p.get("defaultValue", "")),
                        "optional": not p.get("validateExistence", False),
                    }
                )
        except Exception:
            pass

    if not parameters:
        for gp in root.findall(".//GLOBAL_PARAMETER"):
            gui_line = gp.get("GUI_LINE", "")
            d_val = gp.get("DEFAULT_VALUE", "")
            tokens = gui_line.split()
            if len(tokens) >= 3 and tokens[0] == "GUI":
                p_name = tokens[2]
                parameters.append(
                    {
                        "name": p_name,
                        "prompt": p_name,
                        "type": tokens[1],
                        "default_value": d_val,
                        "optional": "OPTIONAL" in tokens[1],
                    }
                )

    return {
        "transformers": transformers,
        "bookmarks": bookmarks,
        "annotations": annotations,
        "links": links,
        "datasets": datasets,
        "parameters": parameters,
    }


def _generate_markdown_docs(
    root: ET.Element,
    workspace_path: Path,
    comp: dict[str, Any],
    include_canvas_summary: bool = True,
) -> str:
    """Generate clean, professional GitHub-flavored Markdown documentation from workspace metadata."""
    title = root.attrib.get("TITLE") or workspace_path.stem
    desc_raw = root.attrib.get("DESCRIPTION") or root.attrib.get("MARKDOWN_DESCRIPTION") or ""
    desc_clean = _clean_html_text(desc_raw)
    build = root.attrib.get("LAST_SAVE_BUILD") or root.attrib.get("FME_BUILD_NUM") or "FME Form"
    last_date = root.attrib.get("LAST_SAVE_DATE") or "Unknown"
    py_compat = root.attrib.get("PYTHON_COMPATIBILITY") or "Python 3.x"
    extents = root.attrib.get("DOC_EXTENTS") or "N/A"
    guid = root.attrib.get("FME_DOCUMENT_GUID") or ""

    transformers = comp["transformers"]
    bookmarks = comp["bookmarks"]
    annotations = comp["annotations"]
    datasets = comp["datasets"]
    parameters = comp["parameters"]
    links = comp["links"]

    readers = [d for d in datasets if d["role"] == "READER"]
    writers = [d for d in datasets if d["role"] == "WRITER"]

    lines: list[str] = [
        f"# 🗺️ FME Workspace: {title}",
        "",
        "> **Generated automatically by FME MCP Documentation Engine**  ",
        f"> Workspace: `{workspace_path.name}` | Build: `{build}` | Last Saved: `{last_date}`",
        "",
        "## 📋 Overview",
        "",
        desc_clean if desc_clean else "*No workflow description provided in workspace properties.*",
        "",
        "### Workspace Properties",
        "",
        "| Property | Value |",
        "|:---|:---|",
        f"| **File Name** | `{workspace_path.name}` |",
        f"| **Path** | `{str(workspace_path.resolve())}` |",
        f"| **FME Build** | `{build}` |",
        f"| **Python Compatibility** | `{py_compat}` |",
        f"| **Document GUID** | `{guid or 'N/A'}` |",
        f"| **Canvas Extents** | `{extents}` |",
        f"| **Total Transformers** | `{len(transformers)}` |",
        f"| **Total Bookmarks** | `{len(bookmarks)}` |",
        f"| **Total Annotations** | `{len(annotations)}` |",
        f"| **Total Datasets** | `{len(readers)} Reader(s), {len(writers)} Writer(s)` |",
        "",
    ]

    lines.extend(
        [
            "## ⚙️ Published User Parameters",
            "",
        ]
    )
    if parameters:
        lines.extend(
            [
                "| Parameter Name | Label / Prompt | Type | Default Value | Required |",
                "|:---|:---|:---|:---|:---|",
            ]
        )
        for p in parameters:
            req_str = "No" if p.get("optional") else "Yes"
            d_val = f"`{p['default_value']}`" if p.get("default_value") else "*None*"
            lines.append(f"| `{p['name']}` | {p['prompt']} | `{p['type']}` | {d_val} | {req_str} |")
        lines.append("")
    else:
        lines.extend(["*No published parameters configured in this workspace.*", ""])

    lines.extend(
        [
            "## 💾 Data Sources & Destinations",
            "",
        ]
    )
    if datasets:
        lines.extend(
            [
                "| Direction | Format | Dataset / Connection |",
                "|:---|:---|:---|",
            ]
        )
        for d in datasets:
            dir_str = "📥 Input (Reader)" if d["role"] == "READER" else "📤 Output (Writer)"
            lines.append(f"| {dir_str} | `{d['format']}` | `{d['dataset'] or 'Default'}` |")
        lines.append("")
    else:
        lines.extend(["*No explicit readers or writers declared in workspace header.*", ""])

    lines.extend(
        [
            "## 🏗️ Workflow Architecture & Bookmarks",
            "",
        ]
    )
    if bookmarks:
        for bm in bookmarks:
            lines.append(f"### 📑 Bookmark: {bm['name']}")
            lines.append("")
            if bm["description"]:
                lines.append(f"**Description:** {bm['description']}")
                lines.append("")
            lines.append(f"- **ID:** `{bm['id']}`")
            lines.append(f"- **Palette / Color:** `{bm['color']}`")
            if bm["top_left"] and bm["bottom_right"]:
                lines.append(
                    f"- **Canvas Boundaries:** `({bm['top_left']})` to `({bm['bottom_right']})`"
                )
            lines.append("")

            enclosed_tf = bm["enclosed_transformers"]
            if enclosed_tf:
                lines.append(f"#### Enclosed Transformers ({len(enclosed_tf)})")
                lines.append("")
                lines.append("| Transformer Name | Type | Status | Output Ports |")
                lines.append("|:---|:---|:---|:---|")
                for tf in enclosed_tf:
                    st = "✅ Active" if tf["enabled"] else "⏸️ Disabled"
                    ports = ", ".join(tf["output_ports"]) if tf["output_ports"] else "*None*"
                    lines.append(f"| `{tf['name']}` | `{tf['type']}` | {st} | {ports} |")
                lines.append("")
            else:
                lines.append("*No transformers enclosed in this bookmark area.*")
                lines.append("")

            enclosed_ann = bm["enclosed_annotations"]
            if enclosed_ann:
                lines.append(f"#### Bookmark Annotations ({len(enclosed_ann)})")
                lines.append("")
                for ann in enclosed_ann:
                    lines.append(f'- 💡 *"{ann["text"]}"*')
                lines.append("")
    else:
        lines.extend(["*No visual bookmarks defined on the canvas.*", ""])

    standalone_ann = [a for a in annotations if a["bookmark_id"] is None]
    lines.extend(
        [
            "## 💬 Canvas Annotations & Notes",
            "",
        ]
    )
    if standalone_ann:
        for ann in standalone_ann:
            pos_info = f" *(Position: `{ann['position']}`)*" if ann["position"] else ""
            lines.append(f"- 📌 **Annotation [ID {ann['id']}]{pos_info}:**  ")
            lines.append(f"  > {ann['text']}")
        lines.append("")
    else:
        lines.extend(["*No standalone annotations present on the canvas.*", ""])

    lines.extend(
        [
            "## 📊 Transformer Inventory & Distribution",
            "",
        ]
    )
    if transformers:
        type_counts: dict[str, list[str]] = {}
        for t in transformers:
            type_counts.setdefault(t["type"], []).append(t["name"])

        lines.append("| Transformer Type | Count | Instance Names | Heavy / Blocking |")
        lines.append("|:---|:---|:---|:---|")
        for t_type, names in sorted(type_counts.items(), key=lambda x: -len(x[1])):
            heavy_meta = HEAVY_TRANSFORMER_CATALOG.get(t_type)
            if heavy_meta:
                heavy_badge = f"⚠️ {heavy_meta['category']} ({heavy_meta['severity']})"
            else:
                heavy_badge = "Standard"
            names_str = ", ".join(f"`{n}`" for n in names)
            lines.append(f"| `{t_type}` | {len(names)} | {names_str} | {heavy_badge} |")
        lines.append("")
    else:
        lines.extend(["*No transformers found in workspace.*", ""])

    if include_canvas_summary:
        lines.extend(
            [
                "## 🔗 Canvas Connectivity Graph",
                "",
                f"- **Total Feature Links:** `{len(links)}`",
                f"- **Active Connections:** `{len([lk for lk in links if lk.get('enabled', True)])}`",
                "",
            ]
        )

    return "\n".join(lines)


def fme_audit_performance(workspace_path: str, strict_mode: bool = False) -> dict[str, Any]:
    """Audit an FME workspace (.fmw) for performance bottlenecks, heavy transformers, and unindexed inputs.

    Identifies blocking operations (Sorter, Dissolver, FeatureMerger), quadratic spatial overlays
    (AreaOnAreaOverlayer, LineOnLineOverlayer), unconnected error/rejected ports, and unindexed
    spatial or database table readers. Computes a standardized 0-100 performance score and generates
    prioritized optimization recommendations.

    Args:
        workspace_path: Path to the .fmw workspace file.
        strict_mode: If True, applies stricter penalties for warnings and missing indexes.

    Returns:
        MCPToolResponse dict containing score, rating, bottlenecks, heavy transformers, and recommendations.
    """
    validated_path = path_guard.validate_path(workspace_path, must_exist=True)
    root, err = _parse_fmw_xml(validated_path)
    if not root:
        return MCPToolResponse(
            success=False, error={"code": "PARSE_ERROR", "message": err}
        ).to_dict()

    comp = _extract_workspace_components(root)
    transformers = comp["transformers"]
    links = comp["links"]
    datasets = comp["datasets"]

    heavy_found: list[dict[str, Any]] = []
    blocking_found: list[dict[str, Any]] = []

    for t in transformers:
        t_type = t["type"]
        if t_type in HEAVY_TRANSFORMER_CATALOG:
            meta = HEAVY_TRANSFORMER_CATALOG[t_type]
            entry = {
                "id": t["id"],
                "name": t["name"],
                "type": t_type,
                "category": meta["category"],
                "severity": meta["severity"],
                "impact": meta["impact"],
                "recommendation": meta["recommendation"],
            }
            heavy_found.append(entry)
            if meta["category"] == "BLOCKING_ACCUMULATOR":
                blocking_found.append(entry)

    bottlenecks: list[dict[str, Any]] = []
    recommendations: list[str] = []

    # 1. Chained blocking pipeline
    if len(blocking_found) >= 2:
        names = ", ".join(t["name"] for t in blocking_found)
        bottlenecks.append(
            {
                "type": "CHAINED_BLOCKING_PIPELINE",
                "severity": "CRITICAL",
                "title": f"Chained Blocking Pipeline ({len(blocking_found)} barriers)",
                "description": f"Multiple stream-blocking transformers ({names}) exist in the workflow. Each accumulates feature batches in memory, halting pipelined feature streaming.",
                "recommendation": "Restructure workflow to minimize blocking points; combine transformations or push grouping/sorting to source database.",
            }
        )
        recommendations.append(
            f"Reduce stream-blocking barriers: {names} force full-dataset buffering."
        )

    # 2. Unconnected error / rejected ports
    connected_ports: dict[str, set[str]] = {}
    for lk in links:
        src_node = lk["source_node"]
        src_port = lk["source_port"].upper()
        connected_ports.setdefault(src_node, set()).add(src_port)

    risky_port_names = {
        "REJECTED",
        "<REJECTED>",
        "FAILED",
        "<FAILED>",
        "UNMERGED_REQUESTOR",
        "UNMERGED_SUPPLIER",
        "<UNREFERENCED>",
    }
    unconnected_rejected: list[dict[str, str]] = []
    for t in transformers:
        c_ports = connected_ports.get(t["id"], set()).union(connected_ports.get(t["name"], set()))
        for p in t["output_ports"]:
            p_clean = p.strip()
            if p_clean.upper() in risky_port_names and p_clean.upper() not in c_ports:
                unconnected_rejected.append(
                    {"transformer": t["name"], "port": p_clean, "type": t["type"]}
                )

    if unconnected_rejected:
        sample_txt = ", ".join(f"{u['transformer']}.{u['port']}" for u in unconnected_rejected[:4])
        bottlenecks.append(
            {
                "type": "UNCONNECTED_REJECTED_PORTS",
                "severity": "HIGH",
                "title": f"Unconnected Error/Rejected Ports ({len(unconnected_rejected)})",
                "description": f"Output ports for failed/rejected features are unconnected ({sample_txt}). Rejected records will be silently dropped without logging or failure notifications.",
                "recommendation": "Connect rejected ports to a Logger, Inspector, or Terminator to capture data rejections.",
            }
        )
        recommendations.append(
            f"Connect rejected ports ({sample_txt}) to a Logger or Terminator to prevent silent data loss."
        )

    # 3. Production debugging overhead
    caching_enabled = root.attrib.get("ENABLE_DATA_CACHING", "No").lower() == "yes"
    if caching_enabled:
        bottlenecks.append(
            {
                "type": "FEATURE_CACHING_ENABLED",
                "severity": "LOW",
                "title": "Feature Caching Enabled",
                "description": "ENABLE_DATA_CACHING is set to Yes. While helpful in development, caching adds disk serialization overhead in production executions.",
                "recommendation": "Disable Feature Caching in Workspace Parameters prior to production batch runs.",
            }
        )
        recommendations.append(
            "Disable feature caching (ENABLE_DATA_CACHING='No') for production batch runs."
        )

    inspectors = [t for t in transformers if t["type"] in ("Inspector", "Visualizer")]
    if inspectors:
        names = ", ".join(t["name"] for t in inspectors)
        bottlenecks.append(
            {
                "type": "DEBUG_TRANSFORMERS_PRESENT",
                "severity": "MEDIUM",
                "title": f"Active GUI Inspectors Found ({len(inspectors)})",
                "description": f"GUI Inspector transformers ({names}) remain in the workspace canvas. In automated runs, these can cause process stalls.",
                "recommendation": "Disable or remove Inspector transformers before scheduled automation.",
            }
        )
        recommendations.append(
            f"Remove or disable Inspector transformers ({names}) for headless automated runs."
        )

    # 4. Unindexed inputs
    unindexed_inputs: list[dict[str, Any]] = []
    spatial_db_formats = {
        "POSTGIS",
        "POSTGRESQL",
        "ORACLE8I",
        "ORACLE_SPATIAL",
        "ORACLE",
        "GEOPACKAGE",
        "SQLITE3",
        "SHAPEFILE",
        "MSSQL_SPATIAL",
        "SDF3",
        "WFS",
    }
    for ds in datasets:
        if ds["role"] == "READER":
            fmt_upper = ds["format"].upper()
            if fmt_upper in spatial_db_formats:
                unindexed_inputs.append(
                    {
                        "dataset": ds["dataset"],
                        "format": ds["format"],
                        "role": "READER",
                        "severity": "HIGH",
                        "issue": "Spatial/Database table reader without verified WHERE clause or spatial bounding box constraint",
                        "recommendation": f"Add WHERE clause or SEARCH_ENVELOPE bounding box on reader '{ds['format']}' to avoid full table scans.",
                    }
                )
                recommendations.append(
                    f"Configure reader envelope/WHERE clause on '{ds['format']}' to avoid table scans."
                )
            elif fmt_upper in ("CSV", "CSV2", "TEXTLINE"):
                unindexed_inputs.append(
                    {
                        "dataset": ds["dataset"],
                        "format": ds["format"],
                        "role": "READER",
                        "severity": "LOW",
                        "issue": "Flat delimited text input does not support spatial indexing or source-level filtering",
                        "recommendation": "For large text files (>100k records), consider pre-filtering with DuckDB/SQLite or loading into GeoPackage.",
                    }
                )

    for h in heavy_found:
        recommendations.append(f"[{h['type']} - {h['name']}]: {h['recommendation']}")

    # Calculate Score
    deductions = 0
    severity_weights = {
        "CRITICAL": 15,
        "HIGH": 8,
        "MEDIUM": 4,
        "LOW": 2,
    }
    if strict_mode:
        severity_weights = {"CRITICAL": 20, "HIGH": 12, "MEDIUM": 6, "LOW": 3}

    for h in heavy_found:
        deductions += severity_weights.get(h["severity"], 4)
    for b in bottlenecks:
        deductions += severity_weights.get(b["severity"], 4)
    for u in unindexed_inputs:
        deductions += severity_weights.get(u["severity"], 3)

    score = max(10, min(100, 100 - deductions))
    if score >= 90:
        rating = "EXCELLENT"
    elif score >= 75:
        rating = "GOOD"
    elif score >= 55:
        rating = "FAIR"
    else:
        rating = "POOR - NEEDS_OPTIMIZATION"

    seen_recs = set()
    unique_recs = []
    for r in recommendations:
        if r not in seen_recs:
            seen_recs.add(r)
            unique_recs.append(r)

    audit_logger.record_event(
        "AUDIT_PERFORMANCE", "mcp-user", "fme_audit_performance", {"path": workspace_path}
    )

    return MCPToolResponse(
        success=True,
        data={
            "workspace_path": str(validated_path),
            "workspace_name": validated_path.name,
            "performance_score": score,
            "rating": rating,
            "summary": {
                "total_transformers": len(transformers),
                "heavy_transformers_count": len(heavy_found),
                "blocking_transformers_count": len(blocking_found),
                "bottlenecks_count": len(bottlenecks),
                "unindexed_inputs_count": len(unindexed_inputs),
                "unconnected_rejected_count": len(unconnected_rejected),
            },
            "heavy_transformers": heavy_found,
            "bottlenecks": bottlenecks,
            "unindexed_inputs": unindexed_inputs,
            "recommendations": unique_recs,
            "audit_flags": {
                "caching_enabled": caching_enabled,
                "strict_mode": strict_mode,
            },
        },
    ).to_dict()


def fme_export_markdown_docs(
    workspace_path: str,
    output_file: str | None = None,
    include_canvas_summary: bool = True,
) -> dict[str, Any]:
    """Generate clean, comprehensive markdown documentation from an FME workspace (.fmw).

    Extracts canvas bookmarks, developer annotations, published parameters, readers/writers,
    and transformer hierarchies into structured GitHub-flavored Markdown.

    Args:
        workspace_path: Path to the .fmw workspace file.
        output_file: Optional file path to save the generated markdown file.
        include_canvas_summary: Whether to include canvas link connectivity stats.

    Returns:
        MCPToolResponse dict with markdown content, component stats, and export path.
    """
    validated_path = path_guard.validate_path(workspace_path, must_exist=True)
    root, err = _parse_fmw_xml(validated_path)
    if not root:
        return MCPToolResponse(
            success=False, error={"code": "PARSE_ERROR", "message": err}
        ).to_dict()

    comp = _extract_workspace_components(root)
    markdown_content = _generate_markdown_docs(
        root=root,
        workspace_path=validated_path,
        comp=comp,
        include_canvas_summary=include_canvas_summary,
    )

    out_path_str: str | None = None
    if output_file:
        out_path = path_guard.validate_path(output_file)
        out_path.write_text(markdown_content, encoding="utf-8")
        out_path_str = str(out_path.resolve())

    audit_logger.record_event(
        "EXPORT_MARKDOWN_DOCS",
        "mcp-user",
        "fme_export_markdown_docs",
        {"path": str(validated_path), "output": out_path_str},
    )

    return MCPToolResponse(
        success=True,
        data={
            "workspace_path": str(validated_path),
            "workspace_name": validated_path.name,
            "output_file": out_path_str,
            "markdown": markdown_content,
            "stats": {
                "total_bookmarks": len(comp["bookmarks"]),
                "total_annotations": len(comp["annotations"]),
                "total_transformers": len(comp["transformers"]),
                "total_parameters": len(comp["parameters"]),
                "total_datasets": len(comp["datasets"]),
                "total_links": len(comp["links"]),
            },
            "bookmarks": [
                {
                    "id": b["id"],
                    "name": b["name"],
                    "description": b["description"],
                    "color": b["color"],
                    "enclosed_transformers": [t["name"] for t in b["enclosed_transformers"]],
                    "enclosed_annotations": [a["text"] for a in b["enclosed_annotations"]],
                }
                for b in comp["bookmarks"]
            ],
            "annotations": [
                {
                    "id": a["id"],
                    "text": a["text"],
                    "bookmark_id": a["bookmark_id"],
                }
                for a in comp["annotations"]
            ],
        },
    ).to_dict()
