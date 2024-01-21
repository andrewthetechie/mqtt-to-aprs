import asyncclick as click
from ..config import aget_config
from pydantic import ValidationError
import sys


@click.command
@click.pass_context
async def check_config(ctx, echo: bool = True):
    """Validate the mqtt2aprs config"""
    await _check_config(ctx, echo)


async def _check_config(ctx, echo: bool = True):
    """Load and validate the mqtt2aprs config from a toml file and the environemnt

    Broken into a separate method from the click command so that other commands can call this first
    and not have to reimplement the validation
    """
    config_path = ctx.obj['config_path']
    load_env = ctx.obj['load_env']
    if echo:
        click.echo(f"Checking config at {config_path}.")
        if load_env:
            click.echo("Will load environment variables")
    try:
        ctx.obj['config'] = await aget_config(config_path=config_path, from_env=load_env)
    except ValidationError as exc:
        click.echo("Config failed to validate")
        click.echo(exc)
        sys.exit(1)
    if echo:
        click.echo("Config validated")
