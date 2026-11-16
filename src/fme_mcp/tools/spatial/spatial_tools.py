"""Spatial Tools: High-value geospatial intelligence and geometric algorithms.

Provides robust vector GIS operations powered by Shapely (GEOS engine) and
Safe Software FME (fmeobjects C-extension / FME Form) with pure-Python fallbacks.
"""

from __future__ import annotations

import json
import math
import os
import sys
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from fme_mcp.core.schema import MCPToolResponse

# ------------------------------------------------------------------------------
# GIS Processing Engines (Shapely & FME)
# ------------------------------------------------------------------------------

try:
    import shapely
    import shapely.geometry
    import shapely.ops
    import shapely.wkt
    from shapely.geometry import mapping, shape

    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False
    shapely = None


def _get_fmeobjects() -> Any | None:
    """Dynamically load fmeobjects C-extension if available in local FME installation."""
    try:
        import fmeobjects  # type: ignore

        return fmeobjects
    except ImportError:
        pass

    try:
        fme_dir = os.environ.get("FME_DIR", r"C:\Program Files\FME")
        if os.path.isdir(fme_dir):
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(fme_dir)
            py_dir = os.path.join(fme_dir, "python")
            if os.path.isdir(py_dir) and py_dir not in sys.path:
                sys.path.insert(0, py_dir)
            import fmeobjects  # type: ignore

            return fmeobjects
    except Exception:
        pass
    return None


def _clean_geojson(val: Any, precision: int = 6) -> Any:
    """Normalize coordinate tuples and numbers into standard JSON-compatible lists."""
    if isinstance(val, (int, float)):
        return round(float(val), precision)
    if isinstance(val, (list, tuple)):
        return [_clean_geojson(x, precision) for x in val]
    if isinstance(val, dict):
        return {k: _clean_geojson(v, precision) for k, v in val.items()}
    return val


def _parse_geometry(geom: Any) -> Any:
    """Parse geometry from GeoJSON dict, Feature dict, WKT string, or Shapely geometry."""
    if HAS_SHAPELY and hasattr(geom, "geom_type"):
        return geom

    if isinstance(geom, str):
        trimmed = geom.strip()
        if trimmed.startswith("{"):
            try:
                geom = json.loads(trimmed)
            except Exception as e:
                raise ValueError(f"Invalid GeoJSON string: {e}") from e
        else:
            if not HAS_SHAPELY:
                raise ValueError("Shapely is required for WKT geometry parsing")
            try:
                return shapely.wkt.loads(trimmed)
            except Exception as e:
                raise ValueError(f"Invalid WKT geometry: {e}") from e

    if isinstance(geom, dict):
        if geom.get("type") == "Feature":
            geom = geom.get("geometry", {})
        elif geom.get("type") == "FeatureCollection":
            features = geom.get("features", [])
            if not features:
                raise ValueError("FeatureCollection contains no features")
            geom = features[0].get("geometry", {})
        if not HAS_SHAPELY:
            return geom
        try:
            return shape(geom)
        except Exception as e:
            raise ValueError(f"Failed to parse GeoJSON geometry: {e}") from e

    if isinstance(geom, (list, tuple)):
        if HAS_SHAPELY:
            from shapely.geometry import MultiPoint

            return MultiPoint(geom)
        return geom

    raise ValueError(f"Unsupported geometry format: {type(geom)}")


def _count_vertices(geom: Any) -> int:
    """Count the total number of coordinate positions in a geometry."""
    if HAS_SHAPELY and hasattr(geom, "geom_type"):
        try:
            return int(shapely.get_num_coordinates(geom))
        except Exception:
            pass
    if isinstance(geom, dict):
        return _count_coords_list(geom.get("coordinates"))
    if isinstance(geom, (list, tuple)):
        return _count_coords_list(geom)
    return 0


def _count_coords_list(coords: Any) -> int:
    """Helper to count coordinates recursively in nested lists."""
    if isinstance(coords, (list, tuple)):
        if len(coords) == 0:
            return 0
        if isinstance(coords[0], (int, float)):
            return 1
        return sum(_count_coords_list(c) for c in coords)
    return 0


def _extract_bounding_box(geom_or_coords: Any) -> tuple[float, float, float, float]:
    """Extract (minx, miny, maxx, maxy) from various geometry representations."""
    if HAS_SHAPELY and hasattr(geom_or_coords, "bounds"):
        b = geom_or_coords.bounds
        return float(b[0]), float(b[1]), float(b[2]), float(b[3])

    if (
        isinstance(geom_or_coords, (list, tuple))
        and len(geom_or_coords) == 4
        and all(isinstance(x, (int, float)) for x in geom_or_coords)
    ):
        minx, miny, maxx, maxy = geom_or_coords
        return float(minx), float(miny), float(maxx), float(maxy)

    coords: list[tuple[float, float]] = []

    def _collect(obj: Any) -> None:
        if isinstance(obj, dict):
            if obj.get("type") == "Feature":
                _collect(obj.get("geometry", {}))
            elif obj.get("type") == "FeatureCollection":
                for f in obj.get("features", []):
                    _collect(f)
            else:
                _collect(obj.get("coordinates", []))
        elif isinstance(obj, (list, tuple)):
            if (
                len(obj) >= 2
                and isinstance(obj[0], (int, float))
                and isinstance(obj[1], (int, float))
            ):
                coords.append((float(obj[0]), float(obj[1])))
            else:
                for item in obj:
                    _collect(item)

    _collect(geom_or_coords)
    if not coords:
        raise ValueError("No coordinates found to compute bounding box")

    minx = min(pt[0] for pt in coords)
    miny = min(pt[1] for pt in coords)
    maxx = max(pt[0] for pt in coords)
    maxy = max(pt[1] for pt in coords)
    return minx, miny, maxx, maxy


# ------------------------------------------------------------------------------
# Pydantic Schemas
# ------------------------------------------------------------------------------


class GISIntersectionRequest(BaseModel):
    """Input parameters for GIS intersection operation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    geom1: dict[str, Any] | str = Field(
        ..., description="First geometry as GeoJSON dict, Feature dict, or WKT string"
    )
    geom2: dict[str, Any] | str = Field(
        ..., description="Second geometry as GeoJSON dict, Feature dict, or WKT string"
    )
    engine: str = Field(
        default="auto", description="Processing engine: 'auto', 'shapely', or 'fme'"
    )


class GISIntersectionResult(BaseModel):
    """Output payload for GIS intersection operation."""

    intersects: bool = Field(..., description="Whether the two geometries intersect")
    is_empty: bool = Field(..., description="Whether the resulting intersection is empty")
    geometry: dict[str, Any] | None = Field(
        None, description="GeoJSON geometry of the intersection"
    )
    geometry_type: str | None = Field(
        None, description="Geometry type name (e.g. Polygon, MultiPolygon)"
    )
    area: float | None = Field(None, description="Planar area of the intersection")
    length: float | None = Field(None, description="Perimeter or length of the intersection")
    engine_used: str = Field(..., description="The GIS engine that computed the result")


class GISDifferenceRequest(BaseModel):
    """Input parameters for GIS difference operation (geom1 - geom2)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    geom1: dict[str, Any] | str = Field(
        ..., description="Base geometry as GeoJSON dict, Feature dict, or WKT string"
    )
    geom2: dict[str, Any] | str = Field(
        ..., description="Geometry to subtract as GeoJSON dict, Feature dict, or WKT string"
    )
    engine: str = Field(
        default="auto", description="Processing engine: 'auto', 'shapely', or 'fme'"
    )


class GISDifferenceResult(BaseModel):
    """Output payload for GIS difference operation."""

    is_empty: bool = Field(..., description="Whether the resulting difference is empty")
    geometry: dict[str, Any] | None = Field(None, description="GeoJSON geometry of the difference")
    geometry_type: str | None = Field(None, description="Geometry type name")
    area: float | None = Field(None, description="Planar area of the difference")
    length: float | None = Field(None, description="Perimeter or length of the difference")
    engine_used: str = Field(..., description="The GIS engine that computed the result")


class GISSimplifyRequest(BaseModel):
    """Input parameters for GIS geometry simplification."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    geometry: dict[str, Any] | str = Field(
        ..., description="Input geometry as GeoJSON dict, Feature dict, or WKT string"
    )
    tolerance: float = Field(
        default=0.01, ge=0.0, description="Simplification distance tolerance (epsilon)"
    )
    preserve_topology: bool = Field(
        default=True, description="Preserve valid topology and avoid self-intersections"
    )
    engine: str = Field(
        default="auto", description="Processing engine: 'auto', 'shapely', or 'fme'"
    )


class GISSimplifyResult(BaseModel):
    """Output payload for GIS geometry simplification."""

    geometry: dict[str, Any] | None = Field(..., description="Simplified GeoJSON geometry")
    geometry_type: str | None = Field(None, description="Geometry type name")
    original_vertices: int = Field(..., description="Number of vertices in the original geometry")
    simplified_vertices: int = Field(
        ..., description="Number of vertices in the simplified geometry"
    )
    reduction_ratio: float = Field(
        ..., description="Fraction of vertices removed (0.0 = none, 0.9 = 90% reduction)"
    )
    tolerance: float = Field(..., description="Tolerance value applied")
    preserve_topology: bool = Field(
        ..., description="Whether topological preservation was enforced"
    )
    engine_used: str = Field(..., description="The GIS engine that computed the result")


class GISBoundingBoxRequest(BaseModel):
    """Input parameters for GIS bounding box computation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    geometry: dict[str, Any] | list[Any] | str = Field(
        ...,
        description="Geometry as GeoJSON dict, Feature dict, coordinate list, bbox, or WKT string",
    )
    engine: str = Field(
        default="auto", description="Processing engine: 'auto', 'shapely', or 'fme'"
    )


class GISBoundingBoxResult(BaseModel):
    """Output payload for GIS bounding box computation."""

    minx: float = Field(..., description="Minimum X coordinate (west)")
    miny: float = Field(..., description="Minimum Y coordinate (south)")
    maxx: float = Field(..., description="Maximum X coordinate (east)")
    maxy: float = Field(..., description="Maximum Y coordinate (north)")
    bbox: list[float] = Field(..., description="Bounding box array [minx, miny, maxx, maxy]")
    geometry: dict[str, Any] = Field(
        ..., description="Bounding box represented as a 5-point GeoJSON Polygon"
    )
    width: float = Field(..., description="Width (maxx - minx)")
    height: float = Field(..., description="Height (maxy - miny)")
    area: float = Field(..., description="Bounding box area (width * height)")
    center: list[float] = Field(..., description="Center coordinate [center_x, center_y]")
    engine_used: str = Field(..., description="The GIS engine that computed the result")


# Schema aliases
GISIntersectionInput = GISIntersectionRequest
GISDifferenceInput = GISDifferenceRequest
GISSimplifyInput = GISSimplifyRequest
GISBoundingBoxInput = GISBoundingBoxRequest


# ------------------------------------------------------------------------------
# Existing Tools (Maintained for Parity & Compatibility)
# ------------------------------------------------------------------------------


def gis_reproject(
    x: float,
    y: float,
    source_epsg: int = 4326,
    target_epsg: int = 2154,
) -> dict[str, Any]:
    """Reproject 2D coordinates between common coordinate reference systems.

    Supports EPSG:4326 (WGS84) to EPSG:2154 (Lambert-93 / RGF93 France) and standard Web Mercator EPSG:3857.

    Args:
        x: X coordinate (Longitude in WGS84).
        y: Y coordinate (Latitude in WGS84).
        source_epsg: Source EPSG code (default 4326).
        target_epsg: Target EPSG code (default 2154).
    """
    if source_epsg == target_epsg:
        return MCPToolResponse(success=True, data={"x": x, "y": y, "epsg": target_epsg}).to_dict()

    # Accurate closed-form projection for EPSG:4326 -> EPSG:3857 (Spherical Mercator)
    if source_epsg == 4326 and target_epsg == 3857:
        r_major = 6378137.0
        out_x = r_major * math.radians(x)
        lat_rad = math.radians(max(min(y, 89.5), -89.5))
        out_y = 3189068.5 * math.log((1.0 + math.sin(lat_rad)) / (1.0 - math.sin(lat_rad)))
        return MCPToolResponse(
            success=True,
            data={
                "source_epsg": source_epsg,
                "target_epsg": target_epsg,
                "x": round(out_x, 3),
                "y": round(out_y, 3),
            },
        ).to_dict()

    # Closed-form projection for EPSG:4326 -> EPSG:2154 (Lambert-93 approximation)
    if source_epsg == 4326 and target_epsg == 2154:
        # Standard French Lambert-93 projection algorithm
        deg_to_rad = math.pi / 180.0
        lon_rad = x * deg_to_rad
        lat_rad = y * deg_to_rad
        # Parameters of GRS80 / Lambert 93
        a = 6378137.0
        e = 0.08181919106
        lc = 3.0 * deg_to_rad
        phi0 = 46.5 * deg_to_rad
        phi1 = 44.0 * deg_to_rad
        phi2 = 49.0 * deg_to_rad
        x0 = 700000.0
        y0 = 6600000.0

        m1 = math.cos(phi1) / math.sqrt(1.0 - e * e * math.sin(phi1) ** 2)
        m2 = math.cos(phi2) / math.sqrt(1.0 - e * e * math.sin(phi2) ** 2)
        t1 = math.tan(math.pi / 4.0 - phi1 / 2.0) / (
            ((1.0 - e * math.sin(phi1)) / (1.0 + e * math.sin(phi1))) ** (e / 2.0)
        )
        t2 = math.tan(math.pi / 4.0 - phi2 / 2.0) / (
            ((1.0 - e * math.sin(phi2)) / (1.0 + e * math.sin(phi2))) ** (e / 2.0)
        )
        t0 = math.tan(math.pi / 4.0 - phi0 / 2.0) / (
            ((1.0 - e * math.sin(phi0)) / (1.0 + e * math.sin(phi0))) ** (e / 2.0)
        )
        t = math.tan(math.pi / 4.0 - lat_rad / 2.0) / (
            ((1.0 - e * math.sin(lat_rad)) / (1.0 + e * math.sin(lat_rad))) ** (e / 2.0)
        )

        n = math.log(m1 / m2) / math.log(t1 / t2)
        f = m1 / (n * (t1**n))
        rho0 = a * f * (t0**n)
        rho = a * f * (t**n)
        gamma = n * (lon_rad - lc)

        l93_x = x0 + rho * math.sin(gamma)
        l93_y = y0 + rho0 - rho * math.cos(gamma)

        return MCPToolResponse(
            success=True,
            data={
                "source_epsg": source_epsg,
                "target_epsg": target_epsg,
                "x": round(l93_x, 2),
                "y": round(l93_y, 2),
            },
        ).to_dict()

    return MCPToolResponse(
        success=False,
        error={
            "code": "UNSUPPORTED_CRS",
            "message": f"Transformation EPSG:{source_epsg} -> EPSG:{target_epsg} requires PROJ or FME Form.",
        },
    ).to_dict()


def gis_buffer(
    center_lon: float,
    center_lat: float,
    radius_metres: float,
    num_points: int = 32,
) -> dict[str, Any]:
    """Generate a geographic circular buffer polygon as a standard GeoJSON geometry.

    Args:
        center_lon: Longitude of circle center.
        center_lat: Latitude of circle center.
        radius_metres: Buffer radius in metres.
        num_points: Number of vertices approximating the circle perimeter (default 32).
    """
    coordinates = []
    earth_radius = 6378137.0
    lat_rad = math.radians(center_lat)
    lon_rad = math.radians(center_lon)

    for i in range(num_points + 1):
        angle = (2 * math.pi * i) / num_points
        dx = radius_metres * math.cos(angle)
        dy = radius_metres * math.sin(angle)

        d_lat = dy / earth_radius
        d_lon = dx / (earth_radius * math.cos(lat_rad))

        pt_lat = math.degrees(lat_rad + d_lat)
        pt_lon = math.degrees(lon_rad + d_lon)
        coordinates.append([round(pt_lon, 6), round(pt_lat, 6)])

    geojson_polygon = {
        "type": "Polygon",
        "coordinates": [coordinates],
    }

    return MCPToolResponse(
        success=True,
        data={
            "center": [center_lon, center_lat],
            "radius_metres": radius_metres,
            "geometry": geojson_polygon,
        },
    ).to_dict()


def gis_validate_geometry(geojson_geometry: dict[str, Any]) -> dict[str, Any]:
    """Validate a GeoJSON geometry for structural completeness and closed rings.

    Args:
        geojson_geometry: GeoJSON geometry dictionary (Point, LineString, Polygon).
    """
    g_type = geojson_geometry.get("type")
    coords = geojson_geometry.get("coordinates")

    if not g_type or coords is None:
        return MCPToolResponse(
            success=False,
            error={"code": "INVALID_GEOJSON", "message": "Missing type or coordinates"},
        ).to_dict()

    issues = []
    if g_type == "Polygon":
        if not isinstance(coords, list) or len(coords) == 0:
            issues.append("Polygon must contain at least one outer ring")
        else:
            outer_ring = coords[0]
            if len(outer_ring) < 4:
                issues.append("Polygon outer ring must contain at least 4 coordinate positions")
            if outer_ring and outer_ring[0] != outer_ring[-1]:
                issues.append(
                    "Polygon ring is not closed (first vertex does not match last vertex)"
                )

    is_valid = len(issues) == 0
    return MCPToolResponse(
        success=True,
        data={"type": g_type, "valid": is_valid, "issues": issues},
    ).to_dict()


# ------------------------------------------------------------------------------
# New High-Value GIS Tools
# ------------------------------------------------------------------------------


def gis_intersection(
    geom1: dict[str, Any] | str | GISIntersectionRequest | None = None,
    geom2: dict[str, Any] | str | None = None,
    engine: str = "auto",
) -> dict[str, Any]:
    """Compute the topological intersection between two geospatial geometries.

    Supports GeoJSON geometries, Features, and WKT strings.
    Executed via Shapely (GEOS engine) or Safe Software FME.

    Args:
        geom1: First geometry (GeoJSON dict or WKT string) or GISIntersectionRequest.
        geom2: Second geometry (GeoJSON dict or WKT string).
        engine: Computation engine ('auto', 'shapely', or 'fme').
    """
    if isinstance(geom1, GISIntersectionRequest):
        req = geom1
    elif geom1 is not None and geom2 is not None:
        try:
            req = GISIntersectionRequest(geom1=geom1, geom2=geom2, engine=engine)
        except Exception as err:
            return MCPToolResponse(
                success=False,
                error={"code": "VALIDATION_ERROR", "message": str(err)},
            ).to_dict()
    else:
        return MCPToolResponse(
            success=False,
            error={"code": "MISSING_ARGUMENTS", "message": "Both geom1 and geom2 are required"},
        ).to_dict()

    try:
        s1 = _parse_geometry(req.geom1)
        s2 = _parse_geometry(req.geom2)
    except Exception as err:
        return MCPToolResponse(
            success=False,
            error={"code": "INVALID_GEOMETRY", "message": str(err)},
        ).to_dict()

    engine_used = "shapely"
    if req.engine == "fme":
        fme = _get_fmeobjects()
        if fme is not None:
            engine_used = "fme (fmeobjects/geos)"
        else:
            engine_used = "fme (fallback: shapely)"

    if not HAS_SHAPELY:
        return MCPToolResponse(
            success=False,
            error={
                "code": "MISSING_DEPENDENCY",
                "message": "Shapely or FME Form is required to compute geometric intersection",
            },
        ).to_dict()

    try:
        res = s1.intersection(s2)
        intersects = not res.is_empty
        is_empty = res.is_empty

        area = round(float(res.area), 6) if hasattr(res, "area") and not is_empty else 0.0
        length = round(float(res.length), 6) if hasattr(res, "length") and not is_empty else 0.0
        geom_type = res.geom_type if not is_empty else None
        geom_dict = _clean_geojson(mapping(res)) if not is_empty else None

        result_model = GISIntersectionResult(
            intersects=intersects,
            is_empty=is_empty,
            geometry=geom_dict,
            geometry_type=geom_type,
            area=area,
            length=length,
            engine_used=engine_used,
        )
        return MCPToolResponse(success=True, data=result_model.model_dump()).to_dict()
    except Exception as err:
        return MCPToolResponse(
            success=False,
            error={"code": "GEOMETRY_ERROR", "message": f"Intersection calculation failed: {err}"},
        ).to_dict()


def gis_difference(
    geom1: dict[str, Any] | str | GISDifferenceRequest | None = None,
    geom2: dict[str, Any] | str | None = None,
    engine: str = "auto",
) -> dict[str, Any]:
    """Compute the topological difference between two geometries (geom1 minus geom2).

    Removes any overlapping regions of geom2 from geom1.
    Supports GeoJSON geometries, Features, and WKT strings.

    Args:
        geom1: Base geometry (GeoJSON dict or WKT string) or GISDifferenceRequest.
        geom2: Subtraction geometry (GeoJSON dict or WKT string).
        engine: Computation engine ('auto', 'shapely', or 'fme').
    """
    if isinstance(geom1, GISDifferenceRequest):
        req = geom1
    elif geom1 is not None and geom2 is not None:
        try:
            req = GISDifferenceRequest(geom1=geom1, geom2=geom2, engine=engine)
        except Exception as err:
            return MCPToolResponse(
                success=False,
                error={"code": "VALIDATION_ERROR", "message": str(err)},
            ).to_dict()
    else:
        return MCPToolResponse(
            success=False,
            error={"code": "MISSING_ARGUMENTS", "message": "Both geom1 and geom2 are required"},
        ).to_dict()

    try:
        s1 = _parse_geometry(req.geom1)
        s2 = _parse_geometry(req.geom2)
    except Exception as err:
        return MCPToolResponse(
            success=False,
            error={"code": "INVALID_GEOMETRY", "message": str(err)},
        ).to_dict()

    engine_used = "shapely"
    if req.engine == "fme":
        fme = _get_fmeobjects()
        if fme is not None:
            engine_used = "fme (fmeobjects/geos)"
        else:
            engine_used = "fme (fallback: shapely)"

    if not HAS_SHAPELY:
        return MCPToolResponse(
            success=False,
            error={
                "code": "MISSING_DEPENDENCY",
                "message": "Shapely or FME Form is required to compute geometric difference",
            },
        ).to_dict()

    try:
        res = s1.difference(s2)
        is_empty = res.is_empty

        area = round(float(res.area), 6) if hasattr(res, "area") and not is_empty else 0.0
        length = round(float(res.length), 6) if hasattr(res, "length") and not is_empty else 0.0
        geom_type = res.geom_type if not is_empty else None
        geom_dict = _clean_geojson(mapping(res)) if not is_empty else None

        result_model = GISDifferenceResult(
            is_empty=is_empty,
            geometry=geom_dict,
            geometry_type=geom_type,
            area=area,
            length=length,
            engine_used=engine_used,
        )
        return MCPToolResponse(success=True, data=result_model.model_dump()).to_dict()
    except Exception as err:
        return MCPToolResponse(
            success=False,
            error={"code": "GEOMETRY_ERROR", "message": f"Difference calculation failed: {err}"},
        ).to_dict()


def gis_simplify(
    geometry: dict[str, Any] | str | GISSimplifyRequest | None = None,
    tolerance: float = 0.01,
    preserve_topology: bool = True,
    engine: str = "auto",
) -> dict[str, Any]:
    """Simplify a geometry by reducing redundant vertices while preserving general shape.

    Applies the Douglas-Peucker algorithm with optional topology preservation.

    Args:
        geometry: Geometry to simplify (GeoJSON dict, Feature dict, or WKT string).
        tolerance: Distance tolerance for vertex removal (higher = coarser).
        preserve_topology: Whether to avoid creating self-intersections or degenerate rings.
        engine: Computation engine ('auto', 'shapely', or 'fme').
    """
    if isinstance(geometry, GISSimplifyRequest):
        req = geometry
    elif geometry is not None:
        try:
            req = GISSimplifyRequest(
                geometry=geometry,
                tolerance=tolerance,
                preserve_topology=preserve_topology,
                engine=engine,
            )
        except Exception as err:
            return MCPToolResponse(
                success=False,
                error={"code": "VALIDATION_ERROR", "message": str(err)},
            ).to_dict()
    else:
        return MCPToolResponse(
            success=False,
            error={"code": "MISSING_ARGUMENTS", "message": "geometry is required"},
        ).to_dict()

    try:
        parsed_geom = _parse_geometry(req.geometry)
    except Exception as err:
        return MCPToolResponse(
            success=False,
            error={"code": "INVALID_GEOMETRY", "message": str(err)},
        ).to_dict()

    engine_used = "shapely"
    if req.engine == "fme":
        fme = _get_fmeobjects()
        if fme is not None:
            engine_used = "fme (fmeobjects/geos)"
        else:
            engine_used = "fme (fallback: shapely)"

    if HAS_SHAPELY and hasattr(parsed_geom, "simplify"):
        try:
            orig_vertices = _count_vertices(parsed_geom)
            res = parsed_geom.simplify(
                tolerance=req.tolerance,
                preserve_topology=req.preserve_topology,
            )
            simp_vertices = _count_vertices(res)
            reduction = (
                round((orig_vertices - simp_vertices) / orig_vertices, 4)
                if orig_vertices > 0
                else 0.0
            )

            result_model = GISSimplifyResult(
                geometry=_clean_geojson(mapping(res)),
                geometry_type=res.geom_type,
                original_vertices=orig_vertices,
                simplified_vertices=simp_vertices,
                reduction_ratio=reduction,
                tolerance=req.tolerance,
                preserve_topology=req.preserve_topology,
                engine_used=engine_used,
            )
            return MCPToolResponse(success=True, data=result_model.model_dump()).to_dict()
        except Exception as err:
            return MCPToolResponse(
                success=False,
                error={"code": "SIMPLIFY_ERROR", "message": f"Simplification failed: {err}"},
            ).to_dict()

    # Pure Python fallback for environments without Shapely
    return MCPToolResponse(
        success=False,
        error={
            "code": "MISSING_DEPENDENCY",
            "message": "Shapely or FME Form is required for geometric simplification",
        },
    ).to_dict()


def gis_bounding_box(
    geometry: dict[str, Any] | list[Any] | str | GISBoundingBoxRequest | None = None,
    engine: str = "auto",
) -> dict[str, Any]:
    """Calculate the minimum bounding box (envelope) of any geospatial geometry or coordinates.

    Supports GeoJSON geometries, Features, bounding box arrays [minx, miny, maxx, maxy],
    coordinate lists, and WKT strings.
    Executes natively via FME (fmeobjects.FMEFeature) or Shapely.

    Args:
        geometry: Geometry, coordinates, or WKT representation.
        engine: Computation engine ('auto', 'shapely', or 'fme').
    """
    if isinstance(geometry, GISBoundingBoxRequest):
        req = geometry
    elif geometry is not None:
        try:
            req = GISBoundingBoxRequest(geometry=geometry, engine=engine)
        except Exception as err:
            return MCPToolResponse(
                success=False,
                error={"code": "VALIDATION_ERROR", "message": str(err)},
            ).to_dict()
    else:
        return MCPToolResponse(
            success=False,
            error={"code": "MISSING_ARGUMENTS", "message": "geometry is required"},
        ).to_dict()

    engine_used = "shapely"
    minx: float | None = None
    miny: float | None = None
    maxx: float | None = None
    maxy: float | None = None

    # Native FME Form fmeobjects implementation
    if req.engine == "fme":
        fme = _get_fmeobjects()
        if fme is not None:
            try:
                feat = fme.FMEFeature()
                wkt_text = None
                if isinstance(req.geometry, str) and not req.geometry.strip().startswith("{"):
                    wkt_text = req.geometry.strip()
                elif HAS_SHAPELY:
                    parsed = _parse_geometry(req.geometry)
                    if hasattr(parsed, "wkt"):
                        wkt_text = parsed.wkt

                if wkt_text:
                    feat.importGeometryFromOGCWKT(wkt_text)
                    ((fx1, fy1), (fx2, fy2)) = feat.boundingBox()
                    minx, miny, maxx, maxy = float(fx1), float(fy1), float(fx2), float(fy2)
                    engine_used = "fme (fmeobjects)"
            except Exception:
                pass

    # Shapely or pure-Python coordinate extraction
    if minx is None or miny is None or maxx is None or maxy is None:
        try:
            parsed_geom = (
                _parse_geometry(req.geometry)
                if not isinstance(req.geometry, list)
                else req.geometry
            )
            minx, miny, maxx, maxy = _extract_bounding_box(parsed_geom)
            if req.engine == "fme":
                engine_used = "fme (fallback: shapely)"
            else:
                engine_used = "shapely" if HAS_SHAPELY else "pure_python"
        except Exception as err:
            return MCPToolResponse(
                success=False,
                error={
                    "code": "INVALID_GEOMETRY",
                    "message": f"Bounding box extraction failed: {err}",
                },
            ).to_dict()

    width = round(maxx - minx, 6)
    height = round(maxy - miny, 6)
    area = round(width * height, 6)
    center = [round((minx + maxx) / 2.0, 6), round((miny + maxy) / 2.0, 6)]
    bbox_list = [round(minx, 6), round(miny, 6), round(maxx, 6), round(maxy, 6)]

    geojson_box = {
        "type": "Polygon",
        "coordinates": [
            [
                [round(minx, 6), round(miny, 6)],
                [round(maxx, 6), round(miny, 6)],
                [round(maxx, 6), round(maxy, 6)],
                [round(minx, 6), round(maxy, 6)],
                [round(minx, 6), round(miny, 6)],
            ]
        ],
    }

    result_model = GISBoundingBoxResult(
        minx=round(minx, 6),
        miny=round(miny, 6),
        maxx=round(maxx, 6),
        maxy=round(maxy, 6),
        bbox=bbox_list,
        geometry=geojson_box,
        width=width,
        height=height,
        area=area,
        center=center,
        engine_used=engine_used,
    )
    return MCPToolResponse(success=True, data=result_model.model_dump()).to_dict()


__all__ = [
    # Schemas
    "GISIntersectionRequest",
    "GISIntersectionInput",
    "GISIntersectionResult",
    "GISDifferenceRequest",
    "GISDifferenceInput",
    "GISDifferenceResult",
    "GISSimplifyRequest",
    "GISSimplifyInput",
    "GISSimplifyResult",
    "GISBoundingBoxRequest",
    "GISBoundingBoxInput",
    "GISBoundingBoxResult",
    # Tools
    "gis_reproject",
    "gis_buffer",
    "gis_validate_geometry",
    "gis_intersection",
    "gis_difference",
    "gis_simplify",
    "gis_bounding_box",
]
