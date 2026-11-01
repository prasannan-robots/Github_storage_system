import base64
import os
import sys
from types import SimpleNamespace

import pytest
from github import GithubException

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "github_storage_system", "src"))
import github_storage_system as gss  # noqa: E402


class FakeRepo:
    default_branch = "main"

    def __init__(self):
        self.files = {}  # (branch, path) -> bytes
        self.calls = []

    def create_file(self, path, message, content, branch):
        assert isinstance(branch, str), "branch must be a string"
        if (branch, path) in self.files:
            raise GithubException(422, {"message": "sha wasn't supplied"}, None)
        self.files[(branch, path)] = content

    def update_file(self, path, message, content, sha, branch):
        self.files[(branch, path)] = content

    def get_contents(self, path, ref):
        if path == "":
            dirs = {p.split("/")[0] for (b, p) in self.files if b == ref and "/" in p}
            top = [SimpleNamespace(type="dir", path=d) for d in sorted(dirs)]
            top += [SimpleNamespace(type="file", path=p) for (b, p) in self.files if b == ref and "/" not in p]
            return top
        if (ref, path) in self.files:
            return SimpleNamespace(type="file", path=path, sha="sha", decoded_content=self.files[(ref, path)])
        return [SimpleNamespace(type="file", path=p) for (b, p) in sorted(self.files) if b == ref and p.startswith(path + "/")]

    def delete_file(self, path, message, sha, branch):
        self.calls.append(("delete", path, branch))
        del self.files[(branch, path)]


@pytest.fixture
def server(monkeypatch, tmp_path):
    repo = FakeRepo()
    monkeypatch.setattr(gss, "Github", lambda token: SimpleNamespace(get_repo=lambda name: repo))
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GITHUB_BRANCH", raising=False)
    s = gss.git_file_server("uploads", token="t", repo="me/store")
    s.fake = repo
    return s


def write(path, data=b"hi"):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def test_defaults_to_repo_default_branch_and_valid_links(server):
    assert server.branch == "main"
    assert server.pull_absolute_file_link("uploads/my pic.png") == \
        "https://raw.githubusercontent.com/me/store/main/uploads/my%20pic.png"


def test_push_removes_local_copy_and_overwrite(server):
    write("uploads/a.txt", b"v1")
    server.push_file("uploads/a.txt")
    assert not os.path.exists("uploads/a.txt")
    write("uploads/a.txt", b"v2")
    with pytest.raises(GithubException):
        server.push_file("uploads/a.txt")
    server.push_file("uploads/a.txt", overwrite=True)
    assert server.pull_file_content("uploads/a.txt") == b"v2"


def test_list_all_links_does_not_skip_files(server):
    for name in "abcd":
        write(f"uploads/{name}.txt")
        server.push_file(f"uploads/{name}.txt")
    assert len(server.pull_all_file_link()) == 4  # used to return only every other file


def test_delete_uses_configured_branch(server):
    write("uploads/a.txt")
    server.push_file("uploads/a.txt")
    server.delete_file("uploads/a.txt")
    assert server.fake.calls == [("delete", "uploads/a.txt", "main")]


def test_pull_file_creates_directories(server):
    write("uploads/deep/x.bin", b"\x00\x01")
    server.push_file("uploads/deep/x.bin")
    server.pull_file("uploads/deep/x.bin")
    assert open("uploads/deep/x.bin", "rb").read() == b"\x00\x01"


def test_missing_credentials_fail_fast(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_REPO", raising=False)
    with pytest.raises(ValueError):
        gss.git_file_server("uploads")
