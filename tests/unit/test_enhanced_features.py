"""Unit tests covering enhanced GIS spatial tools and advanced workspace tools."""

from pathlib import Path

import pytest

from fme_mcp.tools.spatial.spatial_tools import (
    GISBoundingBoxRequest,
    GISDifferenceRequest,
    GISIntersectionRequest,
    GISSimplifyRequest,
    gis_bounding_box,
    gis_difference,
    gis_intersection,
    gis_simplify,
)
from fme_mcp.tools.workspaces.workspace_tools import (
    fme_audit_performance,
    fme_export_markdown_docs,
)

# ==============================================================================
# SPATIAL TOOLS TESTS: gis_intersection
# ==============================================================================


def test_gis_intersection_overlapping_polygons():
    """Verify intersection of two overlapping polygons returns overlapping area and geometry."""
    poly1 = {
        "type": "Polygon",
        "coordinates": [[[0.0, 0.0], [4.0, 0.0], [4.0, 4.0], [0.0, 4.0], [0.0, 0.0]]],
    }
    poly2 = {
        "type": "Polygon",
        "coordinates": [[[2.0, 2.0], [6.0, 2.0], [6.0, 6.0], [2.0, 6.0], [2.0, 2.0]]],
    }

    res = gis_intersection(geom1=poly1, geom2=poly2)
    assert res["success"] is True
    data = res["data"]
    assert data["intersects"] is True
    assert data["is_empty"] is False
    assert data["area"] == pytest.approx(4.0, rel=1e-3)
    assert data["geometry_type"] == "Polygon"
    assert data["geometry"] is not None
    assert "coordinates" in data["geometry"]


def test_gis_intersection_disjoint_polygons():
    """Verify disjoint polygons return intersects=False, is_empty=True, and area=0."""
    poly1 = {
        "type": "Polygon",
        "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]],
    }
    poly2 = {
        "type": "Polygon",
        "coordinates": [[[5.0, 5.0], [6.0, 5.0], [6.0, 6.0], [5.0, 6.0], [5.0, 5.0]]],
    }

    res = gis_intersection(geom1=poly1, geom2=poly2)
    assert res["success"] is True
    data = res["data"]
    assert data["intersects"] is False
    assert data["is_empty"] is True
    assert data["area"] == 0.0
    assert data["geometry"] is None


def test_gis_intersection_with_pydantic_request():
    """Verify gis_intersection works seamlessly when passing a GISIntersectionRequest instance."""
    wkt1 = "POLYGON ((0 0, 10 0, 10 10, 0 10, 0 0))"
    wkt2 = "POLYGON ((5 5, 15 5, 15 15, 5 15, 5 5))"

    req = GISIntersectionRequest(geom1=wkt1, geom2=wkt2, engine="auto")
    res = gis_intersection(req)
    assert res["success"] is True
    assert res["data"]["intersects"] is True
    assert res["data"]["area"] == pytest.approx(25.0, rel=1e-3)
    assert "shapely" in res["data"]["engine_used"]


def test_gis_intersection_wkt_strings_and_engine_selection():
    """Verify WKT strings and engine selection parameter."""
    wkt1 = "POLYGON ((0 0, 5 0, 5 5, 0 5, 0 0))"
    wkt2 = "POLYGON ((1 1, 3 1, 3 3, 1 3, 1 1))"

    res = gis_intersection(geom1=wkt1, geom2=wkt2, engine="fme")
    assert res["success"] is True
    assert res["data"]["intersects"] is True
    assert res["data"]["area"] == pytest.approx(4.0, rel=1e-3)
    assert "fme" in res["data"]["engine_used"]


def test_gis_intersection_error_handling():
    """Verify graceful error reporting for missing arguments or invalid geometry."""
    res_missing = gis_intersection(geom1=None, geom2=None)
    assert res_missing["success"] is False
    assert res_missing["error"]["code"] == "MISSING_ARGUMENTS"

    res_invalid = gis_intersection(geom1="INVALID_WKT", geom2="POLYGON ((0 0, 1 1))")
    assert res_invalid["success"] is False
    assert res_invalid["error"]["code"] == "INVALID_GEOMETRY"


# ==============================================================================
# SPATIAL TOOLS TESTS: gis_difference
# ==============================================================================


def test_gis_difference_overlapping_polygons():
    """Verify difference removes overlapping region of geom2 from geom1."""
    poly1 = {
        "type": "Polygon",
        "coordinates": [[[0.0, 0.0], [4.0, 0.0], [4.0, 4.0], [0.0, 4.0], [0.0, 0.0]]],  # area = 16
    }
    poly2 = {
        "type": "Polygon",
        "coordinates": [[[2.0, 0.0], [4.0, 0.0], [4.0, 4.0], [2.0, 4.0], [2.0, 0.0]]],  # area = 8
    }

    res = gis_difference(geom1=poly1, geom2=poly2)
    assert res["success"] is True
    data = res["data"]
    assert data["is_empty"] is False
    assert data["area"] == pytest.approx(8.0, rel=1e-3)
    assert data["geometry_type"] == "Polygon"


def test_gis_difference_total_subtraction():
    """Verify total subtraction (geom1 fully inside geom2) results in empty geometry."""
    poly1 = {
        "type": "Polygon",
        "coordinates": [[[2.0, 2.0], [3.0, 2.0], [3.0, 3.0], [2.0, 3.0], [2.0, 2.0]]],
    }
    poly2 = {
        "type": "Polygon",
        "coordinates": [[[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]]],
    }

    res = gis_difference(geom1=poly1, geom2=poly2)
    assert res["success"] is True
    data = res["data"]
    assert data["is_empty"] is True
    assert data["geometry"] is None
    assert data["area"] == 0.0


def test_gis_difference_with_pydantic_request_and_wkt():
    """Verify gis_difference works with GISDifferenceRequest and WKT inputs."""
    wkt1 = "POLYGON ((0 0, 6 0, 6 6, 0 6, 0 0))"  # area = 36
    wkt2 = "POLYGON ((0 0, 3 0, 3 6, 0 6, 0 0))"  # area = 18

    req = GISDifferenceRequest(geom1=wkt1, geom2=wkt2, engine="auto")
    res = gis_difference(req)
    assert res["success"] is True
    assert res["data"]["area"] == pytest.approx(18.0, rel=1e-3)
    assert res["data"]["is_empty"] is False


def test_gis_difference_error_handling():
    """Verify error reporting when geometries are omitted or corrupt."""
    res = gis_difference(geom1=None)
    assert res["success"] is False
    assert res["error"]["code"] == "MISSING_ARGUMENTS"

    res_corrupt = gis_difference(geom1={"type": "InvalidType"}, geom2={"type": "Point"})
    assert res_corrupt["success"] is False
    assert res_corrupt["error"]["code"] == "INVALID_GEOMETRY"


# ==============================================================================
# SPATIAL TOOLS TESTS: gis_simplify
# ==============================================================================


def test_gis_simplify_reduces_collinear_vertices():
    """Verify Douglas-Peucker simplification reduces redundant vertices on a LineString."""
    # LineString along y=0 with minor deviations
    coords = [
        [0.0, 0.0],
        [1.0, 0.001],
        [2.0, -0.001],
        [3.0, 0.002],
        [4.0, 0.0],
        [5.0, 0.0],
    ]
    geom = {"type": "LineString", "coordinates": coords}

    res = gis_simplify(geometry=geom, tolerance=0.1, preserve_topology=True)
    assert res["success"] is True
    data = res["data"]
    assert data["original_vertices"] == 6
    assert data["simplified_vertices"] < 6
    assert data["reduction_ratio"] > 0.0
    assert data["geometry"]["type"] == "LineString"


def test_gis_simplify_zero_tolerance_preserves_vertices():
    """Verify tolerance=0.0 preserves all vertices."""
    coords = [[0.0, 0.0], [1.0, 1.0], [2.0, 0.0], [3.0, 1.0]]
    geom = {"type": "LineString", "coordinates": coords}

    res = gis_simplify(geometry=geom, tolerance=0.0)
    assert res["success"] is True
    assert res["data"]["original_vertices"] == res["data"]["simplified_vertices"]
    assert res["data"]["reduction_ratio"] == 0.0


def test_gis_simplify_with_pydantic_request_and_polygon():
    """Verify gis_simplify accepts a GISSimplifyRequest with a Polygon."""
    poly = {
        "type": "Polygon",
        "coordinates": [
            [
                [0.0, 0.0],
                [1.0, 0.001],
                [2.0, 0.0],
                [2.0, 2.0],
                [1.0, 2.001],
                [0.0, 2.0],
                [0.0, 0.0],
            ]
        ],
    }
    req = GISSimplifyRequest(geometry=poly, tolerance=0.05, preserve_topology=True, engine="fme")
    res = gis_simplify(req)
    assert res["success"] is True
    assert res["data"]["original_vertices"] == 7
    assert res["data"]["simplified_vertices"] == 5
    assert res["data"]["reduction_ratio"] > 0.2
    assert "fme" in res["data"]["engine_used"]


def test_gis_simplify_error_handling():
    """Verify error reporting on missing geometry or invalid tolerance."""
    res_missing = gis_simplify(geometry=None)
    assert res_missing["success"] is False
    assert res_missing["error"]["code"] == "MISSING_ARGUMENTS"

    # Negative tolerance should trigger Pydantic validation error
    res_neg = gis_simplify(geometry={"type": "Point", "coordinates": [0, 0]}, tolerance=-1.0)
    assert res_neg["success"] is False
    assert res_neg["error"]["code"] == "VALIDATION_ERROR"


# ==============================================================================
# SPATIAL TOOLS TESTS: gis_bounding_box
# ==============================================================================


def test_gis_bounding_box_from_geojson_polygon():
    """Verify bbox calculation for a GeoJSON Polygon."""
    poly = {
        "type": "Polygon",
        "coordinates": [[[10.0, 20.0], [30.0, 20.0], [30.0, 50.0], [10.0, 50.0], [10.0, 20.0]]],
    }
    res = gis_bounding_box(geometry=poly)
    assert res["success"] is True
    data = res["data"]
    assert data["minx"] == 10.0
    assert data["miny"] == 20.0
    assert data["maxx"] == 30.0
    assert data["maxy"] == 50.0
    assert data["width"] == 20.0
    assert data["height"] == 30.0
    assert data["area"] == 600.0
    assert data["center"] == [20.0, 35.0]
    assert data["bbox"] == [10.0, 20.0, 30.0, 50.0]
    # Check 5-point bounding box polygon
    box_geom = data["geometry"]
    assert box_geom["type"] == "Polygon"
    assert len(box_geom["coordinates"][0]) == 5


def test_gis_bounding_box_from_coordinate_list():
    """Verify bbox calculation from raw coordinate list."""
    coords = [[2.35, 48.85], [2.40, 48.90], [2.30, 48.80]]
    res = gis_bounding_box(geometry=coords)
    assert res["success"] is True
    data = res["data"]
    assert data["minx"] == 2.30
    assert data["maxx"] == 2.40
    assert data["miny"] == 48.80
    assert data["maxy"] == 48.90


def test_gis_bounding_box_from_4_element_array():
    """Verify bbox calculation when passing an existing [minx, miny, maxx, maxy] array."""
    bbox_in = [5.0, 10.0, 25.0, 40.0]
    res = gis_bounding_box(geometry=bbox_in)
    assert res["success"] is True
    data = res["data"]
    assert data["minx"] == 5.0
    assert data["miny"] == 10.0
    assert data["maxx"] == 25.0
    assert data["maxy"] == 40.0
    assert data["width"] == 20.0
    assert data["height"] == 30.0
    assert data["area"] == 600.0


def test_gis_bounding_box_with_pydantic_request_and_wkt():
    """Verify gis_bounding_box works with GISBoundingBoxRequest and WKT geometry."""
    wkt = "LINESTRING (0 0, 5 15, 10 5)"
    req = GISBoundingBoxRequest(geometry=wkt, engine="auto")
    res = gis_bounding_box(req)
    assert res["success"] is True
    data = res["data"]
    assert data["minx"] == 0.0
    assert data["miny"] == 0.0
    assert data["maxx"] == 10.0
    assert data["maxy"] == 15.0
    assert data["width"] == 10.0
    assert data["height"] == 15.0


def test_gis_bounding_box_error_handling():
    """Verify error reporting for missing or empty inputs."""
    res_none = gis_bounding_box(geometry=None)
    assert res_none["success"] is False
    assert res_none["error"]["code"] == "MISSING_ARGUMENTS"

    res_empty = gis_bounding_box(geometry=[])
    assert res_empty["success"] is False
    assert res_empty["error"]["code"] == "INVALID_GEOMETRY"


# ==============================================================================
# WORKSPACE TOOLS TESTS: fme_audit_performance
# ==============================================================================


@pytest.fixture
def complex_sample_fmw(tmp_path: Path) -> Path:
    """Create a synthetic FME workspace with bookmarks, heavy transformers, annotations, and parameters."""
    fmw_file = tmp_path / "audit_test_workflow.fmw"
    content = """#! <?xml version="1.0" encoding="utf-8" ?>
#! <WORKSPACE
#!   TITLE="GIS Processing Pipeline"
#!   DESCRIPTION="Automated spatial pipeline for cadastral parcels."
#!   LAST_SAVE_BUILD="FME 2025.2 (Build 25200)"
#!   LAST_SAVE_DATE="2026-11-10"
#!   PYTHON_COMPATIBILITY="Python 3.11"
#!   DOC_EXTENTS="1000 800"
#!   ENABLE_DATA_CACHING="Yes"
#! >
#! <DATASETS>
#!   <DATASET ROLE="READER" FORMAT="POSTGIS" DATASET="cadastre_db" />
#!   <DATASET ROLE="READER" FORMAT="CSV" DATASET="metadata.csv" />
#!   <DATASET ROLE="WRITER" FORMAT="GEOPACKAGE" DATASET="out_parcels.gpkg" />
#! </DATASETS>
#! <GLOBAL_PARAMETERS>
#!   <GLOBAL_PARAMETER GUI_LINE="GUI TEXT BUFFER_DIST Buffer Distance:" DEFAULT_VALUE="50.0" />
#!   <GLOBAL_PARAMETER GUI_LINE="GUI OPTIONAL_TEXT LOG_DIR Output Directory:" DEFAULT_VALUE="/tmp" />
#! </GLOBAL_PARAMETERS>
#! <COMMENTS>
#!   <COMMENT IDENTIFIER="101" COMMENT_VALUE="Filter invalid geometries before joining" POSITION="120 -150" />
#!   <COMMENT IDENTIFIER="102" COMMENT_VALUE="CRITICAL: Standalone review note" POSITION="600 -400" />
#! </COMMENTS>
#! <BOOKMARKS>
#!   <BOOKMARK IDENTIFIER="1" NAME="01_Preparation" DESCRIPTION="Initial filtering and attribute renaming" PALETTE_COLOR="Blue" CONTENTS="10 11 101" TOP_LEFT="50 -100" BOTTOM_RIGHT="400 -300" />
#!   <BOOKMARK IDENTIFIER="2" NAME="02_Overlay_And_Join" DESCRIPTION="Heavy spatial overlay section" PALETTE_COLOR="Orange" CONTENTS="12 13" TOP_LEFT="450 -100" BOTTOM_RIGHT="800 -300" />
#! </BOOKMARKS>
#! <TRANSFORMERS>
#!   <TRANSFORMER IDENTIFIER="10" TYPE="AttributeKeeper" POSITION="100 -200" ENABLED="true">
#!     <XFORM_PARM PARM_NAME="XFORMER_NAME" PARM_VALUE="Keeper_Attrs"/>
#!     <OUTPUT_FEAT NAME="OUTPUT"/>
#!   </TRANSFORMER>
#!   <TRANSFORMER IDENTIFIER="11" TYPE="Sorter" POSITION="250 -200" ENABLED="true">
#!     <XFORM_PARM PARM_NAME="XFORMER_NAME" PARM_VALUE="Sorter_Parcels"/>
#!     <OUTPUT_FEAT NAME="OUTPUT"/>
#!   </TRANSFORMER>
#!   <TRANSFORMER IDENTIFIER="12" TYPE="FeatureMerger" POSITION="500 -200" ENABLED="true">
#!     <XFORM_PARM PARM_NAME="XFORMER_NAME" PARM_VALUE="FeatureMerger_Owners"/>
#!     <OUTPUT_FEAT NAME="COMPLETE"/>
#!     <OUTPUT_FEAT NAME="UNMERGED_REQUESTOR"/>
#!   </TRANSFORMER>
#!   <TRANSFORMER IDENTIFIER="13" TYPE="AreaOnAreaOverlayer" POSITION="650 -200" ENABLED="true">
#!     <XFORM_PARM PARM_NAME="XFORMER_NAME" PARM_VALUE="AreaOverlayer_Zones"/>
#!     <OUTPUT_FEAT NAME="AREA"/>
#!   </TRANSFORMER>
#!   <TRANSFORMER IDENTIFIER="14" TYPE="Inspector" POSITION="850 -200" ENABLED="true">
#!     <XFORM_PARM PARM_NAME="XFORMER_NAME" PARM_VALUE="Inspector_Debug"/>
#!     <OUTPUT_FEAT NAME="OUTPUT"/>
#!   </TRANSFORMER>
#! </TRANSFORMERS>
#! <FEAT_LINKS>
#!   <FEAT_LINK IDENTIFIER="1" SOURCE_NODE="Keeper_Attrs" SOURCE_PORT_DESC="OUTPUT" TARGET_NODE="Sorter_Parcels" TARGET_PORT_DESC="INPUT" ENABLED="true" />
#!   <FEAT_LINK IDENTIFIER="2" SOURCE_NODE="Sorter_Parcels" SOURCE_PORT_DESC="OUTPUT" TARGET_NODE="FeatureMerger_Owners" TARGET_PORT_DESC="REQUESTOR" ENABLED="true" />
#!   <FEAT_LINK IDENTIFIER="3" SOURCE_NODE="FeatureMerger_Owners" SOURCE_PORT_DESC="COMPLETE" TARGET_NODE="AreaOverlayer_Zones" TARGET_PORT_DESC="INPUT" ENABLED="true" />
#!   <FEAT_LINK IDENTIFIER="4" SOURCE_NODE="AreaOverlayer_Zones" SOURCE_PORT_DESC="AREA" TARGET_NODE="Inspector_Debug" TARGET_PORT_DESC="INPUT" ENABLED="true" />
#! </FEAT_LINKS>
#! </WORKSPACE>
"""
    fmw_file.write_text(content, encoding="utf-8")
    return fmw_file


def test_fme_audit_performance_detects_bottlenecks(complex_sample_fmw: Path):
    """Verify performance audit identifies heavy transformers, blocking chains, and debug nodes."""
    res = fme_audit_performance(str(complex_sample_fmw), strict_mode=False)
    assert res["success"] is True
    data = res["data"]

    # Verify summary structure
    assert data["workspace_name"] == "audit_test_workflow.fmw"
    assert 0 <= data["performance_score"] <= 100
    assert data["rating"] in ["EXCELLENT", "GOOD", "FAIR", "POOR - NEEDS_OPTIMIZATION"]

    summary = data["summary"]
    assert summary["total_transformers"] == 5
    assert summary["heavy_transformers_count"] >= 3  # Sorter, FeatureMerger, AreaOnAreaOverlayer

    # Check heavy transformers catalog detection
    heavy_types = [h["type"] for h in data["heavy_transformers"]]
    assert "Sorter" in heavy_types
    assert "FeatureMerger" in heavy_types
    assert "AreaOnAreaOverlayer" in heavy_types

    # Check bottleneck categories
    bottleneck_types = [b["type"] for b in data["bottlenecks"]]
    assert "CHAINED_BLOCKING_PIPELINE" in bottleneck_types
    assert "DEBUG_TRANSFORMERS_PRESENT" in bottleneck_types
    assert "FEATURE_CACHING_ENABLED" in bottleneck_types
    assert "UNCONNECTED_REJECTED_PORTS" in bottleneck_types

    # Check unindexed readers
    unindexed = data["unindexed_inputs"]
    assert any(u["format"] == "POSTGIS" for u in unindexed)

    # Check recommendations list is populated
    assert len(data["recommendations"]) > 0


def test_fme_audit_performance_strict_mode(complex_sample_fmw: Path):
    """Verify strict mode applies heavier deductions to the final performance score."""
    res_normal = fme_audit_performance(str(complex_sample_fmw), strict_mode=False)
    res_strict = fme_audit_performance(str(complex_sample_fmw), strict_mode=True)

    assert res_normal["success"] is True
    assert res_strict["success"] is True
    assert res_strict["data"]["performance_score"] <= res_normal["data"]["performance_score"]
    assert res_strict["data"]["audit_flags"]["strict_mode"] is True


def test_fme_audit_performance_real_workspace():
    """Verify audit on repository example workspace MCPConnector_Demo.fmw."""
    demo_path = Path("examples/workbench/MCPConnector_Demo.fmw")
    if not demo_path.exists():
        pytest.skip("examples/workbench/MCPConnector_Demo.fmw not found")

    res = fme_audit_performance(str(demo_path))
    assert res["success"] is True
    assert res["data"]["workspace_name"] == "MCPConnector_Demo.fmw"
    assert "performance_score" in res["data"]


def test_fme_audit_performance_corrupt_file(tmp_path: Path):
    """Verify error reporting on corrupt or non-xml workspace file."""
    corrupt_file = tmp_path / "corrupt.fmw"
    corrupt_file.write_text("NOT_XML_DATA", encoding="utf-8")

    res = fme_audit_performance(str(corrupt_file))
    assert res["success"] is False
    assert res["error"]["code"] == "PARSE_ERROR"


# ==============================================================================
# WORKSPACE TOOLS TESTS: fme_export_markdown_docs
# ==============================================================================


def test_fme_export_markdown_docs_content(complex_sample_fmw: Path):
    """Verify generated markdown contains structured sections, tables, bookmarks, and parameters."""
    res = fme_export_markdown_docs(str(complex_sample_fmw), include_canvas_summary=True)
    assert res["success"] is True
    data = res["data"]

    md = data["markdown"]
    # Check title & metadata
    assert "# 🗺️ FME Workspace: GIS Processing Pipeline" in md
    assert "cadastral parcels" in md
    assert "FME 2025.2" in md

    # Check published parameters section
    assert "## ⚙️ Published User Parameters" in md
    assert "BUFFER_DIST" in md

    # Check datasets section
    assert "## 💾 Data Sources & Destinations" in md
    assert "POSTGIS" in md
    assert "GEOPACKAGE" in md

    # Check bookmarks section and hierarchy
    assert "## 🏗️ Workflow Architecture & Bookmarks" in md
    assert "### 📑 Bookmark: 01_Preparation" in md
    assert "Keeper_Attrs" in md
    assert "Sorter_Parcels" in md
    assert "### 📑 Bookmark: 02_Overlay_And_Join" in md
    assert "AreaOverlayer_Zones" in md

    # Check standalone annotation section
    assert "## 💬 Canvas Annotations & Notes" in md
    assert "CRITICAL: Standalone review note" in md

    # Check transformer distribution inventory
    assert "## 📊 Transformer Inventory & Distribution" in md
    assert "AreaOnAreaOverlayer" in md

    # Check canvas connectivity summary
    assert "## 🔗 Canvas Connectivity Graph" in md

    # Verify component stats
    stats = data["stats"]
    assert stats["total_bookmarks"] == 2
    assert stats["total_annotations"] == 2
    assert stats["total_transformers"] == 5
    assert stats["total_parameters"] == 2
    assert stats["total_datasets"] == 3


def test_fme_export_markdown_docs_saves_to_file(complex_sample_fmw: Path, tmp_path: Path):
    """Verify markdown output can be saved directly to a file on disk."""
    out_file = tmp_path / "workspace_doc.md"
    res = fme_export_markdown_docs(
        str(complex_sample_fmw),
        output_file=str(out_file),
        include_canvas_summary=False,
    )

    assert res["success"] is True
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert content == res["data"]["markdown"]
    # Connectivity graph omitted when include_canvas_summary=False
    assert "## 🔗 Canvas Connectivity Graph" not in content


def test_fme_export_markdown_docs_corrupt_file(tmp_path: Path):
    """Verify error reporting when exporting docs from an invalid file."""
    bad_file = tmp_path / "invalid.fmw"
    bad_file.write_text("INVALID_CONTENT", encoding="utf-8")

    res = fme_export_markdown_docs(str(bad_file))
    assert res["success"] is False
    assert res["error"]["code"] == "PARSE_ERROR"
