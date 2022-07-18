#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload a file to your own folder on the pastebin repo.

# Install

- Save this file somewhere in your PATH as "shbin", and add execution permissions. 

  `$ chmod -x /path/to/shbin`

- Create a personal token from https://github.com/settings/tokens

  Follow these instructions for details https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
  Make sure of:
    
    - Enable Repo and User scopes
    - Enable SSO

- Set the environment variable:

    export SHBIN_GITHUB_TOKEN = "<your personal token>"

- Install pygithub

  ```
  $pip --user install pygithub
  ```

- [optionally] Install xclip. For example in Ubuntu/Debian
  
  ```
  $ sudo apt install xclip
  ```

# Usage

```
$ shbin <file>
$ shbin  # upload content from the clipboard, discovering its format. e.g. an screenshot

$ shbin <file> -u -m "your message"   # update a file and add a commit message
$ shbin <file1> <file2> [...]         # upload several files  
$ shbin -h   # show full options
```
"""

import argparse
import os
import pathlib
import secrets
import subprocess
import sys

from github import Github, GithubException

VERSION = "0.1.0"


def valid_path(path_str):
    path = pathlib.Path(path_str)
    if not path.exists() or not path.is_file():
        raise argparse.ArgumentTypeError(f"{path_str} is not a valid file")
    return path


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="upload a file to your folder on pastebin repo",
    )
    parser.add_argument("files", nargs="*", type=valid_path)
    parser.add_argument("-m", "--message", help="Message for the commit", default="")
    parser.add_argument("-f", "--suffix", help="Extension for plain text", default="md")
    parser.add_argument("-u", "--update", default="Update file if it exists")
    parser.add_argument(
        "--repo",
        default=os.environ.get("SHBIN_REPO", "shiphero/pastebin"),
        help="REPO to commit",
    )
    parser.add_argument(
        "--gh-token",
        default=os.environ.get("SHBIN_GITHUB_TOKEN"),
        help="Github Personal access token",
    )
    return parser


def main() -> None:

    parser = init_argparse()
    args = parser.parse_args()
    gh = Github(args.gh_token)

    repo = gh.get_repo(args.repo)
    user = gh.get_user().login

    if not args.files:
        # if no files were given, try to read from clipboard using xclip
        base_command = ["xclip", "-o", "-selection", "clipboard", "-t"]

        targets = subprocess.check_output(base_command + ["TARGETS"], text=True).splitlines()
        mime_type = "text/plain" if "text/plain" in targets else targets[0]

        content = subprocess.check_output(base_command + [mime_type])

        suffix = args.suffix if mime_type == "text/plain" else mime_type.split("/")[-1]
        # TODO detect language via pygments

        path_name = f"{secrets.token_urlsafe(8)}.{suffix}"
        result = repo.create_file(f"{user}/{path_name}", args.message, content)
        print(result["content"].html_url)
        return

    for path in args.files:
        file_content = path.read_bytes()

        try:
            result = repo.create_file(f"{user}/{path.name}", args.message, file_content)
        except GithubException:
            # file already exist
            if args.update:
                contents = repo.get_contents(f"{user}/{path.name}")
                print(f"{path.name} already exists. Updating it.", file=sys.stderr)
                result = repo.update_file(f"{user}/{path.name}", args.message, file_content, contents.sha)
                print(result["content"].html_url)
            else:
                new_path = f"{path.stem}_{secrets.token_urlsafe(8)}{path.suffix}"
                print(f"{path.name} already exists. Creating {new_path}.", file=sys.stderr)
                result = repo.create_file(f"{user}/{new_path}", args.message, file_content)

        print(f"{repo.html_url}/blob/{result['commit'].sha}/{result['content'].path}")


if __name__ == "__main__":
    main()
