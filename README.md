# django-faq

FAQ module for Volkanos — structured Q&A with soft entity references, T9N translations,
image support, and group management.

## Installation

```shell
pip install entirius-django-faq
```

Add the app to your project:

```python
INSTALLED_APPS = [
    ...
    "django_regional",
    "django_faq",
]
```

## Development

```shell
make install     # sync dependencies (uv)
make check       # lint + format check (ruff)
make test        # test suite (pytest + pytest-django)
```

Development and agent instructions: [AGENTS.md](AGENTS.md).

## License

Mozilla Public License 2.0 — see [LICENSE](LICENSE).
