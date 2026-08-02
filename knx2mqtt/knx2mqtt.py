#!python3

import argparse
import asyncio

from knx2mqtt import config, daemon


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="A KNX to MQTT bridge with bidirectional telegram transfer")
    parser.add_argument("-c", "--config", type=str, help="Path to a knx2mqtt configuration file")
    parser.add_argument("-l", "--logconfig", type=str, help="Path to a logging configuration file")
    args = parser.parse_args()

    # Convert args to user config
    user_cfg = {}
    if args.logconfig:
        user_cfg.update({"file": args.logconfig})

    user_read_cfg = {}
    if args.config:
        user_read_cfg.update({"file": args.config})

    # Read user configuration
    cfg = config.ConfigManager(**user_cfg)
    cfg.read(**user_read_cfg)

    # Start app
    d = daemon.Daemon(cfg)
    await d.run()

if __name__ == "__main__":
    asyncio.run(main())
