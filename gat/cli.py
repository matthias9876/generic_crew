import sys
import argparse
from gat import config_loader
from gat.phases import requirements_phase, hiring_phase, execution_phase


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="python -m gat",
        description="GAT: Generic Agentic Team CLI"
    )
    parser.add_argument(
        "--config", default="gat/gat.yaml",
        help="Path to the unified gat.yaml configuration file"
    )
    parser.add_argument(
        "--preset", default=None,
        help="Model preset: 'gpu' (fast) or 'mixed' (quality)"
    )
    subparsers = parser.add_subparsers(dest="phase", required=True)

    # requirements subcommand
    req_parser = subparsers.add_parser(
        "requirements", help="Run requirements review phase"
    )
    req_parser.add_argument(
        "--rd", required=True, help="Path to the requirements document"
    )
    req_parser.add_argument(
        "--output", default="review.md",
        help="Path for the output review document"
    )
    req_parser.add_argument(
        "--logs", default="logs/",
        help="Root directory for agent work logs"
    )

    # hire subcommand
    hire_parser = subparsers.add_parser(
        "hire", help="Run crew hiring phase"
    )
    hire_parser.add_argument(
        "--rd", required=True, help="Path to the requirements document"
    )
    hire_parser.add_argument(
        "--output", default="crew.yaml",
        help="Path for the generated crew YAML"
    )
    hire_parser.add_argument(
        "--logs", default="logs/",
        help="Root directory for agent work logs"
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
    run_parser.add_argument(
        "--logs", default="logs/",
        help="Root directory for agent work logs"
    )

    try:
        args = parser.parse_args(argv)

        # Load unified config
        cfg = config_loader.load_config(args.config)
        preset_data = config_loader.resolve_preset(cfg, preset=args.preset)

        if args.phase == "requirements":
            result = requirements_phase.run(
                rd_path=args.rd,
                models=preset_data,
                log_dir=args.logs,
                output_path=args.output,
                pipeline_cfg=cfg,
            )
        elif args.phase == "hire":
            result = hiring_phase.run(
                rd_path=args.rd,
                models=preset_data,
                log_dir=args.logs,
                output_yaml_path=args.output,
            )
        elif args.phase == "run":
            result = execution_phase.run(
                rd_path=args.rd,
                crew_yaml_path=args.crew,
                models=preset_data,
                log_dir=args.logs,
                pipeline_cfg=cfg,
            )
        else:
            parser.print_usage()
            sys.exit(2)
        print(result)
    except (FileNotFoundError, ValueError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
