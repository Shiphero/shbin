"""
Handles GitHub Device Flow authentication and storing the token + repo in a config file.
"""

import json
import sys
import time
import webbrowser
import requests

import pyclip
from platformdirs import user_config_path
from rich import print
from rich.prompt import Prompt

GITHUB_CLIENT_ID = "Ov23liYdj3oj4CUOqEds"
GITHUB_SCOPES = ["read:user", "repo"]

# Where we store local config
CONFIG_PATH = user_config_path("shbin", ensure_exists=True) / "config.json"


# -------------------------------------------------------------------
# Helper: load/save config
# -------------------------------------------------------------------
def load_config():
    """
    Loads our JSON config from CONFIG_PATH, returns dict or {} if none.
    """
    if CONFIG_PATH.is_file():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return {}


def save_config(cfg):
    """
    Saves the dict `cfg` to CONFIG_PATH as JSON. Creates parent dirs if needed.
    """
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


# -------------------------------------------------------------------
# The minimal device-flow
# -------------------------------------------------------------------
def device_flow_auth(client_id, scopes):
    """
    Performs a minimal device-flow to get an OAuth token from GitHub.
    Returns the token, or None if it fails/times out.
    """
    # 1) Request the device code
    auth_url = "https://github.com/login/device/code"
    data = {
        "client_id": client_id,
        "scope": " ".join(scopes),
    }
    headers = {"Accept": "application/json"}
    r = requests.post(auth_url, data=data, headers=headers)
    r.raise_for_status()
    resp = r.json()

    device_code = resp["device_code"]
    user_code = resp["user_code"]
    verification_uri = resp["verification_uri"]
    interval = resp["interval"]
    expires_in = resp["expires_in"]
    try:
        pyclip.copy(user_code)
        copied = " (already copied 📋!) "
    except pyclip.ClipboardSetupException:
        copied = " "

    print(f"You will be redirected to Github now.\nWhen asked, paste the{copied}code:\n [yellow]{user_code}[/yellow]")

    time.sleep(2)
    webbrowser.open(verification_uri)

    # 2) Poll until success or timeout
    token_url = "https://github.com/login/oauth/access_token"
    start = time.time()
    while True:
        time.sleep(interval)
        elapsed = time.time() - start
        if elapsed > expires_in:
            print("[red]Timed out waiting for authorization.[/red]")
            return None

        poll_resp = requests.post(
            token_url,
            data={
                "client_id": client_id,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            headers={"Accept": "application/json"},
        )
        poll_resp.raise_for_status()
        js = poll_resp.json()

        if "error" in js:
            err = js["error"]
            if err == "authorization_pending":
                continue  # user hasn't clicked "Authorize" yet
            elif err == "slow_down":
                interval += 2
            else:
                print(f"[red]Authorization failed: {err}[/red]")
                return None
        else:
            print("[green]✓[/green] Got access token.")
            return js["access_token"]


def do_auth():
    token = device_flow_auth(GITHUB_CLIENT_ID, GITHUB_SCOPES)
    if not token:
        sys.exit("[red]x[/red]No token acquired. Exiting.")

    # Prompt for the repo
    new_repo = Prompt.ask("Which repo do you want to use as your 'pastebin'? (ex: myorg/pastebin)")

    # Save to config
    config = load_config()
    config["token"] = token
    config["repo"] = new_repo
    save_config(config)
    print("[green]✓[/green] All done!")
