"""
PDF exporter for PPTX files.
Uses LibreOffice CLI if available, otherwise skips with a warning.
"""

import logging
import os
import shutil
import subprocess
import sys
from typing import Optional

logger = logging.getLogger(__name__)


def _find_libreoffice() -> Optional[str]:
    """Find LibreOffice executable on the system."""
    # Check common names in PATH
    for name in ['libreoffice', 'soffice', 'soffice.exe', 'libreoffice.exe']:
        path = shutil.which(name)
        if path:
            return path

    # Check common install locations on Windows
    if sys.platform == 'win32':
        for prog_dir in [
            os.environ.get('PROGRAMFILES', r'C:\Program Files'),
            os.environ.get('PROGRAMFILES(X86)', r'C:\Program Files (x86)'),
        ]:
            if prog_dir:
                lo_path = os.path.join(prog_dir, 'LibreOffice', 'program', 'soffice.exe')
                if os.path.isfile(lo_path):
                    return lo_path

    # Check common install locations on macOS
    if sys.platform == 'darwin':
        mac_path = '/Applications/LibreOffice.app/Contents/MacOS/soffice'
        if os.path.isfile(mac_path):
            return mac_path

    return None


def export_pdf(pptx_path: str, pdf_path: Optional[str] = None) -> str:
    """Convert a PPTX file to PDF using LibreOffice.

    Args:
        pptx_path: Path to the input .pptx file.
        pdf_path: Optional output PDF path. If None, uses same name as pptx
                  with .pdf extension.

    Returns:
        The PDF file path on success, or empty string if LibreOffice is not
        available or conversion fails.
    """
    if not os.path.isfile(pptx_path):
        logger.warning("PPTX file not found: %s", pptx_path)
        return ''

    lo_bin = _find_libreoffice()
    if not lo_bin:
        logger.warning(
            "LibreOffice not found. PDF export skipped. "
            "Install LibreOffice for PDF export support: https://www.libreoffice.org/"
        )
        return ''

    # Determine output directory and filename
    pptx_dir = os.path.dirname(os.path.abspath(pptx_path))
    pptx_base = os.path.splitext(os.path.basename(pptx_path))[0]

    if pdf_path is None:
        pdf_path = os.path.join(pptx_dir, f'{pptx_base}.pdf')

    out_dir = os.path.dirname(os.path.abspath(pdf_path))

    try:
        cmd = [
            lo_bin,
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', out_dir,
            os.path.abspath(pptx_path),
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            logger.warning("LibreOffice conversion failed: %s", result.stderr)
            return ''

        # LibreOffice outputs to outdir with the same base name
        lo_output = os.path.join(out_dir, f'{pptx_base}.pdf')

        # If the desired pdf_path differs from what LO produced, rename
        if os.path.abspath(lo_output) != os.path.abspath(pdf_path):
            if os.path.isfile(lo_output):
                os.replace(lo_output, pdf_path)

        if os.path.isfile(pdf_path):
            logger.info("PDF exported to: %s", pdf_path)
            return pdf_path
        else:
            logger.warning("PDF file was not created.")
            return ''

    except subprocess.TimeoutExpired:
        logger.warning("LibreOffice conversion timed out.")
        return ''
    except Exception as e:
        logger.warning("PDF export failed: %s", e)
        return ''
