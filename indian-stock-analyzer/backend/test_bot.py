from __future__ import annotations

from bot_commands import handle_command


def run_local_tests() -> None:
    test_commands = [
        "HELP",
        "NIFTY",
        "BANKNIFTY",
        "TOP5",
        "WORST5",
        "SIGNAL RELIANCE",
        "NEWS NIFTY",
        "ALERT ON",
        "MARKET",
    ]
    print("=== Direct command parser tests ===")
    for cmd in test_commands:
        print(f"\n> {cmd}")
        print(handle_command(cmd)[:600])


if __name__ == "__main__":
    run_local_tests()
