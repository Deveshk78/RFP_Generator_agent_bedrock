#!/usr/bin/env python3
"""RFP Agent CLI - Amazon Bedrock + DynamoDB."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.bedrock_agent import BedrockAgent
from src.config import get_settings
from src.dynamodb_store import DynamoDBStore

console = Console()


def _read_text(value: str | None, file_path: str | None) -> str:
    if file_path:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return path.read_text(encoding="utf-8")
    if value:
        return value
    raise ValueError("Provide --content/--profile or --file/--profile-file")


def cmd_init(store: DynamoDBStore) -> None:
    store.ensure_table()
    console.print("[green]DynamoDB table ready.[/green]")


def cmd_create(store: DynamoDBStore, args: argparse.Namespace) -> None:
    content = _read_text(args.content, args.file)
    item = store.create_rfp(args.title, content)
    console.print(
        Panel(
            f"[bold]{item['title']}[/bold]\nID: {item['rfp_id']}",
            title="RFP Created",
            border_style="green",
        )
    )


def cmd_list(store: DynamoDBStore) -> None:
    items = store.list_rfps()
    if not items:
        console.print("[yellow]No RFPs found. Use create to add one.[/yellow]")
        return

    table = Table(title="RFP Documents")
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Created")

    for item in items:
        table.add_row(
            item["rfp_id"][:8] + "...",
            item["title"],
            item.get("status", "draft"),
            item.get("created_at", ""),
        )
    console.print(table)


def cmd_show(store: DynamoDBStore, args: argparse.Namespace) -> None:
    item = store.get_rfp(args.rfp_id)
    if not item:
        console.print(f"[red]RFP not found: {args.rfp_id}[/red]")
        sys.exit(1)

    console.print(
        Panel(
            f"ID: {item['rfp_id']}\nStatus: {item.get('status', 'draft')}\n\n{item['content']}",
            title=item["title"],
        )
    )


def cmd_analyze(store: DynamoDBStore, agent: BedrockAgent, args: argparse.Namespace) -> None:
    item = store.get_rfp(args.rfp_id)
    if not item:
        console.print(f"[red]RFP not found: {args.rfp_id}[/red]")
        sys.exit(1)

    console.print("[blue]Analyzing RFP with Amazon Bedrock...[/blue]")
    analysis = agent.analyze_rfp(item["title"], item["content"])
    store.save_analysis(args.rfp_id, analysis)
    console.print(Markdown(analysis))


def cmd_propose(store: DynamoDBStore, agent: BedrockAgent, args: argparse.Namespace) -> None:
    item = store.get_rfp(args.rfp_id)
    if not item:
        console.print(f"[red]RFP not found: {args.rfp_id}[/red]")
        sys.exit(1)

    company_profile = _read_text(args.profile, args.profile_file)
    latest_analysis = store.get_latest_analysis(args.rfp_id)
    analysis_text = latest_analysis["analysis"] if latest_analysis else None

    console.print("[blue]Generating proposal with Amazon Bedrock...[/blue]")
    proposal = agent.generate_proposal(
        title=item["title"],
        content=item["content"],
        company_name=args.company,
        company_profile=company_profile,
        analysis=analysis_text,
    )
    store.save_proposal(args.rfp_id, args.company, proposal)
    console.print(Markdown(proposal))


def cmd_chat(store: DynamoDBStore, agent: BedrockAgent, args: argparse.Namespace) -> None:
    item = store.get_rfp(args.rfp_id)
    if not item:
        console.print(f"[red]RFP not found: {args.rfp_id}[/red]")
        sys.exit(1)

    latest_analysis = store.get_latest_analysis(args.rfp_id)
    latest_proposal = store.get_latest_proposal(args.rfp_id)
    history_rows = store.get_chat_history(args.rfp_id)

    history = [
        {"role": row["role"], "content": row["content"]} for row in history_rows
    ]

    console.print(
        Panel(
            f"Chatting about: {item['title']}\nType 'exit' or 'quit' to leave.",
            title="RFP Chat",
            border_style="blue",
        )
    )

    while True:
        try:
            question = console.input("[bold cyan]You:[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Chat ended.[/yellow]")
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            console.print("[yellow]Chat ended.[/yellow]")
            break

        store.save_message(args.rfp_id, "user", question)
        history.append({"role": "user", "content": question})

        answer = agent.chat_about_rfp(
            title=item["title"],
            content=item["content"],
            question=question,
            history=history[:-1],
            analysis=latest_analysis["analysis"] if latest_analysis else None,
            proposal=latest_proposal["proposal"] if latest_proposal else None,
        )

        store.save_message(args.rfp_id, "assistant", answer)
        history.append({"role": "assistant", "content": answer})
        console.print(Panel(Markdown(answer), title="Agent", border_style="green"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="RFP Agent powered by Amazon Bedrock and DynamoDB"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create DynamoDB table if missing")

    create = sub.add_parser("create", help="Store a new RFP document")
    create.add_argument("--title", required=True, help="RFP title")
    create.add_argument("--content", help="RFP text content")
    create.add_argument("--file", help="Path to RFP text/markdown file")

    sub.add_parser("list", help="List stored RFP documents")

    show = sub.add_parser("show", help="Show an RFP by ID")
    show.add_argument("--rfp-id", required=True, help="RFP UUID")

    analyze = sub.add_parser("analyze", help="Analyze an RFP with Bedrock")
    analyze.add_argument("--rfp-id", required=True, help="RFP UUID")

    propose = sub.add_parser("propose", help="Generate a proposal draft")
    propose.add_argument("--rfp-id", required=True, help="RFP UUID")
    propose.add_argument("--company", required=True, help="Company name")
    propose.add_argument("--profile", help="Company profile text")
    propose.add_argument("--profile-file", help="Path to company profile file")

    chat = sub.add_parser("chat", help="Interactive Q&A about an RFP")
    chat.add_argument("--rfp-id", required=True, help="RFP UUID")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        settings = get_settings()
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        sys.exit(1)

    store = DynamoDBStore(settings)
    agent = BedrockAgent(settings)

    try:
        if args.command == "init":
            cmd_init(store)
        elif args.command == "create":
            cmd_create(store, args)
        elif args.command == "list":
            cmd_list(store)
        elif args.command == "show":
            cmd_show(store, args)
        elif args.command == "analyze":
            cmd_analyze(store, agent, args)
        elif args.command == "propose":
            cmd_propose(store, agent, args)
        elif args.command == "chat":
            cmd_chat(store, agent, args)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        sys.exit(1)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        sys.exit(1)
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
