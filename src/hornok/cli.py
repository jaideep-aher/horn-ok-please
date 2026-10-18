"""Command line for the audit kit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

from hornok import __version__
from hornok.defense import isolate_instructions
from hornok.gen import composite_attack
from hornok.parse import parse_decision
from hornok.scenes import write_stimuli


def _parse_quad(text: str) -> list[list[float]]:
    parts = [float(p) for p in text.split(",")]
    if len(parts) != 8:
        raise argparse.ArgumentTypeError("quad needs 8 numbers: x,y repeated for TL TR BR BL")
    return [[parts[i], parts[i + 1]] for i in range(0, 8, 2)]


def _cmd_gen(args: argparse.Namespace) -> int:
    image = Image.open(args.base)
    ink = tuple(int(c) for c in args.ink.split(","))
    out = composite_attack(
        image,
        args.text.replace("\\n", "\n"),
        args.quad,
        style=args.style,
        weathering=args.weathering,
        seed=args.seed,
        ink=ink,  # type: ignore[arg-type]
        absorb=args.absorb,
    )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.save(args.out)
    print(args.out)
    return 0


def _cmd_parse(args: argparse.Namespace) -> int:
    raw = args.text if args.text is not None else sys.stdin.read()
    action, rationale = parse_decision(raw)
    print(json.dumps({"action": action, "rationale": rationale}, ensure_ascii=False))
    return 0


def _cmd_scenes(args: argparse.Namespace) -> int:
    manifest = write_stimuli(Path(args.out), weathering=args.weathering, style=args.style)
    print(f"wrote {len(manifest['scenes'])} scenes to {args.out}")
    return 0


def _cmd_defend(args: argparse.Namespace) -> int:
    image = Image.open(args.image)
    cleaned, report = isolate_instructions(image)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    cleaned.save(args.out)
    sidecar = Path(args.out).with_suffix(".json")
    sidecar.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"image": args.out, "masked_text": report["masked_text"]}, ensure_ascii=False))
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    from hornok.report import build_report

    records = []
    for line in Path(args.predictions).read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    report = build_report(records)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hornok", description="Horn OK Please audit kit")
    parser.add_argument("--version", action="version", version=f"hornok {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("gen", help="paint text onto an image")
    gen.add_argument("--base", required=True)
    gen.add_argument("--text", required=True)
    gen.add_argument("--quad", required=True, type=_parse_quad)
    gen.add_argument("--out", required=True)
    gen.add_argument("--style", default="painted", choices=["painted", "stencil"])
    gen.add_argument("--weathering", type=float, default=0.28)
    gen.add_argument("--seed", type=int, default=0)
    gen.add_argument("--ink", default="32,18,14")
    gen.add_argument("--absorb", type=float, default=0.1)
    gen.set_defaults(func=_cmd_gen)

    parse = sub.add_parser("parse", help="parse a model completion")
    parse.add_argument("--text", default=None)
    parse.set_defaults(func=_cmd_parse)

    scenes = sub.add_parser("make-scenes", help="write the synthetic benchmark stimuli")
    scenes.add_argument("--out", default="eval/stimuli")
    scenes.add_argument("--weathering", type=float, default=0.28)
    scenes.add_argument("--style", default="painted", choices=["painted", "stencil"])
    scenes.set_defaults(func=_cmd_scenes)

    defend = sub.add_parser("defend", help="OCR instruction isolation")
    defend.add_argument("--image", required=True)
    defend.add_argument("--out", required=True)
    defend.set_defaults(func=_cmd_defend)

    report = sub.add_parser("report", help="compute the pre-registered metrics")
    report.add_argument("--predictions", required=True)
    report.add_argument("--out", default=None)
    report.set_defaults(func=_cmd_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
