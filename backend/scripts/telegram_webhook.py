#!/usr/bin/env python3
"""
CLI utility for safely inspecting, registering, and removing the Telegram Bot Webhook
for the connectED backend.

Security Guarantees:
- Never prints or logs TELEGRAM_BOT_TOKEN or TELEGRAM_WEBHOOK_SECRET.
- Never prints the raw URL containing the bot token.
- Redacts sensitive query parameters, tokens, and credentials in displayed output and errors.
- Protects against accidental deletion and silent destination overwrites.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Optional, Tuple
from dotenv import dotenv_values

def load_credentials() -> Tuple[Optional[str], Optional[str], str]:
    env_vals = dotenv_values(".env") if os.path.exists(".env") else {}
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or env_vals.get("TELEGRAM_BOT_TOKEN")
    secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET") or env_vals.get("TELEGRAM_WEBHOOK_SECRET")
    username = os.environ.get("TELEGRAM_BOT_USERNAME") or env_vals.get("TELEGRAM_BOT_USERNAME") or "ZeplyAIBot"
    return token, secret, username

def sanitize_text(text: str, token: Optional[str] = None, secret: Optional[str] = None) -> str:
    if not text:
        return ""
    cleaned = str(text)
    if token:
        cleaned = cleaned.replace(token, "[REDACTED_BOT_TOKEN]")
    if secret:
        cleaned = cleaned.replace(secret, "[REDACTED_SECRET]")
    # Redact Telegram bot token in path pattern: /bot<token>/
    cleaned = re.sub(r"bot[0-9]+:[a-zA-Z0-9_-]+", "bot[REDACTED_TOKEN]", cleaned)
    # Redact query parameters
    cleaned = re.sub(r"(secret_token=|token=)[^&\s]+", r"\1[REDACTED]", cleaned)
    return cleaned

def sanitize_url(url: str, token: Optional[str] = None, secret: Optional[str] = None) -> str:
    if not url:
        return "<None (No webhook registered)>"
    return sanitize_text(url, token=token, secret=secret)

def _call_telegram_api(endpoint: str, token: str, payload: Optional[dict] = None) -> dict:
    url = f"https://api.telegram.org/bot{token}/{endpoint}"
    data = None
    headers = {"User-Agent": "connectED-Webhook-Manager/1.0"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            raw_body = e.read().decode("utf-8", errors="replace")
            parsed = json.loads(raw_body)
            error_body = parsed.get("description", raw_body)
        except Exception:
            error_body = str(e.reason)
        safe_msg = sanitize_text(f"Telegram API HTTP Error {e.code}: {error_body}", token=token)
        raise RuntimeError(safe_msg) from None
    except urllib.error.URLError as e:
        safe_msg = sanitize_text(f"Network error communicating with Telegram: {e.reason}", token=token)
        raise RuntimeError(safe_msg) from None
    except Exception as e:
        safe_msg = sanitize_text(f"Unexpected error communicating with Telegram: {e}", token=token)
        raise RuntimeError(safe_msg) from None

def get_webhook_info(token: str) -> dict:
    return _call_telegram_api("getWebhookInfo", token)

def set_webhook(token: str, webhook_url: str, secret_token: Optional[str] = None) -> dict:
    payload = {
        "url": webhook_url,
        "allowed_updates": ["message", "callback_query"],
    }
    if secret_token:
        payload["secret_token"] = secret_token
    return _call_telegram_api("setWebhook", token, payload=payload)

def delete_webhook(token: str) -> dict:
    return _call_telegram_api("deleteWebhook", token)

def main():
    parser = argparse.ArgumentParser(description="connectED Telegram Webhook Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: info
    subparsers.add_parser("info", help="Get current webhook status from Telegram")

    # Subcommand: set
    set_parser = subparsers.add_parser("set", help="Register a new webhook URL")
    set_parser.add_argument(
        "--url",
        required=True,
        help="Public base URL (e.g. https://xxx.ngrok-free.app) or full endpoint path",
    )
    set_parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite if an existing webhook is already registered to a different destination",
    )

    # Subcommand: delete
    del_parser = subparsers.add_parser("delete", help="Remove the active webhook from Telegram")
    del_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Confirm deletion without interactive confirmation prompt",
    )

    args = parser.parse_args()
    token, secret, username = load_credentials()

    if not token or not token.strip() or token.startswith("your_"):
        print("[!] ERROR: TELEGRAM_BOT_TOKEN is not configured in .env or shell environment.")
        print("    Please set TELEGRAM_BOT_TOKEN=<token_from_botfather> in .env to use this utility.")
        sys.exit(1)

    try:
        if args.command == "info":
            res = get_webhook_info(token).get("result", {})
            registered_url = res.get("url", "")
            is_reg = bool(registered_url)
            matches = registered_url.endswith("/api/v1/webhooks/telegram") if is_reg else False

            print("\n================ Telegram Webhook Status ================")
            print(f"Bot Username:              @{username}")
            print(f"Webhook Registered:        {is_reg}")
            print(f"Registered URL:            {sanitize_url(registered_url, token, secret)}")
            print(f"Matches /api/v1/webhooks:  {matches}")
            print(f"Pending Updates Count:     {res.get('pending_update_count', 0)}")
            print(f"Has Custom Certificate:    {res.get('has_custom_certificate', False)}")
            print(f"Last Error Date:           {res.get('last_error_date', 'None')}")
            print(f"Last Error Message:        {sanitize_text(res.get('last_error_message', 'None'), token, secret)}")
            if "ip_address" in res:
                print(f"Server IP Address:         {res.get('ip_address')}")
            if "allowed_updates" in res:
                print(f"Allowed Updates:           {res.get('allowed_updates')}")
            print("=========================================================\n")

        elif args.command == "set":
            target_url = args.url.strip()
            if not target_url.startswith("https://"):
                print("[!] ERROR: Telegram webhooks require a public HTTPS URL (e.g. https://xxx.ngrok-free.app).")
                sys.exit(1)

            if not target_url.endswith("/api/v1/webhooks/telegram"):
                target_url = target_url.rstrip("/") + "/api/v1/webhooks/telegram"

            # Check existing webhook first to avoid silent overwriting
            info = get_webhook_info(token).get("result", {})
            current_url = info.get("url", "")
            if current_url and current_url != target_url and not args.force:
                print("\n[!] CONFLICT DETECTED:")
                print(f"    The bot is currently pointing to another destination:")
                print(f"    {sanitize_url(current_url, token, secret)}")
                print("    To overwrite this registration, re-run with the --force flag.\n")
                sys.exit(1)

            if not secret or not secret.strip() or secret.startswith("your_"):
                print("[!] WARNING: TELEGRAM_WEBHOOK_SECRET is not configured in .env.")
                print("    Telegram webhook requests will NOT include X-Telegram-Bot-Api-Secret-Token.")

            resp = set_webhook(token, target_url, secret_token=secret)
            if resp.get("ok"):
                print("\n[+] SUCCESS: Telegram webhook registered successfully!")
                print(f"    Target URL:            {sanitize_url(target_url, token, secret)}")
                print(f"    Secret Token Enforced: {'Yes' if (secret and not secret.startswith('your_')) else 'No'}")
                print("    Allowed Updates:       ['message', 'callback_query']")
                print("    NOTE: Registration with Telegram succeeded. Live delivery requires a running backend,")
                print(f"          active HTTPS tunnel, and a real update (e.g. sending /start to @{username}).\n")
            else:
                desc = sanitize_text(resp.get("description", "Unknown error"), token, secret)
                print(f"[!] FAILED: Telegram responded: {desc}")
                sys.exit(1)

        elif args.command == "delete":
            if not args.yes:
                # Prompt user if running in interactive shell, or require --yes
                if sys.stdin.isatty():
                    confirm = input("Are you sure you want to delete the active Telegram webhook? [y/N]: ").strip().lower()
                    if confirm not in ("y", "yes"):
                        print("Operation aborted. Webhook was not deleted.")
                        sys.exit(0)
                else:
                    print("[!] ERROR: Deleting the webhook requires the --yes flag in non-interactive mode.")
                    sys.exit(1)

            resp = delete_webhook(token)
            if resp.get("ok"):
                print("\n[+] SUCCESS: Telegram webhook successfully removed.")
            else:
                desc = sanitize_text(resp.get("description", "Unknown error"), token, secret)
                print(f"[!] FAILED: Telegram responded: {desc}")
                sys.exit(1)

    except RuntimeError as e:
        print(f"[!] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
