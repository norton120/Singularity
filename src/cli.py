import time
import click

from .slacker import Slacker

@click.command()
@click.option("--wait", default=0, help="Wait for this many seconds before updating.")
def update_slack_status(wait: int):
    if wait:
        click.echo(f"Waiting {wait} seconds before updating...")
        time.sleep(wait)
        click.echo("Done waiting.")
    click.echo("Updating slack status based on current taskwarrior tasks...")
    client = Slacker()
    client.update_statuses_based_on_current_state()
    click.echo("Updated.")

if __name__ == "__main__":
    update_slack_status()
