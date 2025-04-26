# How to contribute

- [How to contribute](#how-to-contribute)
  - [Setup the development environment](#setup-the-development-environment)
  - [Commit message guidelines](#commit-message-guidelines)
  - [Milestones](#milestones)
  - [Testing](#testing)
  - [Submitting changes](#submitting-changes)
  - [Coding conventions](#coding-conventions)
  - [Note](#note)

We are really glad you're reading this, because we need volunteer developers to
help this project `SpectraFit`.

Here are some important resources:

- [Issues](https://github.com/Anselmoo/spectrafit/issues) for open BUG reports
  or feature requests
- [Pull requests](https://github.com/Anselmoo/spectrafit/pulls) for contributing
  code
- Milestones, which are listed below.

## Setup the development environment

`SpectraFit` is using [uv][4] as python package management system and
[pre-commit][5] for managing git hooks. For fixing bugs or developing new
features, we recommend to use both tools. The python version should be `3.8.1`
or higher and can be optional managed via [pyenv][6].

```bash
# Setting up your Python environment
pyenv local 3.10.0

# Install dependencies with uv
uv pip install -e .

# Install development dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install --install-hooks
```

Even if we have no git hook for code style in `markdown`, `json`, and `yaml`
files, we prefer the [prettier style][7] and its extension for `toml` files.

## Commit message guidelines

We follow the [Conventional Commits][14] specification for our commit messages. This leads to more readable messages that are easy to follow when looking through the project history.

### Commit message format

Each commit message consists of a **header**, a **body** and a **footer**. The header has a special format that includes a **type**, an optional **scope** and a **subject**:

```
<type>[optional scope]: <emoji> <subject>
[optional body]
[optional footer(s)]
```

Examples:

```
feat: ✨ add new peak fitting method
fix: 🐛 handle NaN values in solver
docs: 📝 update usage documentation
```

### Types and emojis

We use the following types and associated emojis:

| Type     |            Emoji             | Description                         |
| -------- | :--------------------------: | ----------------------------------- |
| feat     |      `:sparkles:` (✨)       | A new feature                       |
| fix      |         `:bug:` (🐛)         | A bug fix                           |
| docs     |        `:memo:` (📝)         | Documentation only changes          |
| style    |      `:lipstick:` (💄)       | Changes that do not affect meaning  |
| refactor |       `:recycle:` (♻️)       | Code change that is not a fix/feat  |
| perf     |         `:zap:` (⚡)         | Performance improvement             |
| test     |  `:white_check_mark:` (✅)   | Adding or correcting tests          |
| build    | `:construction_worker:` (👷) | Build system or dependencies        |
| ci       |       `:wrench:` (🔧)        | CI/CD configuration                 |
| chore    |       `:hammer:` (🔨)        | Other changes that don't modify src |
| revert   |       `:rewind:` (⏪)        | Reverts a previous commit           |

### Scope

The scope is optional and should be the name of the module affected (as perceived by the person reading the changelog generated from commit messages).

### Subject

The subject contains a succinct description of the change:

- Use the imperative, present tense: "change" not "changed" nor "changes"
- Don't capitalize the first letter
- No dot (.) at the end

### Body

The body should include the motivation for the change and contrast this with previous behavior.

### Footer

The footer should contain any information about **Breaking Changes** and is also the place to reference GitHub issues that this commit **Closes**.

## Milestones

[Milestones][10] now also available for the `spectrafit` application.
Furthermore, project status can be seen in the [GitHub Project Panel][13].

## Testing

We are using only [GitHub-Actions][1] for [pre-commit][5] testing, the CI/CD
pipeline and the release.

## Submitting changes

Please send a [GitHub Pull Request to SpectraFit][9] with a clear list of what
you've done (read more about
[pull requests](http://help.github.com/pull-requests/)). We can always use more
test coverage. Please follow our coding conventions (below) and make sure all of
your commits are atomic (one feature per commit).

Always write a clear log message for your commits following our [commit message guidelines](#commit-message-guidelines).

In terms of connecting [issues][11] with the corresponding [PR][9], we prefer to
use the the [GitHub convention of using the issue number][12] in the commit
message. This also allows us to easily linking PRs with issues in our [Project
Board][13].

### Branching rules

We follow a Trunk-Based Development approach:

- All changes should branch from `main`
- Use short-lived feature branches named with the pattern: `type/short-description`
  Examples:
  - `feat/peak-fitting`
  - `fix/nan-handling`
  - `docs/usage-update`
- Merge to `main` via pull request after review and passing CI
- Rebase frequently to keep branches up to date with `main`
- Delete feature branches after merge

## Coding conventions

Start reading our code and you'll get the hang of it. We optimize for
readability:

- We use as formaters for Python:
  - [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
  - [![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
  - [![Code style: flake8](https://img.shields.io/badge/code%20style-flake8-brightgreen.svg)](https://flake8.pycqa.org/en/latest/)
  - [Google convention][2] for docstrings
- We use as formater for `Markdown`, `JSON` and `YAML` files:
  - [![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square&logo=prettier)](https://github.com/prettier/prettier)

## Note

This template is adapted from [opengovernment][3].

[1]: https://github.com/Anselmoo/spectrafit/actions
[2]: https://google.github.io/styleguide/pyguide.html
[3]: https://github.com/opengovernment/opengovernment/blob/main/CONTRIBUTING.md
[4]: https://github.com/astral-sh/uv
[5]: https://pre-commit.com
[6]: https://github.com/pyenv/pyenv
[7]: https://prettier.io
[8]: https://lmfit.github.io/lmfit-py/fitting.html
[9]: https://github.com/Anselmoo/spectrafit/pulls
[10]: https://github.com/Anselmoo/spectrafit/milestones
[11]: https://github.com/Anselmoo/spectrafit/issues
[12]: https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue
[13]: https://github.com/Anselmoo/spectrafit/projects/1
[14]: https://www.conventionalcommits.org/
