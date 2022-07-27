"""Upload content to your pastebin repo"""
usage = """

Usage:
  shbin (-h | --help)
  shbin (<path>... | -x ) [-n] [-m <message>] [-o <target_path>]


Options:
  -h --help                                 Show this screen.
  -x --from-clipboard                       Paste content from clipboard instead file/s
  -m <message>, --message=<message>         Commit message
  -o <target>, --target=<target>            Optional filename or directory to upload file/s
  -n --new                                  Create a new file if the given already exists
  
"""

import itertools
import os
import pathlib
import secrets
import sys
from mimetypes import guess_extension

import magic
import pyclip
from docopt import DocoptExit, docopt
from github import Github, GithubException
from rich import print
from rich.prompt import Confirm

__version__ = "0.1"


class FakePath:
    """
    A wrapper on a PurePath object (ie it doesn’t actually access a filesystem)
    with an explicity content in bytes.
    """

    def __init__(self, *args, content=b""):
        self._path = pathlib.PurePath(*args)
        self._content = content

    def read_bytes(self):
        return self._content

    def __getattr__(self, attr):
        return getattr(self._path, attr)


def get_repo_and_user():
    gh = Github(os.environ["SHBIN_GITHUB_TOKEN"])
    return gh.get_repo(os.environ["SHBIN_REPO"]), gh.get_user().login


def expand_paths(path_or_patterns):
    """
    receive a list of relative paths or glob patterns and return an iterator of Path instances
    """
    patterns = []
    for path_or_pattern in path_or_patterns:
        if str(path_or_pattern).startswith("/"):
            # if it's absolute, we assume it's a path
            patterns.append([pathlib.Path(path_or_pattern)])
        else:
            patterns.append(pathlib.Path(".").glob(path_or_pattern))

    return itertools.chain.from_iterable(patterns)


def main(argv=None) -> None:
    args = docopt(__doc__ + usage, argv, version=__version__)
    try:
        repo, user = get_repo_and_user()
    except Exception as e:
        raise DocoptExit(
            f"Ensure SHBIN_GITHUB_TOKEN and SHBIN_REPO environment variables are correctly set. (error {e})"
        )

    if args["--from-clipboard"]:
        try:
            content = pyclip.paste()
        except pyclip.ClipboardSetupException as e:
            raise DocoptExit(str(e))

        if args["--target"]:
            directory, path_name = pathlib.PurePath(args["--target"]).parts
            directory = f"{user}/{directory}"
        else:
            extension = guess_extension(magic.from_buffer(content, mime=True))
            # TODO try autodectect extension via pygment if .txt was guessed.
            path_name = f"{secrets.token_urlsafe(8)}{extension}"
            directory = f"{user}"
        files = [FakePath(path_name, content=content)]
        
    else:
        files = list(expand_paths(args["<path>"]))
        dir_target = args["--target"] or ""

        if (
            files
            and pathlib.PurePath(dir_target).suffix
            and not Confirm.ask(
                "--output looks like a file, not a directory. Are you sure?"
            )
        ):
            raise SystemExit(f"🚪 ok, see you soon")

        directory = f"{user}/{dir_target}".rstrip("/")

    message = args["--message"] or ""

    for path in files:
        file_content = path.read_bytes()

        try:
            result = repo.create_file(f"{directory}/{path.name}", message, file_content)
        except GithubException:
            # file already exists
            if args["--new"]:
                new_path = f"{path.stem}_{secrets.token_urlsafe(8)}{path.suffix}"
                print(
                    f"[bold yellow]warning:[/bold yellow] {path.name} already exists. Creating as {new_path}.",
                    file=sys.stderr,
                )
                result = repo.create_file(
                    f"{directory}/{new_path}", message, file_content
                )

            else:
                # TODO upload all the files in a single commit
                contents = repo.get_contents(f"{directory}/{path.name}")
                print(
                    f"[bold yellow]warning:[/bold yellow] {path.name} already exists. Updating it.",
                    file=sys.stderr,
                )
                result = repo.update_file(
                    f"{directory}/{path.name}", message, file_content, contents.sha
                )

    if not files:
        print("🤷 [bold]no file was uploaded[/bold]")
    else:
        url = (
            result["content"].html_url.rpartition("/")[0]
            if len(files) > 1
            else result["content"].html_url
        )
        emoji = "🔗"
        try:
            pyclip.copy(str(url))
            emoji += "📋"
        except pyclip.ClipboardSetupException:
            pass
        print(f"{emoji} {url}")


if __name__ == "__main__":
    main()
