import asyncclick as click
from ..config import DEFAULT_CONFIG_PATH
from .config import check_config
from .run import run


@click.group
@click.option("-c", "--config-path", type=click.Path(exists=True), default=DEFAULT_CONFIG_PATH)
@click.option("--load-env/--no-load-env", type=bool, default=True)
@click.pass_context
def cli(ctx, config_path, load_env):
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)

    ctx.obj['config_path'] = config_path
    ctx.obj['load_env'] = load_env

for command in [check_config, run]:
    cli.add_command(command)
