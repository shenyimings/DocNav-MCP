"""Tests for document navigator."""

import asyncio
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from docnav.navigator import DocumentNavigator, DocumentCompass


async def main():
    """Main test function."""
    navigator = DocumentNavigator()
    compass: DocumentCompass
    doc_id, compass = await navigator.load_document_from_file(
        Path("./tests/test_report.md")
    )
    outline = compass.get_outline()
    print(outline)

    context = compass.get_section("h2_1635")
    print(context)

    print(navigator.loaded_documents)
    navigate_context = navigator.navigate(doc_id, "h2_1635")
    print(navigate_context)


if __name__ == "__main__":
    asyncio.run(main())
