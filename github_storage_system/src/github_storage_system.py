"""Use a GitHub repository as simple file storage (e.g. for a Flask app)."""

import os

from github import Github, GithubException


class git_file_server:
    """Pushes, pulls and deletes files in a GitHub repository.

    Files are stored at the same relative path they have locally, so
    ``push_file("uploads/a.png")`` creates ``uploads/a.png`` in the repo.

    Credentials default to environment variables:
        GITHUB_TOKEN   token with contents write access
        GITHUB_REPO    "owner/name" of the storage repository
        GITHUB_BRANCH  optional; defaults to the repository's default branch
    """

    def __init__(self, path_of_upload_folder, token=None, repo=None, branch=None):
        token = token or os.getenv("GITHUB_TOKEN")
        repo = repo or os.getenv("GITHUB_REPO")
        if not token or not repo:
            raise ValueError("Set GITHUB_TOKEN and GITHUB_REPO (or pass token= and repo=).")

        self.path_of_upload_folder = path_of_upload_folder
        self.token = token
        self.repo = repo
        self.github_object = Github(token)
        self.repository = self.github_object.get_repo(repo)
        # Passing branch=None to PyGithub fails and produced ".../None/..." links.
        self.branch = branch or os.getenv("GITHUB_BRANCH") or self.repository.default_branch
        self.pushed_files = []  # files pushed by this instance
        self.files_in_github = []  # result of the last pull_all_filename()

    def push_file(self, filename, overwrite=False, keep_local=False):
        """Uploads a local file to the same path in the repository.

        Raises if the file already exists unless ``overwrite=True``. The local
        copy is deleted afterwards unless ``keep_local=True``.
        """
        with open(filename, "rb") as f:
            content = f.read()
        path = self._repo_path(filename)
        try:
            self.repository.create_file(path, f"Add {path}", content, branch=self.branch)
        except GithubException as error:
            if not overwrite or error.status != 422:  # 422: file already exists
                raise
            existing = self.repository.get_contents(path, ref=self.branch)
            self.repository.update_file(path, f"Update {path}", content, existing.sha, branch=self.branch)
        self.pushed_files.append(path)
        if not keep_local and os.path.exists(filename):
            os.remove(filename)

    def push_all_files(self, overwrite=False):
        """Pushes every file in the upload folder."""
        for entry in os.scandir(self.path_of_upload_folder):
            if entry.is_file():
                self.push_file(entry.path, overwrite=overwrite)

    def pull_all_filename(self):
        """Returns the paths of all files in the repository."""
        self.files_in_github = []
        contents = self.repository.get_contents("", ref=self.branch)
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(self.repository.get_contents(file_content.path, ref=self.branch))
            else:
                self.files_in_github.append(file_content.path)
        return self.files_in_github

    def pull_file_content(self, filename):
        """Returns the file's bytes."""
        return self.repository.get_contents(self._repo_path(filename), ref=self.branch).decoded_content

    def pull_file(self, filename):
        """Downloads a file to the same relative path locally."""
        content = self.pull_file_content(filename)
        directory = os.path.dirname(filename)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(filename, "wb") as f:
            f.write(content)

    def pull_all_files(self):
        for name in self.pull_all_filename():
            self.pull_file(name)

    def pull_file_link(self, filename):
        """github.com link that serves the raw file."""
        return f"https://github.com/{self.repo}/blob/{self.branch}/{self._url_path(filename)}?raw=true"

    def pull_absolute_file_link(self, filename):
        """raw.githubusercontent.com link to the file."""
        return f"https://raw.githubusercontent.com/{self.repo}/{self.branch}/{self._url_path(filename)}"

    def pull_all_file_link(self):
        # The old version removed items from the list while iterating over
        # it, which skipped every other file.
        return [self.pull_file_link(name) for name in self.pull_all_filename()]

    def delete_file(self, filename):
        path = self._repo_path(filename)
        contents = self.repository.get_contents(path, ref=self.branch)
        self.repository.delete_file(contents.path, f"Delete {contents.path}", contents.sha, branch=self.branch)

    def delete_all_files(self):
        for name in self.pull_all_filename():
            self.delete_file(name)

    def push_file_get_link(self, filename, overwrite=False):
        self.push_file(filename, overwrite=overwrite)
        return self.pull_file_link(filename)

    @staticmethod
    def _repo_path(filename):
        path = str(filename).replace(os.sep, "/")
        while path.startswith("./"):
            path = path[2:]
        return path.lstrip("/")

    @classmethod
    def _url_path(cls, filename):
        from urllib.parse import quote

        return quote(cls._repo_path(filename))
