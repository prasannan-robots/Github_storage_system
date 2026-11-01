# github_storage_system

Use a GitHub repository as simple file storage — handy for small Flask apps on hosts with an
ephemeral filesystem (Heroku, Render, …).

```bash
pip install github_storage_system
```

```python
from github_storage_system import git_file_server

store = git_file_server("uploads")              # reads GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH

store.push_file("uploads/photo.png")            # uploads, then deletes the local copy
store.push_file("uploads/photo.png", overwrite=True)   # replace an existing file
url = store.pull_absolute_file_link("uploads/photo.png")  # raw.githubusercontent.com URL
data = store.pull_file_content("uploads/photo.png")
store.delete_file("uploads/photo.png")
```

| Environment variable | Purpose |
| --- | --- |
| `GITHUB_TOKEN` | Token with *Contents: read & write* on the storage repo |
| `GITHUB_REPO` | `owner/name` of the storage repo |
| `GITHUB_BRANCH` | Optional; defaults to the repo's default branch |

Files keep their relative path, so `uploads/photo.png` is stored at `uploads/photo.png`.
Keep the storage repo **private** if the files aren't meant to be public (raw links then need
a token).

## 0.1.0

- No longer breaks when `GITHUB_BRANCH` is unset (uses the repo's default branch instead of
  `None`, which made uploads fail and produced `.../None/...` links).
- `delete_file` deletes from the configured branch.
- `pull_all_file_link` no longer skips every other file.
- `push_file(..., overwrite=True)` replaces existing files; `keep_local=True` keeps the local copy.
- `pull_file` creates directories and closes files; clear error when credentials are missing.

## Development

```bash
pip install -e . pytest && pytest
```
