import sys
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from src.config import settings
from src.graph import app

console = Console()


def _print_error(title: str, message: str) -> None:
    console.print(
        Panel(
            message.strip(),
            title=f"[bold red]{title}[/bold red]",
            border_style="red",
        )
    )


def _build_retriever_panel(search_queries: list, details: list) -> Panel:
    header_lines = [
        f"[bold yellow]Agent Search Query:[/bold yellow] {', '.join(repr(q) for q in search_queries)}"
    ]
    snippet_blocks = []
    for i, item in enumerate(details):
        snippet = item["snippet"]
        score = item.get("score", 0.0)
        matched = ", ".join(item.get("matched_keywords", [])) or "none"
        preview = f"{snippet[:200]}..." if len(snippet) > 200 else snippet
        snippet_blocks.append(
            f"[bold]Snippet {i + 1}[/bold] [dim](TF-IDF Score: {score})[/dim]\n"
            f"[green]Matched Keywords:[/green] {matched}\n"
            f"{preview}"
        )

    panel_body = "\n\n".join(header_lines + snippet_blocks) if snippet_blocks else "No snippets retrieved."
    return Panel(
        panel_body,
        title=f"[bold blue]Data Retriever Agent ({len(details)} snippets)[/bold blue]",
        border_style="blue",
    )


def _build_report_panel(text: str) -> Panel:
    content = Markdown(text) if text.strip() else "[dim]Synthesizing report...[/dim]"
    return Panel(
        content,
        title="[bold green]Report Generator Agent[/bold green]",
        border_style="green",
    )


def run_query(query: str) -> None:
    query = query.strip()
    if not query:
        _print_error("Invalid Input", "Query cannot be empty. Please provide a valid question.")
        return

    console.print(f"\n[bold cyan]Query:[/bold cyan] {query}")

    initial_state = {
        "query": query,
        "search_queries": [],
        "retrieved_snippets": [],
        "retrieval_details": [],
        "final_report": "",
    }

    report_text = ""
    status = console.status("[bold yellow]Data Retriever Agent is searching knowledge_base.txt...", spinner="dots")
    live = Live(_build_report_panel(""), console=console, refresh_per_second=15)
    live_started = False

    try:
        status.start()
        for mode, payload in app.stream(initial_state, stream_mode=["updates", "messages"]):
            if mode == "updates" and "retriever" in payload:
                status.stop()
                ret_data = payload["retriever"]
                console.print(
                    _build_retriever_panel(
                        ret_data.get("search_queries", []),
                        ret_data.get("retrieval_details", []),
                    )
                )
                live.start()
                live_started = True

            elif mode == "messages":
                msg_chunk, metadata = payload
                if metadata.get("langgraph_node") == "reporter" and msg_chunk.content:
                    chunk_str = (
                        msg_chunk.content
                        if isinstance(msg_chunk.content, str)
                        else "".join(
                            b.get("text", "") for b in msg_chunk.content if isinstance(b, dict)
                        )
                    )
                    if chunk_str:
                        report_text += chunk_str
                        if live_started:
                            live.update(_build_report_panel(report_text))

            elif mode == "updates" and "reporter" in payload:
                final_text = payload["reporter"].get("final_report", "") or report_text
                if live_started:
                    live.update(_build_report_panel(final_text))
    except Exception as exc:
        status.stop()
        if live_started:
            live.stop()
        _print_error("Execution Error", f"Failed to process query:\n{exc}")
    finally:
        status.stop()
        if live_started:
            live.stop()


def main() -> None:
    try:
        settings.validate_runtime()
    except (ValueError, FileNotFoundError) as err:
        _print_error("Configuration Error", str(err))
        sys.exit(1)

    if len(sys.argv) > 1:
        run_query(" ".join(sys.argv[1:]))
        return

    console.print("[bold]Knowledge RAG Agents[/bold] (type 'exit' to quit)")
    while True:
        try:
            query = console.input("\n[bold cyan]Ask a question > [/bold cyan]").strip()
            if not query:
                continue
            if query.lower() in {"exit", "quit", "q"}:
                break
            run_query(query)
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()
