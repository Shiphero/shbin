"""
Turns a Github repo into a pastebin.
"""
import itertools
import os
import pathlib
import re
import secrets
import sys
import time
from mimetypes import guess_extension


import pyclip
from docopt import DocoptExit, docopt
from github import Github, GithubException
from rich import print
import requests

usage = """

Usage:
  shbin dl <url_or_path>  
  shbin run [--logs] [--command=<command>] <url_or_path>
  shbin (<path>... | -x | -) [-f <file-name>] [-n] [-m <message>] [-d <target-dir>] 
        [--namespace=<namespace>] [--url-link-to-pages]
  shbin (-h | --help)
  

Options:
  -h --help                                         Show this screen.
  -x --from-clipboard                               Paste content from clipboard instead file/s
  -n --new                                          Create a new file if the given already exists
  -f <file-name>, --file-name=<file-name>           Add name to content of clipboard
  -m <message>, --message=<message>                 Commit message
  -d <target-dir>, --target-dir=<target-dir>        Optional (sub)directory to upload file/s. 
  --namespace=<namespace>                           Base namespace to upload. Default to
                                                    SHBIN_NAMESPACE envvar or "{user}/". 
  --command=<command>                               How to run the given file. Default "auto".
  -p, --url-link-to-pages                           Reformat the url to link to Github pages. 
"""

__version__ = "0.3.0"


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
    try:
        user = gh.get_user().login
    except GithubException:
        user = os.environ.get("SHBIN_FORCE_USER")
        if not user:
            raise
    return gh.get_repo(os.environ["SHBIN_REPO"]), user


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


def get_extension(content):
    try:
        import magic
    except ImportError as e:
        print(
            f"[bold yellow]warning:[/bold yellow] check the README to correctly install python-magic. Import Error: {e}"
        )
        return ""
        # Optionally could we detect a few formats in our own?
        # for instance, images are easy https://stackoverflow.com/a/27670182/811740
    else:
        return guess_extension(magic.from_buffer(content, mime=True))


def normalize_path(url_or_path, repo):
    return re.sub(rf"^https://github\.com/{repo.full_name}/(blob|tree)/{repo.default_branch}/", "", url_or_path).rstrip(
        "/"
    )


def run(url_or_path, repo, user, show_logs=True, command="auto"):
    path = normalize_path(url_or_path, repo)
    wf = repo.get_workflow("run_script.yml")

    if command == "auto":
        import ipdb;ipdb.set_trace()
        executables = {"py": "python", "sh": "bash", "js": "node", "rb": "ruby", "php": "php", "go": "go run"}
        extension = path.rpartition(".")[-1]
        try:
            command = executables[extension]
        except KeyError:
            raise DocoptExit(f"Unknown command for .{extension} files")

    wf.create_dispatch(repo.default_branch, {"file_path": path, "command": command})
    while True:
        run = wf.get_runs(user, repo.default_branch, event="workflow_dispatch")[0]
        if run.status == "in_progress":
            job = run.jobs()[0]
            break
        time.sleep(1)
        continue

    print(f"⚙️  {job.html_url}")

    if show_logs:
        url = job.logs_url()
        sentinel = "Cleaning up orphan processes"  # determines the logs is finished
        seen = 0
        while True:
            response = requests.get(url)
            lines = response.text.splitlines()
            new_lines = lines[seen:]
            seen = len(lines)
            for line in new_lines:
                print(line)
            if sentinel in line:
                break
    while job.status != "completed":
        job.update()
        time.sleep(1)

    output = repo.get_contents(f"{user}/{path}_run_{run.id}/output.txt").decoded_content.decode("utf-8")
    print(f"[green]Result:[/green]\n\n{output}")
    print(f"More: shbin dl {path}_run_{run.id}")


def download(url_or_path, repo, user):
    """
    # download a file
    $ shbin dl https://github.com/Shiphero/pastebin/blob/main/bibo/AWS_API_fullfilment_methods/AWS_fulfillment_methods.ipynb
    $ shbin dl bibo/AWS_API_fullfilment_methods/AWS_fulfillment_methods.ipynb

    # or a folder
    $ shbin dl https://github.com/Shiphero/pastebin/blob/main/bibo/AWS_API_fullfilment_methods/
    $ shbin dl bibo/AWS_API_fullfilment_methods/
    """
    path = normalize_path(url_or_path, repo)
    try:
        content = repo.get_contents(path)
        if isinstance(content, list):
            # FIXME currently this will flatten the tree:
            # suposse dir/foo.py and dir/subdir/bar.py
            # Then `$ shbin dl dir` will get foo.py and bar.py in the same dir.
            for content_file in content:
                download(content_file.path, repo, user)
            return
        else:
            content = content.decoded_content
    except GithubException:
        if not path.startswith(f"{user}/"):
            new_path = f"{user}/{path}"
            print(f"[yellow]trying {new_path}")
            return download(new_path, repo, user)
        print("[red]x[/red] content not found")
    else:
        target = pathlib.Path(path).name
        pathlib.Path(target).write_bytes(content)
        print(f"[green]✓[/green] downloaded {target}")


def main(argv=None) -> None:
    args = docopt(__doc__ + usage, argv, version=__version__)
    try:
        repo, user = get_repo_and_user()
    except Exception as e:
        raise DocoptExit(
            f"Ensure SHBIN_GITHUB_TOKEN and SHBIN_REPO environment variables are correctly set. (error {e})"
        )
    # resolves namespace + target-dir (without ending slash)
    # it also interpolates {user}
    namespace = args.get("--namespace")
    if namespace is None:
        namespace = os.environ.get("SHBIN_NAMESPACE", "{user}")
    namespace = namespace.format(user=user).rstrip("/")
    if args["--target-dir"]:
        namespace += f"/{args['--target-dir'].rstrip('/')}"

    if args["dl"]:
        return download(args["<url_or_path>"], repo, user)
    elif args["run"]:
        return run(args["<url_or_path>"], repo, user, args["--logs"], args["--command"])
    elif args["--from-clipboard"] or args["<path>"] == ["-"]:
        if args["--from-clipboard"]:
            try:
                content = pyclip.paste()
            except pyclip.ClipboardSetupException as e:
                raise DocoptExit(str(e))
        else:
            content = sys.stdin.buffer.read()

        if args["--file-name"]:
            file_name = f'{args["--file-name"]}'
        else:
            extension = get_extension(content)
            # TODO try autodectect extension via pygment if .txt was guessed.
            file_name = f"{secrets.token_urlsafe(8)}{extension}"
        files = [FakePath(file_name, content=content)]
    else:
        files = list(expand_paths(args["<path>"]))
        if args["--file-name"]:
            if len(files) > 1:
                raise DocoptExit("--file-name can only be used with a single file")

            file_name = args["--file-name"]
            content = files[0].read_bytes()
            files = [FakePath(file_name, content=content)]

    message = args["--message"] or ""

    for path in files:
        result = create_or_update(repo, path, namespace, message, args["--new"])

    if not files:
        print("🤷 [bold]no file was uploaded[/bold]")
    else:
        url = result["content"].html_url.rpartition("/")[0] if len(files) > 1 else result["content"].html_url
        if args["--url-link-to-pages"]:
            content = url.partition(f"{repo.default_branch}/")[-1]
            url = f"https://{repo.owner.login.lower()}.github.io/{repo.name}/{content}"

        emoji = "🔗"
        try:
            if os.environ.get("SHBIN_COPY_URL", "").strip().lower() not in ("0", "false", "no"):
                pyclip.copy(str(url))
                emoji += "📋"
        except pyclip.ClipboardSetupException:
            pass
        print(f"{emoji} {url}")


def create_or_update(repo, path, namespace, message, force_new):
    file_content = path.read_bytes()
    file_name = f"{namespace}/{path.name}".lstrip("/")
    try:
        result = repo.create_file(file_name, message, file_content)
    except GithubException:
        # file already exists
        if force_new:
            new_path = f"{path.stem}_{secrets.token_urlsafe(8)}{path.suffix}"
            print(
                f"[bold yellow]warning:[/bold yellow] {path.name} already exists. Creating as {new_path}.",
                file=sys.stderr,
            )
            result = repo.create_file(f"{namespace}/{new_path}".lstrip("/"), message, file_content)

        else:
            # TODO upload all the files in a single commit
            contents = repo.get_contents(file_name)
            print(
                f"[bold yellow]warning:[/bold yellow] {path.name} already exists. Updating it.",
                file=sys.stderr,
            )
            result = repo.update_file(file_name, message, file_content, contents.sha)
    return result


if __name__ == "__main__":
    main()
