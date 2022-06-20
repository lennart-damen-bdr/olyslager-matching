import logging
import click
from oly_matching.main import main
from oly_matching.pretty_logging import configure_logger


@click.group()
@click.version_option()
def cli() -> None:
    """Command line interface for the recommender model."""


@cli.command()
@click.option("--lis-path", default="./data/raw/lis.xlsx")
@click.option("--tecdoc-path", default="./data/raw/tecdoc.xlsx")
@click.option("--output-folder", default="./data/output")
def match(lis_path: str, tecdoc_path: str, output_folder: str) -> None:
    """Entrypoint for the matching process"""
    configure_logger(logging.INFO)
    main(lis_path, tecdoc_path, output_folder)


if __name__ == "__main__":
    cli()
