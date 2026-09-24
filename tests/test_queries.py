import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rich.console import Console
from main import _build_report_panel, _build_retriever_panel
from src.graph import app

SCREENSHOTS_DIR = ROOT_DIR / "docs" / "screenshots"

TEST_CASES = [
    {
        "filename": "01_international_travel_policy.png",
        "query": "What is the policy on international travel?",
        "expected_section": "SECTION 1",
    },
    {
        "filename": "02_power_banks_and_ecigarettes.png",
        "query": "What are the rules for carrying power banks and e-cigarettes?",
        "expected_section": "SECTION 6",
    },
    {
        "filename": "03_traveling_with_pets_thai.png",
        "query": "พาสัตว์เลี้ยงขึ้นเครื่องบินมีเงื่อนไขและค่าใช้จ่ายเท่าไหร่?",
        "expected_section": "SECTION 11",
    },
    {
        "filename": "04_flight_delay_thai.png",
        "query": "เครื่องช้า 3 ชั่วโมง",
        "expected_section": "SECTION 8",
    },
    {
        "filename": "05_out_of_scope_cryptocurrency.png",
        "query": "Can I pay for excess baggage fees using Bitcoin or cryptocurrency?",
        "expected_section": "SECTION 4",
    },
]


def _save_console_screenshot(console: Console, output_path: Path, title: str) -> None:
    """Export recorded Rich console output directly to a high-DPI PNG screenshot."""
    svg = console.export_svg(title=title)
    svg = re.sub(r' textLength="[^"]+"(?=>[^<]*[\u0e00-\u0e7f])', "", svg)
    svg = svg.replace("font-size: 20px", "font-size: 20.33px")

    with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", encoding="utf-8") as tmp_svg:
        tmp_svg.write(svg)
        tmp_svg.flush()
        subprocess.run(
            ["rsvg-convert", "-z", "2", tmp_svg.name, "-o", str(output_path)],
            check=True,
        )


class TestKnowledgeRAGQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        for old_file in SCREENSHOTS_DIR.glob("*.png"):
            old_file.unlink()

    def test_queries_and_generate_screenshots(self) -> None:
        for case in TEST_CASES:
            query = case["query"]
            filename = case["filename"]
            expected_section = case["expected_section"]

            with self.subTest(query=query):
                result = app.invoke(
                    {
                        "query": query,
                        "search_queries": [],
                        "retrieved_snippets": [],
                        "retrieval_details": [],
                        "final_report": "",
                    }
                )

                snippets = result.get("retrieved_snippets", [])
                final_report = result.get("final_report", "").strip()

                self.assertTrue(snippets, f"No snippets retrieved for query: {query}")
                self.assertTrue(
                    any(expected_section in s for s in snippets),
                    f"Expected {expected_section} in retrieved snippets for query: {query}",
                )
                self.assertTrue(final_report, f"Empty final report for query: {query}")

                record_console = Console(record=True, width=120)
                record_console.print(f'[dim]$ python main.py "{query}"[/dim]\n')
                record_console.print(f"[bold cyan]Query:[/bold cyan] {query}")
                record_console.print(
                    _build_retriever_panel(
                        result.get("search_queries", []),
                        result.get("retrieval_details", []),
                    )
                )
                record_console.print(_build_report_panel(final_report))

                output_path = SCREENSHOTS_DIR / filename
                _save_console_screenshot(
                    record_console,
                    output_path=output_path,
                    title=f'python main.py "{query}"',
                )
                self.assertTrue(output_path.exists(), f"Screenshot not created: {output_path}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
