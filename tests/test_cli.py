from unittest.mock import Mock, create_autospec, patch
import io
import os

import pytest
from docopt import DocoptExit
from github import GithubException
from github.Repository import Repository
from pyclip import ClipboardSetupException as RealClipboardSetupException

from shbin import __version__, __doc__, main

PNG_1x1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc\xb8\xbb\xe8=\x00\x04\xce\x02o\x8a\xc4\xab\xc4\x00\x00\x00\x00IEND\xaeB`\x82"
)

def create_github_downloable_files(data):
    class ContentFile:
        pass

    obj = ContentFile()

    for key, value in data.items():
        setattr(obj, key, value)
    return obj

@pytest.fixture
def repo():
    repo = create_autospec(Repository, name="gh_repo")
    repo.create_file.return_value = {"content": Mock(html_url="https://the-url")}
    repo.update_file.return_value = {"content": Mock(html_url="https://the-url-updated")}
    return repo


@pytest.fixture
def pyclip(monkeypatch):
    class Stub:
        def copy(self, content):
            self.content = content

        def paste(self):
            try:
                return self.content
            except AttributeError:
                raise RealClipboardSetupException("missing")

        ClipboardSetupException = RealClipboardSetupException

    clip = Stub()
    monkeypatch.setattr("shbin.pyclip", clip)
    return clip


@pytest.fixture
def stdin(monkeypatch):
    def patch(data):
        monkeypatch.setattr("sys.stdin", Mock(buffer=io.BytesIO(data)))

    # some default data
    patch(b"input data")
    return patch


@pytest.fixture
def patched_repo_and_user(repo):
    with patch("shbin.get_repo_and_user", return_value=(repo, "messi")) as mocked:
        yield mocked


@pytest.mark.parametrize("argv", (["-h"], ["--help"]))
def test_help(capsys, argv):
    with pytest.raises(SystemExit):
        main(argv)

    output = capsys.readouterr().out
    assert __doc__.strip() in output
    assert "Usage:" in output
    assert "Options:" in output


@pytest.mark.parametrize("argv", (["-x", "file1.py"], []))
def test_x_and_files_required_and_exclusive(argv):
    with pytest.raises(DocoptExit):
        main(argv)


def test_version(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])
    assert capsys.readouterr().out == f"{__version__}\n"


def test_token_envvar_is_mandarory(monkeypatch):
    monkeypatch.delenv("SHBIN_GITHUB_TOKEN", raising=False)
    with pytest.raises(DocoptExit) as e:
        main(["foo.py"])

    assert "Ensure SHBIN_GITHUB_TOKEN" in str(e.value)


def test_repo_envvar_is_mandarory(monkeypatch):
    monkeypatch.setenv("SHBIN_GITHUB_TOKEN", "123")
    monkeypatch.delenv("SHBIN_REPO", raising=False)
    with pytest.raises(DocoptExit) as e:
        main(["foo.py"])

    assert "error 'SHBIN_REPO'" in str(e)


def test_upload_file(tmp_path, patched_repo_and_user, repo, pyclip, capsys):
    file = tmp_path / "hello.py"
    file.write_text('print("hello")')
    main([str(file)])
    repo.create_file.assert_called_once_with("messi/hello.py", "", b'print("hello")')
    assert pyclip.paste() == "https://the-url"
    assert capsys.readouterr().out == "🔗📋 https://the-url\n"


@pytest.mark.parametrize("disable", ("0", "false", "no", "FALSE"))
def test_upload_file_no_copy_url(tmp_path, patched_repo_and_user, repo, pyclip, capsys, monkeypatch, disable):
    pyclip.copy("foo")
    monkeypatch.setenv("SHBIN_COPY_URL", disable)
    file = tmp_path / "hello.py"
    file.write_text('print("hello")')
    main([str(file)])
    repo.create_file.assert_called_once_with("messi/hello.py", "", b'print("hello")')
    # url not copied
    assert pyclip.paste() == "foo"
    # no clipboard emoji
    assert capsys.readouterr().out == "🔗 https://the-url\n"


def test_no_files(tmp_path, patched_repo_and_user, repo, capsys):
    main(["NOT_EXISTENT"])
    assert "no file was uploaded" in capsys.readouterr().out


@pytest.mark.parametrize("target", ["project", "project/", "project/subdir"])
def test_upload_file_with_target(tmp_path, patched_repo_and_user, repo, target):
    file = tmp_path / "hello.md"
    file.write_text("hello")
    main([str(file), "-d", target])
    repo.create_file.assert_called_once_with(f"messi/{target.rstrip('/')}/hello.md", "", b"hello")


@pytest.mark.parametrize(
    "namespace, expected",
    [
        ("", "hello.md"),
        ("{user}-goat", "messi-goat/hello.md"),
        ("goat/{user}/", "goat/messi/hello.md"),
    ],
)
def test_upload_with_custom_prefix(tmp_path, patched_repo_and_user, repo, namespace, expected):
    file = tmp_path / "hello.md"
    file.write_text("hello")
    main([str(file), "--namespace", namespace])
    repo.create_file.assert_called_once_with(expected, "", b"hello")


@pytest.mark.parametrize(
    "namespace, expected",
    [
        ("", "hello.md"),
        ("{user}-goat", "messi-goat/hello.md"),
        ("goat/{user}/", "goat/messi/hello.md"),
    ],
)
def test_upload_with_namespace_from_envvar(tmp_path, patched_repo_and_user, repo, namespace, expected, monkeypatch):
    monkeypatch.setenv("SHBIN_NAMESPACE", namespace)
    file = tmp_path / "hello.md"
    file.write_text("hello")
    main([str(file)])
    repo.create_file.assert_called_once_with(expected, "", b"hello")


def test_upload_file_with_target_as_file_confirm(tmp_path, patched_repo_and_user, repo):
    file = tmp_path / "hello.md"
    file.write_text("hello")
    main([str(file), "-d", "bye.md"])
    repo.create_file.assert_called_once_with("messi/bye.md/hello.md", "", b"hello")


def test_upload_glob(tmp_path, monkeypatch, patched_repo_and_user, repo):
    file1 = tmp_path / "hello.md"
    file2 = tmp_path / "bye.md"
    file1.write_bytes(b"hello")
    file2.write_bytes(b"bye")
    monkeypatch.chdir(tmp_path)

    main(["*.md", "-m", "hello and bye"])

    assert repo.create_file.call_count == 2
    repo.create_file.assert_any_call("messi/hello.md", "hello and bye", b"hello")
    repo.create_file.assert_any_call("messi/bye.md", "hello and bye", b"bye")


def test_x_requires_functional_pyclip(pyclip, patched_repo_and_user, repo):
    with pytest.raises(DocoptExit) as e:
        main(["-x"])
    assert "missing" in str(e)


def test_plain_from_clipboard(pyclip, patched_repo_and_user, repo, capsys):
    pyclip.copy(b"some data")
    with patch("shbin.secrets.token_urlsafe", return_value="abc"):
        main(["-x"])
    repo.create_file.assert_any_call("messi/abc.txt", "", b"some data")
    # the url was copied
    assert pyclip.paste() == "https://the-url"
    assert capsys.readouterr().out == "🔗📋 https://the-url\n"


def test_png_from_clipboard(pyclip, patched_repo_and_user, repo, capsys):
    pyclip.copy(PNG_1x1)
    with patch("shbin.secrets.token_urlsafe", return_value="abc"):
        main(["-x"])
    repo.create_file.assert_any_call("messi/abc.png", "", PNG_1x1)
    # the url was copied
    assert pyclip.paste() == "https://the-url"
    assert capsys.readouterr().out == "🔗📋 https://the-url\n"


def test_from_clipboard_with_name(pyclip, patched_repo_and_user, repo, capsys):
    pyclip.copy(b"data")
    main(["-x", "-f", "data.md"])
    repo.create_file.assert_any_call("messi/data.md", "", b"data")
    # the url was copied
    assert pyclip.paste() == "https://the-url"
    assert capsys.readouterr().out == "🔗📋 https://the-url\n"


def test_from_clipboard_with_name_and_directory(pyclip, patched_repo_and_user, repo, capsys):
    pyclip.copy(b"data")
    main(["-x", "-f", "data.md", "-d", "foo"])
    repo.create_file.assert_any_call("messi/foo/data.md", "", b"data")
    # the url was copied
    assert pyclip.paste() == "https://the-url"
    assert capsys.readouterr().out == "🔗📋 https://the-url\n"


def test_from_clipboard_with_namespace(pyclip, patched_repo_and_user, repo, capsys):
    pyclip.copy(b"data")
    main(["-x", "-f", "data.md", "--namespace", "foo"])
    repo.create_file.assert_any_call("foo/data.md", "", b"data")
    # the url was copied
    assert pyclip.paste() == "https://the-url"
    assert capsys.readouterr().out == "🔗📋 https://the-url\n"


def test_plain_from_stdin(stdin, pyclip, patched_repo_and_user, repo, capsys):
    stdin(b"some data")
    with patch("shbin.secrets.token_urlsafe", return_value="abc"):
        main(["-"])
    repo.create_file.assert_any_call("messi/abc.txt", "", b"some data")
    # the url was copied
    assert pyclip.paste() == "https://the-url"
    assert capsys.readouterr().out == "🔗📋 https://the-url\n"


def test_from_stdin_with_name(stdin, pyclip, patched_repo_and_user, repo, capsys):
    stdin(b"data")
    main(["-", "-f", "data.md"])
    repo.create_file.assert_any_call("messi/data.md", "", b"data")
    # the url was copied
    assert pyclip.paste() == "https://the-url"
    assert capsys.readouterr().out == "🔗📋 https://the-url\n"


def test_png_from_stdin(stdin, pyclip, patched_repo_and_user, repo, capsys):
    stdin(PNG_1x1)
    with patch("shbin.secrets.token_urlsafe", return_value="abc"):
        main(["-"])
    repo.create_file.assert_any_call("messi/abc.png", "", PNG_1x1)
    # the url was copied
    assert pyclip.paste() == "https://the-url"
    assert capsys.readouterr().out == "🔗📋 https://the-url\n"


def test_simple_update(pyclip, tmp_path, patched_repo_and_user, repo):
    repo.create_file.side_effect = GithubException(400, data="", headers=None)
    repo.get_contents.return_value.sha = "abc123"
    file = tmp_path / "hello.py"
    file.write_bytes(b"hello")
    main([str(file)])
    repo.get_contents.assert_called_once_with("messi/hello.py")
    repo.update_file.assert_called_once_with("messi/hello.py", "", b"hello", "abc123")


def test_force_new(pyclip, tmp_path, patched_repo_and_user, repo, capsys):
    repo.create_file.side_effect = [
        GithubException(400, data="", headers=None),
        {"content": Mock(html_url="https://the-url-2")},
    ]
    file = tmp_path / "hello.md"
    file.write_bytes(b"hello")

    with patch("shbin.secrets.token_urlsafe", return_value="abc"):
        main([str(file), "-n"])
    assert repo.create_file.call_count == 2
    repo.create_file.assert_called_with("messi/hello_abc.md", "", b"hello")
    assert capsys.readouterr().out == "🔗📋 https://the-url-2\n"

def test_download_a_file(tmp_path, patched_repo_and_user, repo):
    git_data = {
        "decoded_content": b"awesome content",
    }
    repo.get_contents.return_value = create_github_downloable_files(git_data)
    working_dir = tmp_path / "working_dir"
    working_dir.mkdir()
    os.chdir(working_dir)
    main(["dl", "hello.md"])
    assert (working_dir / "hello.md").read_bytes() == b"awesome content"



