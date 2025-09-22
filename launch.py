#!/usr/bin/env python3
"""
Unified Launcher for Gooby Discord Bot and MCP Servers

This script launches both the Discord bot and any configured MCP servers,
providing unified logging and graceful shutdown handling.
"""

import asyncio
import signal
import subprocess
import sys
import os
import json
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("gooby_launcher")

class GoobyLauncher:
    """Unified launcher for Gooby bot and MCP servers."""

    def __init__(self):
        self.bot_process: Optional[subprocess.Popen] = None
        self.mcp_processes: Dict[str, subprocess.Popen] = {}
        self.shutdown_event = asyncio.Event()
        self.base_dir = Path(__file__).parent

    async def setup_mcp_config(self):
        """Set up LM Studio MCP configuration."""
        try:
            # Get the user's LM Studio config directory
            home = Path.home()

            if sys.platform == "win32":
                lmstudio_dir = home / ".lmstudio"
            else:
                lmstudio_dir = home / ".lmstudio"

            mcp_config_path = lmstudio_dir / "mcp.json"

            # Ensure directory exists
            lmstudio_dir.mkdir(exist_ok=True)

            # Path to our MCP server
            mcp_server_path = self.base_dir / "mcp_servers" / "discord_reactions" / "server.py"

            # MCP configuration for LM Studio
            mcp_config = {
                "discord-reactions": {
                    "command": "python",
                    "args": [str(mcp_server_path)],
                    "env": {
                        "PYTHONPATH": str(self.base_dir)
                    }
                }
            }

            # Read existing config if it exists
            existing_config = {}
            if mcp_config_path.exists():
                try:
                    with open(mcp_config_path, 'r') as f:
                        existing_config = json.load(f)
                except json.JSONDecodeError:
                    logger.warning("Existing mcp.json is invalid, will overwrite")

            # Merge configurations
            existing_config.update(mcp_config)

            # Write updated config
            with open(mcp_config_path, 'w') as f:
                json.dump(existing_config, f, indent=2)

            logger.info(f"Updated LM Studio MCP configuration at {mcp_config_path}")

        except Exception as e:
            logger.error(f"Failed to setup MCP configuration: {e}")
            raise

    async def start_mcp_server(self, name: str, script_path: Path) -> subprocess.Popen:
        """Start an MCP server process."""
        try:
            logger.info(f"Starting MCP server: {name}")

            # Start the MCP server
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=self.base_dir,
                env={**os.environ, "PYTHONPATH": str(self.base_dir)},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.mcp_processes[name] = process
            logger.info(f"MCP server {name} started with PID {process.pid}")

            # Start output monitoring
            asyncio.create_task(self._monitor_process_output(name, process))

            return process

        except Exception as e:
            logger.error(f"Failed to start MCP server {name}: {e}")
            raise

    async def start_discord_bot(self) -> subprocess.Popen:
        """Start the Discord bot process."""
        try:
            logger.info("Starting Discord bot")

            # Start the bot
            self.bot_process = subprocess.Popen(
                [sys.executable, "bot.py"],
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            logger.info(f"Discord bot started with PID {self.bot_process.pid}")

            # Start output monitoring
            asyncio.create_task(self._monitor_process_output("bot", self.bot_process))

            return self.bot_process

        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
            raise

    async def _monitor_process_output(self, name: str, process: subprocess.Popen):
        """Monitor and log output from a subprocess."""
        try:
            while True:
                # Check if process is still running
                if process.poll() is not None:
                    break

                # Read stderr (where most logging goes)
                if process.stderr and process.stderr.readable():
                    line = await asyncio.get_event_loop().run_in_executor(
                        None, process.stderr.readline
                    )
                    if line:
                        logger.info(f"[{name}] {line.strip()}")

                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error monitoring {name} output: {e}")

    async def check_dependencies(self):
        """Check if required dependencies are installed."""
        try:
            # Check if FastMCP is available for MCP server
            result = subprocess.run(
                [sys.executable, "-c", "import fastmcp"],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error("FastMCP not installed. Installing dependencies...")

                # Install MCP server dependencies
                mcp_requirements = self.base_dir / "mcp_servers" / "discord_reactions" / "requirements.txt"
                if mcp_requirements.exists():
                    subprocess.run([
                        sys.executable, "-m", "pip", "install", "-r", str(mcp_requirements)
                    ], check=True)
                    logger.info("MCP dependencies installed successfully")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            raise
        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
            raise

    async def shutdown(self):
        """Gracefully shutdown all processes."""
        logger.info("Initiating graceful shutdown...")

        # Stop Discord bot
        if self.bot_process:
            try:
                logger.info("Stopping Discord bot...")
                self.bot_process.terminate()

                # Wait for graceful shutdown
                try:
                    await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, self.bot_process.wait
                        ),
                        timeout=10.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("Bot didn't shutdown gracefully, killing...")
                    self.bot_process.kill()

                logger.info("Discord bot stopped")
            except Exception as e:
                logger.error(f"Error stopping Discord bot: {e}")

        # Stop MCP servers
        for name, process in self.mcp_processes.items():
            try:
                logger.info(f"Stopping MCP server: {name}")
                process.terminate()

                try:
                    await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, process.wait
                        ),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"MCP server {name} didn't shutdown gracefully, killing...")
                    process.kill()

                logger.info(f"MCP server {name} stopped")
            except Exception as e:
                logger.error(f"Error stopping MCP server {name}: {e}")

        logger.info("Shutdown complete")

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
            self.shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def run(self):
        """Main launcher loop."""
        try:
            logger.info("=== Gooby Bot Launcher Starting ===")

            # Setup signal handlers
            self.setup_signal_handlers()

            # Check dependencies
            await self.check_dependencies()

            # Setup MCP configuration
            await self.setup_mcp_config()

            # Start MCP servers
            mcp_server_path = self.base_dir / "mcp_servers" / "discord_reactions" / "server.py"
            if mcp_server_path.exists():
                await self.start_mcp_server("discord-reactions", mcp_server_path)
            else:
                logger.warning(f"MCP server not found at {mcp_server_path}")

            # Wait a moment for MCP servers to start
            await asyncio.sleep(2)

            # Start Discord bot
            await self.start_discord_bot()

            logger.info("=== All services started successfully ===")
            logger.info("Press Ctrl+C to stop all services")

            # Wait for shutdown signal
            await self.shutdown_event.wait()

        except KeyboardInterrupt:
            logger.info("Launcher interrupted by user")
        except Exception as e:
            logger.error(f"Launcher error: {e}")
            raise
        finally:
            await self.shutdown()

async def main():
    """Main entry point."""
    launcher = GoobyLauncher()
    await launcher.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nLauncher stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)