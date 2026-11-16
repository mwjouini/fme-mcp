# Graph Report - fme-mcp-ultra  (2026-11-16)

## Corpus Check
- Corpus is ~37,913 words - fits in a single context window. You may not need a graph.

## Summary
- 998 nodes · 1617 edges · 70 communities (43 shown, 27 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 69 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- MCP Server & FME AI Tools
- MkDocs Architecture & Guides
- CI/CD & PyPI Release Pipeline
- Security Redaction & Vulnerability Scans
- Multi-Platform Binary Releases
- MCP Server & FME AI Tools
- Test Suite & Quality Assurance
- FME Socket IPC Bridge
- Security Redaction & Vulnerability Scans
- MCPConnector FME Transformer Bridge
- MCP Server & FME AI Tools
- Rich CLI & Doctor Diagnostics
- CI/CD & PyPI Release Pipeline
- Spatial Analytics & GIS Operations
- Documentation Deployment
- Rich CLI & Doctor Diagnostics
- FME Socket IPC Bridge
- Pydantic Schema & Core Models
- Pydantic Schema & Core Models
- Documentation Deployment
- Module (compose, context)
- Security Redaction & Vulnerability Scans
- Rich CLI & Doctor Diagnostics
- Security Redaction & Vulnerability Scans
- Module (report, label)
- Security Redaction & Vulnerability Scans
- Rich CLI & Doctor Diagnostics
- MCP Server & FME AI Tools
- Spatial Analytics & GIS Operations
- Module (request, label)
- MCP Server & FME AI Tools
- Test Suite & Quality Assurance
- Security Redaction & Vulnerability Scans
- Rich CLI & Doctor Diagnostics
- Security Redaction & Vulnerability Scans
- Spatial Analytics & GIS Operations
- Rich CLI & Doctor Diagnostics
- Module (basesettings, pathlib)
- Spatial Analytics & GIS Operations
- Module (workspaces, workspaces)
- Module (exception, fmemcperror)
- Rich CLI & Doctor Diagnostics
- Spatial Analytics & GIS Operations
- MCPConnector FME Transformer Bridge
- Security Redaction & Vulnerability Scans
- Module (fmecompatibilitylayer, info)
- Dataset Profiling & Quality Scoring
- Spatial Analytics & GIS Operations
- Test Suite & Quality Assurance
- Security Redaction & Vulnerability Scans
- Security Redaction & Vulnerability Scans
- MCP Server & FME AI Tools
- Security Redaction & Vulnerability Scans
- Spatial Analytics & GIS Operations
- Rich CLI & Doctor Diagnostics
- Pydantic Schema & Core Models
- MCP Server & FME AI Tools
- MCP Server & FME AI Tools
- Test Suite & Quality Assurance
- Test Suite & Quality Assurance
- Test Suite & Quality Assurance
- MCP Server & FME AI Tools
- Pydantic Schema & Core Models
- Module (tool, entry)
- Module (funding, github)
- Module (mcp)

## God Nodes (most connected - your core abstractions)
1. `MCPToolResponse` - 58 edges
2. `FMEFormClient` - 19 edges
3. `FMEBridgeServer` - 17 edges
4. `with` - 15 edges
5. `gis_intersection()` - 14 edges
6. `gis_simplify()` - 14 edges
7. `gis_bounding_box()` - 14 edges
8. `FMEMCPError` - 13 edges
9. `gis_difference()` - 13 edges
10. `nav` - 12 edges

## Surprising Connections (you probably didn't know these)
- `test_command_guard_blocks_shell_metacharacters()` --uses--> `CommandInjectionError`  [INFERRED]
  tests/unit/test_security.py → src/fme_mcp/core/errors.py
- `test_command_guard_blocks_unauthorised_binary()` --uses--> `CommandInjectionError`  [INFERRED]
  tests/unit/test_security.py → src/fme_mcp/core/errors.py
- `test_mcp_connector_transformer_alias()` --uses--> `MCPConnectorTransformer`  [INFERRED]
  tests/unit/test_transformer_bridge.py → src/fme_mcp/fme/transformer_bridge.py
- `test_gis_intersection_with_pydantic_request()` --uses--> `GISIntersectionRequest`  [INFERRED]
  tests/unit/test_enhanced_features.py → src/fme_mcp/tools/spatial/spatial_tools.py
- `test_gis_difference_with_pydantic_request_and_wkt()` --uses--> `GISDifferenceRequest`  [INFERRED]
  tests/unit/test_enhanced_features.py → src/fme_mcp/tools/spatial/spatial_tools.py

## Import Cycles
- None detected.

## Communities (70 total, 27 thin omitted)

### Community 0 - "MCP Server & FME AI Tools"
Cohesion: 0.08
Nodes (22): ai_explain_workspace(), ai_suggest_transformations(), fme_audit_performance(), fme_compare_workspaces(), fme_diagnose(), fme_discover_workspaces(), fme_export_markdown_docs(), fme_get_workspace() (+14 more)

### Community 1 - "MkDocs Architecture & Guides"
Cohesion: 0.04
Nodes (44): Code of Conduct, Contributing, Roadmap, FME 2026 Parity, FME Version Compatibility (2018–2026+), Docker, Overview, markdown_extensions (+36 more)

### Community 2 - "CI/CD & PyPI Release Pipeline"
Cohesion: 0.06
Nodes (37): name, runs-on, steps, name, runs-on, steps, GITHUB_TOKEN, jobs (+29 more)

### Community 3 - "Security Redaction & Vulnerability Scans"
Cohesion: 0.09
Nodes (8): MCPToolResponse, ai_explain_workspace(), ai_suggest_transformations(), mcp_list_servers(), mcp_register_server(), workflow_create(), workflow_get(), workflow_run()

### Community 4 - "Multi-Platform Binary Releases"
Cohesion: 0.05
Nodes (36): name, runs-on, steps, strategy, GITHUB_TOKEN, arch, binary_name, os (+28 more)

### Community 5 - "MCP Server & FME AI Tools"
Cohesion: 0.07
Nodes (15): fme_execute_python(), fme_info(), fme_list_packages(), fme_list_transformers(), util_ping(), util_validate_coordinates(), util_version(), fme_execute_python() (+7 more)

### Community 6 - "Test Suite & Quality Assurance"
Cohesion: 0.08
Nodes (29): jobs, lint-and-typecheck, unit-tests, name, runs-on, steps, os, python-version (+21 more)

### Community 7 - "FME Socket IPC Bridge"
Cohesion: 0.11
Nodes (3): FMEBridgeClient, FMEBridgeServer, test_fme_bridge_loopback_socket()

### Community 8 - "Security Redaction & Vulnerability Scans"
Cohesion: 0.08
Nodes (24): GITHUB_TOKEN, jobs, security-scans, name, on, pull_request, push, schedule (+16 more)

### Community 9 - "MCPConnector FME Transformer Bridge"
Cohesion: 0.11
Nodes (5): MCPConnectorTransformer, MockFeature, test_mcp_connector_transformer_alias(), test_transformer_bridge_connected_send(), test_transformer_bridge_offline_graceful()

### Community 10 - "MCP Server & FME AI Tools"
Cohesion: 0.13
Nodes (9): data_profile(), data_read_metadata(), quality_score_dataset(), data_profile(), data_read_metadata(), quality_score_dataset(), test_data_profile_computes_nulls(), test_data_read_metadata_csv() (+1 more)

### Community 11 - "Rich CLI & Doctor Diagnostics"
Cohesion: 0.12
Nodes (5): default_callback(), doctor(), inspect(), serve(), version()

### Community 12 - "CI/CD & PyPI Release Pipeline"
Cohesion: 0.10
Nodes (20): jobs, pypi-publish, name, on, release, workflow_dispatch, contents, id-token (+12 more)

### Community 13 - "Spatial Analytics & GIS Operations"
Cohesion: 0.14
Nodes (9): gis_intersection(), test_fme_audit_performance_real_workspace(), test_gis_difference_overlapping_polygons(), test_gis_difference_with_pydantic_request_and_wkt(), test_gis_intersection_disjoint_polygons(), test_gis_intersection_error_handling(), test_gis_intersection_overlapping_polygons(), test_gis_intersection_with_pydantic_request() (+1 more)

### Community 14 - "Documentation Deployment"
Cohesion: 0.10
Nodes (19): name, runs-on, steps, GITHUB_TOKEN, jobs, deploy-docs, name, on (+11 more)

### Community 15 - "Rich CLI & Doctor Diagnostics"
Cohesion: 0.19
Nodes (6): build_binary(), compute_sha256(), create_entrypoint(), ensure_pyinstaller(), get_project_root(), main()

### Community 17 - "Pydantic Schema & Core Models"
Cohesion: 0.13
Nodes (6): GISBoundingBoxResult, GISDifferenceRequest, GISDifferenceResult, GISIntersectionRequest, GISIntersectionResult, GISSimplifyResult

### Community 18 - "Pydantic Schema & Core Models"
Cohesion: 0.11
Nodes (18): description, type, properties, type, description, type, description, type (+10 more)

### Community 19 - "Documentation Deployment"
Cohesion: 0.19
Nodes (4): _clean_html_text(), _extract_workspace_components(), _generate_markdown_docs(), _parse_fmw_xml()

### Community 20 - "Module (compose, context)"
Cohesion: 0.12
Nodes (16): context, dockerfile, build, container_name, environment, healthcheck, image, ports (+8 more)

### Community 21 - "Security Redaction & Vulnerability Scans"
Cohesion: 0.21
Nodes (6): SecurityError, RBACEngine, Role, test_rbac_enforcement_raises_on_denial(), test_rbac_permits_admin(), test_rbac_restricts_read_only_user()

### Community 24 - "Security Redaction & Vulnerability Scans"
Cohesion: 0.19
Nodes (3): on_workspace_shutdown(), on_workspace_startup(), send_bridge_event()

### Community 25 - "Module (report, label)"
Cohesion: 0.13
Nodes (14): label, placeholder, render, value, body, attributes, id, type (+6 more)

### Community 26 - "Security Redaction & Vulnerability Scans"
Cohesion: 0.23
Nodes (5): PathTraversalError, PathGuard, test_path_guard_allows_valid_subpath(), test_path_guard_blocks_traversal_escape(), test_path_guard_rejects_null_byte()

### Community 28 - "MCP Server & FME AI Tools"
Cohesion: 0.15
Nodes (7): catalog_get_lineage(), catalog_register_asset(), catalog_search_assets(), catalog_get_lineage(), catalog_register_asset(), catalog_search_assets(), test_catalog_register_and_search()

### Community 29 - "Spatial Analytics & GIS Operations"
Cohesion: 0.15
Nodes (7): gis_bounding_box(), GISBoundingBoxRequest, test_gis_bounding_box_error_handling(), test_gis_bounding_box_from_4_element_array(), test_gis_bounding_box_from_coordinate_list(), test_gis_bounding_box_from_geojson_polygon(), test_gis_bounding_box_with_pydantic_request_and_wkt()

### Community 30 - "Module (request, label)"
Cohesion: 0.15
Nodes (12): label, placeholder, body, attributes, id, type, validations, description (+4 more)

### Community 31 - "MCP Server & FME AI Tools"
Cohesion: 0.15
Nodes (6): gov_classify_dataset(), gov_get_tenant_config(), gov_redact_pii(), gov_classify_dataset(), gov_get_tenant_config(), gov_redact_pii()

### Community 32 - "Test Suite & Quality Assurance"
Cohesion: 0.20
Nodes (5): fme_audit_performance(), complex_sample_fmw(), test_fme_audit_performance_corrupt_file(), test_fme_audit_performance_detects_bottlenecks(), test_fme_audit_performance_strict_mode()

### Community 33 - "Security Redaction & Vulnerability Scans"
Cohesion: 0.17
Nodes (11): label, placeholder, value, body, attributes, id, type, description (+3 more)

### Community 34 - "Rich CLI & Doctor Diagnostics"
Cohesion: 0.24
Nodes (6): build_demo_fmw(), main(), build_fmx_content(), encode_mapping_python(), encode_xml_python(), main()

### Community 36 - "Spatial Analytics & GIS Operations"
Cohesion: 0.18
Nodes (6): gis_simplify(), GISSimplifyRequest, test_gis_simplify_error_handling(), test_gis_simplify_reduces_collinear_vertices(), test_gis_simplify_with_pydantic_request_and_polygon(), test_gis_simplify_zero_tolerance_preserves_vertices()

### Community 37 - "Rich CLI & Doctor Diagnostics"
Cohesion: 0.24
Nodes (4): test_mcp_server_call_ping(), test_mcp_server_call_reproject(), test_mcp_server_inspect_workspace(), test_mcp_server_lists_all_tools()

### Community 39 - "Spatial Analytics & GIS Operations"
Cohesion: 0.20
Nodes (6): _count_coords_list(), _count_vertices(), _extract_bounding_box(), _collect(), gis_validate_geometry(), test_gis_validate_geometry_detects_unclosed_polygon()

### Community 40 - "Module (workspaces, workspaces)"
Cohesion: 0.18
Nodes (5): fme_compare_workspaces(), fme_discover_workspaces(), fme_get_workspace(), fme_get_workspace_parameters(), fme_run_workspace()

### Community 42 - "Rich CLI & Doctor Diagnostics"
Cohesion: 0.44
Nodes (8): check_and_configure(), print_banner(), print_detail(), print_step(), print_success(), print_warn(), install.sh script, update_json_client()

### Community 43 - "Spatial Analytics & GIS Operations"
Cohesion: 0.20
Nodes (5): _clean_geojson(), gis_difference(), _parse_geometry(), test_gis_difference_error_handling(), test_gis_difference_total_subtraction()

### Community 44 - "MCPConnector FME Transformer Bridge"
Cohesion: 0.28
Nodes (3): ensure_bridge_started(), is_bridge_running(), test_is_bridge_running_offline()

### Community 46 - "Security Redaction & Vulnerability Scans"
Cohesion: 0.36
Nodes (4): SSRFError, SSRFGuard, test_ssrf_guard_blocks_cloud_metadata(), test_ssrf_guard_blocks_loopback()

### Community 48 - "Dataset Profiling & Quality Scoring"
Cohesion: 0.22
Nodes (4): fme_inspect_canvas(), fme_preview_dataset(), test_fme_inspect_canvas(), test_fme_preview_dataset_csv()

### Community 49 - "Spatial Analytics & GIS Operations"
Cohesion: 0.25
Nodes (5): gis_buffer(), gis_reproject(), test_gis_buffer_creates_valid_geojson_polygon(), test_gis_reproject_wgs84_to_lambert93(), test_gis_reproject_wgs84_to_web_mercator()

### Community 50 - "Test Suite & Quality Assurance"
Cohesion: 0.25
Nodes (4): fme_export_markdown_docs(), test_fme_export_markdown_docs_content(), test_fme_export_markdown_docs_corrupt_file(), test_fme_export_markdown_docs_saves_to_file()

### Community 53 - "MCP Server & FME AI Tools"
Cohesion: 0.33
Nodes (5): PYTHONIOENCODING, PYTHONUNBUFFERED, fme-mcp, uvx, fme-mcp

## Knowledge Gaps
- **6 isolated node(s):** `uvx`, `fme-mcp`, `PYTHONIOENCODING`, `PYTHONUNBUFFERED`, `fme-mcp` (+1 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 509 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MCPToolResponse` connect `Security Redaction & Vulnerability Scans` to `MCP Server & FME AI Tools`, `MCP Server & FME AI Tools`, `Spatial Analytics & GIS Operations`, `Pydantic Schema & Core Models`, `Documentation Deployment`, `MCP Server & FME AI Tools`, `Spatial Analytics & GIS Operations`, `MCP Server & FME AI Tools`, `Test Suite & Quality Assurance`, `Spatial Analytics & GIS Operations`, `Spatial Analytics & GIS Operations`, `Module (workspaces, workspaces)`, `Spatial Analytics & GIS Operations`, `Dataset Profiling & Quality Scoring`, `Spatial Analytics & GIS Operations`, `Test Suite & Quality Assurance`, `MCP Server & FME AI Tools`, `MCP Server & FME AI Tools`, `Test Suite & Quality Assurance`, `Test Suite & Quality Assurance`, `Test Suite & Quality Assurance`, `Pydantic Schema & Core Models`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `FMEFormClient` (e.g. with `WorkspaceExecutionError` and `WorkspaceNotFoundError`) actually correct?**
  _`FMEFormClient` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `uvx`, `fme-mcp`, `PYTHONIOENCODING` to the rest of the system?**
  _6 weakly-connected nodes found - possible missing edges._
- **Should `MCP Server & FME AI Tools` be split into smaller, more focused modules?**
  _Cohesion score 0.07653061224489796 - nodes in this community are weakly interconnected._
- **Why does `FMEFormClient` connect `Rich CLI & Doctor Diagnostics` to `FME Socket IPC Bridge`, `Module (exception, fmemcperror)`, `Rich CLI & Doctor Diagnostics`, `Rich CLI & Doctor Diagnostics`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Should `MkDocs Architecture & Guides` be split into smaller, more focused modules?**
  _Cohesion score 0.044444444444444446 - nodes in this community are weakly interconnected._
- **Why does `FMEBridgeServer` connect `FME Socket IPC Bridge` to `FME Socket IPC Bridge`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._