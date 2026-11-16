#!/usr/bin/env python3
"""Build Standalone Executable for FME MCP.

Bundles FME MCP (fme-mcp-ultra) into a single, self-contained standalone executable
using PyInstaller. Requires zero Python installation on the target machine.

Usage:
    python scripts/build_standalone.py
    python scripts/build_standalone.py --output-dir dist/bin --clean
"""

from __future__ import annotations

import argparse
import hashlib
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path


def get_project_root() -> Path:
    """Return the repository root directory."""
    return Path(__file__).resolve().parent.parent


def ensure_pyinstaller() -> None:
    """Verify that PyInstaller is installed in the current Python environment."""
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("[!] PyInstaller is not installed in the active Python environment.")
        print("[*] Attempting to install pyinstaller...")
        installed = False
        for installer_cmd in [
            ["uv", "pip", "install", "pyinstaller>=6.0.0"],
            [sys.executable, "-m", "pip", "install", "pyinstaller>=6.0.0"],
            ["pip", "install", "pyinstaller>=6.0.0"],
        ]:
            try:
                subprocess.check_call(installer_cmd)
                installed = True
                print("[+] PyInstaller successfully installed.")
                break
            except Exception:
                continue

        if not installed:
            print("[-] Failed to install PyInstaller automatically.")
            print(
                "    Please install manually: pip install pyinstaller (or uv pip install pyinstaller)"
            )
            sys.exit(1)


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def create_entrypoint(temp_dir: Path) -> Path:
    """Generate a clean standalone entrypoint script."""
    entrypoint_path = temp_dir / "_standalone_entrypoint.py"
    code = (
        "# Auto-generated standalone entrypoint for FME MCP (fme-mcp-ultra)\n"
        "import sys\n"
        "from fme_mcp_ultra.cli.main import cli\n\n"
        "if __name__ == '__main__':\n"
        "    cli()\n"
    )
    entrypoint_path.write_text(code, encoding="utf-8")
    return entrypoint_path


def build_binary(
    output_dir: Path,
    binary_name: str = "fme-mcp",
    clean: bool = True,
    debug: bool = False,
    onefile: bool = True,
    test_binary: bool = True,
) -> Path:
    """Bundle FME MCP into a standalone executable using PyInstaller."""
    ensure_pyinstaller()

    root_dir = get_project_root()
    src_dir = root_dir / "src"
    build_dir = root_dir / "build" / "pyinstaller"

    output_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    is_windows = platform.system() == "Windows"
    target_exe_name = f"{binary_name}.exe" if is_windows else binary_name
    target_path = output_dir / target_exe_name

    print("=" * 70)
    print(" FME MCP - Standalone Binary Builder")
    print("=" * 70)
    print(f"[*] Project root: {root_dir}")
    print(f"[*] Source path:  {src_dir}")
    print(f"[*] Output dir:   {output_dir}")
    print(f"[*] Target exe:   {target_path}")
    print(f"[*] OS Platform:  {platform.system()} ({platform.machine()})")
    print(f"[*] Python:       {sys.version.split()[0]} ({sys.executable})")

    # Generate temporary clean entrypoint
    entrypoint = create_entrypoint(build_dir)

    # Core hidden imports required by fme-mcp-ultra and its dependencies
    hidden_imports = [
        "fme_mcp_ultra",
        "fme_mcp_ultra.cli",
        "fme_mcp_ultra.cli.main",
        "fme_mcp_ultra.core",
        "fme_mcp_ultra.core.config",
        "fme_mcp_ultra.core.errors",
        "fme_mcp_ultra.core.logging",
        "fme_mcp_ultra.core.schema",
        "fme_mcp_ultra.fme",
        "fme_mcp_ultra.fme.fme_bridge",
        "fme_mcp_ultra.fme.fme_form_client",
        "fme_mcp_ultra.fme.fme_flow_client",
        "fme_mcp_ultra.fme.transformer_bridge",
        "fme_mcp_ultra.fme.compatibility_layer",
        "fme_mcp_ultra.fme.parameter_mapper",
        "fme_mcp_ultra.security",
        "fme_mcp_ultra.security.audit_log",
        "fme_mcp_ultra.security.command_guard",
        "fme_mcp_ultra.server",
        "fme_mcp_ultra.server.mcp_server",
        "fme_mcp_ultra.tools",
        "fme_mcp_ultra.tools.ai.ai_tools",
        "fme_mcp_ultra.tools.catalog.catalog_tools",
        "fme_mcp_ultra.tools.datasets.dataset_tools",
        "fme_mcp_ultra.tools.governance.governance_tools",
        "fme_mcp_ultra.tools.mcp_federation.federation_tools",
        "fme_mcp_ultra.tools.orchestration.workflow_tools",
        "fme_mcp_ultra.tools.quality.quality_tools",
        "fme_mcp_ultra.tools.spatial.spatial_tools",
        "fme_mcp_ultra.tools.utilities.util_tools",
        "fme_mcp_ultra.tools.workspaces.workspace_tools",
        "anyio._backends._asyncio",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
    ]

    # Packages to collect all data and submodules
    collect_packages = [
        "fme_mcp_ultra",
        "mcp",
        "starlette",
        "uvicorn",
        "fastapi",
        "pydantic",
        "pydantic_settings",
        "pydantic_core",
        "rich",
        "typer",
        "anyio",
    ]

    # Conditionally collect shapely if installed
    try:
        import shapely  # noqa: F401

        collect_packages.append("shapely")
    except ImportError:
        pass

    pyinstaller_args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        binary_name,
        "--paths",
        str(src_dir),
        "--distpath",
        str(output_dir),
        "--workpath",
        str(build_dir / "work"),
        "--specpath",
        str(build_dir),
        "--noconfirm",
    ]

    if onefile:
        pyinstaller_args.append("--onefile")

    if clean:
        pyinstaller_args.append("--clean")

    if debug:
        pyinstaller_args.extend(["--log-level", "DEBUG"])
    else:
        pyinstaller_args.extend(["--log-level", "WARN"])

    for imp in hidden_imports:
        pyinstaller_args.extend(["--hidden-import", imp])

    for pkg in collect_packages:
        pyinstaller_args.extend(["--collect-all", pkg])

    # Entrypoint script
    pyinstaller_args.append(str(entrypoint))

    print("[*] Running PyInstaller bundling process...")
    start_time = time.time()
    try:
        subprocess.check_call(pyinstaller_args)
    except subprocess.CalledProcessError as e:
        print(f"[-] PyInstaller failed with exit code {e.returncode}")
        sys.exit(e.returncode)

    elapsed = time.time() - start_time
    print(f"[+] PyInstaller finished in {elapsed:.1f}s")

    if not target_path.exists():
        print(f"[-] Target binary not found at expected location: {target_path}")
        sys.exit(1)

    # Make executable on Unix
    if not is_windows:
        target_path.chmod(0o755)

    size_mb = target_path.stat().st_size / (1024 * 1024)
    sha256_hash = compute_sha256(target_path)

    # Write SHA256 checksum file
    checksum_file = target_path.with_name(f"{target_path.name}.sha256")
    checksum_file.write_text(f"{sha256_hash}  {target_path.name}\n", encoding="utf-8")

    print("-" * 70)
    print("[+] Standalone binary successfully generated!")
    print(f"    Path:     {target_path}")
    print(f"    Size:     {size_mb:.2f} MB")
    print(f"    SHA256:   {sha256_hash}")
    print(f"    Checksum: {checksum_file}")
    print("-" * 70)

    # Verification run
    if test_binary:
        print("[*] Verifying standalone binary execution...")
        try:
            res = subprocess.run(
                [str(target_path), "version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            print(f"[+] Output from '{target_path.name} version':")
            print(f"    {res.stdout.strip()}")
            print("[+] Standalone binary verified successfully!")
        except Exception as e:
            print(f"[-] Standalone binary smoke test failed: {e}")
            sys.exit(1)

    return target_path


def main() -> None:
    """CLI interface for building standalone executables."""
    parser = argparse.ArgumentParser(
        description="Bundle FME MCP (fme-mcp-ultra) into a single self-contained standalone executable."
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=get_project_root() / "dist",
        help="Destination directory for the built binary (default: dist)",
    )
    parser.add_argument(
        "--binary-name",
        "-n",
        type=str,
        default="fme-mcp",
        help="Base binary name (default: fme-mcp)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=True,
        help="Clean PyInstaller cache and build artifacts before bundling",
    )
    parser.add_argument(
        "--no-clean",
        action="store_false",
        dest="clean",
        help="Keep PyInstaller cache and build artifacts",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable PyInstaller debug logging",
    )
    parser.add_argument(
        "--no-onefile",
        action="store_false",
        dest="onefile",
        help="Build directory-based distribution instead of a single executable file",
    )
    parser.add_argument(
        "--no-test",
        action="store_false",
        dest="test_binary",
        help="Skip smoke test execution of the built binary",
    )

    args = parser.parse_args()

    build_binary(
        output_dir=args.output_dir,
        binary_name=args.binary_name,
        clean=args.clean,
        debug=args.debug,
        onefile=args.onefile,
        test_binary=args.test_binary,
    )


if __name__ == "__main__":
    main()
