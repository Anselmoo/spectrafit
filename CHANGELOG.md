# CHANGELOG

---

> See also: [https://github.com/Anselmoo/spectrafit/releases][1]

## v0.3.2

---

- Replaced poetry hosted `pre-commit` hook with [pre-commit action][6].
- Extend `pre-commit` hook [MyPy][7].
- Fixed a bug for the energy range separation.
- Removed the `--display` option.

## v0.3.1

---

- Introducing `pytest` and `coverage` for increasing code quality.
- Adding [`codecov.io`][5] into the GitHub actions workflow.
- Updating the [contribution guideline][4] with inside milestones.

## v0.2.4

---

- Adding a Docker Workflow via [https://ghcr.io/anselmoo/spectrafit:latest][2].
- Poetry for PyPi release via [https://pypi.org/project/spectrafit/][3].

## v0.2.0

---

- Changed from text file based input to object based input.
- Extended `matplotlib` with `seaborn` for the plotting.
- Start outsourcing code into submodules.

## v0.1.0

---

- The orginal program `fastfit` is now running as `spectrafit` with an own
  installer besed on [POETRY](https://python-poetry.org).

[1]: https://github.com/Anselmoo/spectrafit/releases
[2]: https://ghcr.io/anselmoo/spectrafit:latest
[3]: https://pypi.org/project/spectrafit/
[4]: https://github.com/Anselmoo/spectrafit/blob/master/CONTRIBUTING.md
[5]: https://codecov.io/gh/Anselmoo/spectrafit
[6]: https://github.com/marketplace/actions/pre-commit
[7]: https://mypy.readthedocs.io/en/stable/
