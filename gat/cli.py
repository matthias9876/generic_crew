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
    subparsers = parser.add_subparsers(dest="phase", required=True)

    # requirements subcommand
    req_parser = subparsers.add_parser("requirements", help="Run requirements review phase")
    req_parser.add_argument("--rd", required=True, help="Path to the requirements document")
    req_parser.add_argument("--output", default="review.md", help="Path for the output review document")
    req_parser.add_argument("--models", default="gat/models.yaml", help="Path to models YAML")
    req_parser.add_argument("--preset", default=None, help="Model preset: 'gpu' (fast, 12GB VRAM) or 'precise' (slow, 64GB RAM)")
    req_parser.add_argument("--logs", default="logs/", help="Root directory for agent work logs")

    # hire subcommand
    hire_parser = subparsers.add_parser("hire", help="Run crew hiring phase")
    hire_parser.add_argument("--rd", required=True, help="Path to the requirements document")
    hire_parser.add_argument("--output", default="crew.yaml", help="Path for the generated crew YAML")
    hire_parser.add_argument("--models", default="gat/models.yaml", help="Path to models YAML")
    hire_parser.add_argument("--preset", default=None, help="Model preset: 'gpu' (fast, 12GB VRAM) or 'precise' (slow, 64GB RAM)")
    hire_parser.add_argument("--logs", default="logs/", help="Root directory for agent work logs")

    # run subcommand
    run_parser = subparsers.add_parser("run", help="Run execution phase")
    run_parser.add_argument("--rd", required=True, help="Path to the requirements document")
    run_parser.add_argument("--crew", required=True, help="Path to the crew YAML from the hire phase")
    run_parser.add_argument("--models", default="gat/models.yaml", help="Path to models YAML")
    run_parser.add_argument("--preset", default=None, help="Model preset: 'gpu' (fast, 12GB VRAM) or 'precise' (slow, 64GB RAM)")
    run_parser.add_argument("--logs", default="logs/", help="Root directory for agent work logs")

    try:
        args = parser.parse_args(argv)
        models = config_loader.load_models(args.models, preset=args.preset)
        if args.phase == "requirements":
            result = requirements_phase.run(
                rd_path=args.rd,
                models=models,
                log_dir=args.logs,
                output_path=args.output
            )
        elif args.phase == "hire":
            result = hiring_phase.run(
                rd_path=args.rd,
                models=models,
                log_dir=args.logs,
                output_yaml_path=args.output
            )
        elif args.phase == "run":
            result = execution_phase.run(
                rd_path=args.rd,
                crew_yaml_path=args.crew,
                models=models,
                log_dir=args.logs
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
