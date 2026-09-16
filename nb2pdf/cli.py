import click
from pathlib import Path
from .converter import convert


@click.command()
@click.argument("notebook_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o", "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output PDF path. Defaults to same name as input with .pdf extension."
)
def main(notebook_path: Path, output: Path):
    """
    Convert a Jupyter Notebook (.ipynb) to Neobrutalism styled PDF with clickable ArdhanFah footer.
    """
    try:
        click.echo(f"⚡ Converting {notebook_path} to Neobrutalism PDF...")
        out_file = convert(str(notebook_path), str(output) if output else None)
        click.secho(f"✨ Successfully generated PDF: {out_file}", fg="green", bold=True)
    except Exception as e:
        click.secho(f"❌ Error: {str(e)}", fg="red", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
