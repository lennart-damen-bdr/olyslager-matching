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
@click.option("--matching-method", default="exact", help="Choose from: exact, cut_strings, fuzzy")
def match(lis_path: str, tecdoc_path: str, output_folder: str, matching_method: str) -> None:
    """Entrypoint for the matching process

    Creates 4 files:
    - matches_per_lis_id.xlsx: for each LIS type ID, state which N-types correspond to it (together with extra info)
    - links_with_original_data.xlsx: for every link between LIS and TecDoc, state what was the
                                     original information in LIS and TecDoc (used to validate matches by hand)
    - metrics: overall overview of matching performance
    - results_per_model.xlsx: overview of performance per model (useful for identifying algorithm improvements)
    """
    configure_logger(logging.INFO)
    main(lis_path, tecdoc_path, output_folder, matching_method)


if __name__ == "__main__":
    cli()
