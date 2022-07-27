import pytest

from shbin import FakePath, expand_paths


def test_fake_path():
    fp = FakePath("foo.py", content=b"x123")
    assert fp.read_bytes() == b"x123"
    assert fp.suffix == ".py"
    assert fp.stem == "foo"
    assert fp.is_absolute() is False


@pytest.fixture
def a_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for f in "abc":
        (tmp_path / f"{f}.py").touch()
    (tmp_path / "smile.png").touch()
    (tmp_path / "subdir").mkdir() 
    (tmp_path / "subdir/readme.txt").touch()
    return tmp_path


@pytest.mark.parametrize('given, expected', [
    (["*.py"], {"a.py", "b.py", "c.py"}),
    (["smile.png"], {"smile.png"}),
    (["a.py", "smile.png"], {"smile.png", "a.py"}),
    (["smile.png", "subdir/*"], {"smile.png", "subdir/readme.txt"}),
])
def test_expand_path_with_relative_patterns(given, expected, a_dir):
    assert {str(path) for path in expand_paths(given)} == expected


def test_expand_path_support_absolute(a_dir):
    a_absolute = (a_dir / "a.py").resolve()
    assert next(expand_paths([a_absolute])) == a_absolute
