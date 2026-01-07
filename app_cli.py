import asyncio
import subprocess
from pathlib import Path

import click

# TODO: Import your app-specific seeding functions here
# Example:
# from core.example_entity import seed_example_entity
# from generate.example_generate import generate_example_data

from utils.database import close_connection_pool, get_connection_pool
from common.logger import logger


@click.group()
def app_cli():
    """CLI for seeding data into your application."""
    pass


@app_cli.command()
@click.option("-d", "--detach", is_flag=True, help="Run in detached mode")
def up(detach: bool):
    """Start the application containers."""
    docker_dir = Path(__file__).parent.joinpath("docker")
    cmd = ["docker", "compose", "up", "--build"]
    if detach:
        cmd.append("-d")
    subprocess.run(cmd, cwd=docker_dir)

    logger.succeed("Containers started successfully")
    logger.info("Read the instructions in README.md for setup guide")


@app_cli.command()
def down():
    """Stop the application containers and remove volumes."""
    docker_dir = Path(__file__).parent.joinpath("docker")
    cmd = ["docker", "compose", "down", "--remove-orphans", "--volumes"]
    subprocess.run(cmd, cwd=docker_dir)
    logger.succeed("Containers stopped and volumes removed")


@app_cli.command()
def seed():
    """Seed data into the application."""
    async def async_seed():
        await get_connection_pool()
        try:
            # TODO: Add your seeding functions here
            # Example:
            # await seed_example_entity()
            pass
        finally:
            await close_connection_pool()

    asyncio.run(async_seed())


@app_cli.command()
def generate():
    """Generate seed data files."""
    async def async_generate():
        # TODO: Add your generation functions here
        # Example:
        # await generate_example_data()
        pass

    asyncio.run(async_generate())


if __name__ == "__main__":
    app_cli()
