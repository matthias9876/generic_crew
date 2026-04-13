import os
import sys
import shutil
import argparse
from datetime import datetime
from gat import config_loader
from gat.phases import requirements_phase, hiring_phase, execution_phase


def _make_run_dir(base: str = "runs") -> str:
    """Return a timestamped run directory path and create it."""
    stamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    run_dir = os.path.join(base, stamp)
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="python -m gat",
        description="GAT: Generic Agentic Team CLI"
    )
    parser.add_argument(
        "--config", nargs="+", default=["gat/gat.yaml"],
        help="One or more config YAML files (later files override earlier ones)"
    )
    parser.add_argument(
        "--preset", default=None,
        help="Model preset: 'gpu' (fast) or 'mixed' (quality)"
    )
    parser.add_argument(
        "--run-dir", default=None, dest="run_dir",
        help="Output directory for this run (default: runs/YYYY-MM-DDTHH-MM-SS/)"
    )
    subparsers = parser.add_subparsers(dest="phase", required=True)

    # requirements subcommand
    req_parser = subparsers.add_parser(
        "requirements", help="Run requirements review phase"
    )
    req_parser.add_argument(
        "--rd", required=True, help="Path to the requirements document"
    )

    # hire subcommand
    hire_parser = subparsers.add_parser(
        "hire", help="Run crew hiring phase"
    )
    hire_parser.add_argument(
        "--rd", required=True, help="Path to the requirements document"
    )

    # run subcommand
    run_parser = subparsers.add_parser(
        "run", help="Run execution phase"
    )
    run_parser.add_argument(
        "--rd", required=True, help="Path to the requirements document"
    )
    run_parser.add_argument(
        "--crew", required=True,
        help="Path to the crew YAML from the hire phase"
    )

    # full subcommand — chains all three phases
    full_parser = subparsers.add_parser(
        "full", help="Run all three phases: requirements → hire → execute"
    )
    full_parser.add_argument(
        "--rd", required=True, help="Path to the requirements document"
    )

    try:
        args = parser.parse_args(argv)

        cfg = config_loader.load_config(args.config)
        config_loader.patch_ssl_for_unverified_instances(cfg)
        preset_data = config_loader.resolve_preset(cfg, preset=args.preset)

        run_dir = args.run_dir or _make_run_dir()

        if args.phase == "requirements":
            result = requirements_phase.run(
                rd_path=args.rd,
                models=preset_data,
                run_dir=run_dir,
                pipeline_cfg=cfg,
            )
        elif args.phase == "hire":
            result = hiring_phase.run(
                rd_path=args.rd,
                models=preset_data,
                run_dir=run_dir,
                pipeline_cfg=cfg,
            )
        elif args.phase == "run":
            result = execution_phase.run(
                rd_path=args.rd,
                crew_yaml_path=args.crew,
                models=preset_data,
                run_dir=run_dir,
                pipeline_cfg=cfg,
            )
        elif args.phase == "full":
            result = _run_full(args.rd, preset_data, run_dir, cfg)
        else:
            parser.print_usage()
            sys.exit(2)
        print(result)
    except (FileNotFoundError, ValueError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


def _run_full(rd_path: str, preset_data: dict, run_dir: str, cfg: dict) -> str:
    """Chain requirements → hire → execute, all writing into run_dir."""
    print(f"[gat full] Run directory: {run_dir}", flush=True)

    # Phase 1: requirements
    print("[gat full] Phase 1/3: requirements review", flush=True)
    reviewed_path = requirements_phase.run(
        rd_path=rd_path,
        models=preset_data,
        run_dir=run_dir,
        pipeline_cfg=cfg,
    )
    print(f"[gat full]   → {reviewed_path}", flush=True)

    # Phase 2: hire (uses the reviewed requirements as input)
    print("[gat full] Phase 2/3: crew hiring", flush=True)
    crew_path = hiring_phase.run(
        rd_path=reviewed_path,
        models=preset_data,
        run_dir=run_dir,
        pipeline_cfg=cfg,
    )
    print(f"[gat full]   → {crew_path}", flush=True)

    # Phase 3: execute
    print("[gat full] Phase 3/3: execution", flush=True)
    summary = execution_phase.run(
        rd_path=reviewed_path,
        crew_yaml_path=crew_path,
        models=preset_data,
        run_dir=run_dir,
        pipeline_cfg=cfg,
    )

    return f"Run complete. Output in: {run_dir}\n\n{summary}"


if __name__ == "__main__":
    main()
