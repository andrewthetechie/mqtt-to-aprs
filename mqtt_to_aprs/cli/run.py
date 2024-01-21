import asyncclick as click

from .config import _check_config


@click.command
@click.pass_context
async def run(ctx):
    await _check_config(ctx, echo=False)
    print(ctx.obj['config'])
