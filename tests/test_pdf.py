import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from docnav.processors import PDFProcessor
import asyncio

processor = PDFProcessor()


async def main():
    document = await processor.process(Path("tests/test_report_pdf/txt/test_report_pdf_origin.pdf"))
    # print(document.get_outline(7))
    print(document.source_text)


# Run the async function
asyncio.run(main())
