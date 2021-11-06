# CHANGELOG

---

> See also: [https://github.com/Anselmoo/spectrafit/releases][1]

## v0.6.0

---

- Introduce the **Global-Fitting** option, which allows to fit the several
  spectra with a single model.
- Changed the input for **Pseudo-Voigt**:
  - _`fwhm_g`_ &#8594; **`fwhmg`**
  - _`fwhm_l`_ &#8594; **`fwhml`**
- Changed the input for **Gaussian-FWHM** and **Lorentzian-FWHM**:
  - _`fwhm`_ &#8594; **`fwhmg`**
  - _`fwhm`_ &#8594; **`fwhml`**
- Changed the input for **Voigt-FWHM**:
  - _`fwhm`_ &#8594; **`fwhmv`**
- Adding error-handling for not determatination of _Confiden Interval_.

## v0.5.6

---

- CI/CD pipeline is now token-protected.

## v0.5.5

---

- Removed the `setuptools==57.5.0` limitation due to formally `Python2.7`.

## v0.5.4

---

- Adding a [stale boot][13] for keeping the issue and PRs up-to-date.

## v0.5.3

---

- Extending unit tests to the `SpectraFit` package.

## v0.5.2

---

- Adding maintainer to the `pyproject.yml` file.

## v0.5.1

---

- Minor fix of broken links in docs.

## v0.5.0

---

- Rewrite `SpectraFit` main to become a more object-oriented approach.
- Increase the coverage quality of the tests.

## v0.4.2

---

- Removed the [`GIT LFS`][12] integration for avoiding trouble with broken
  images.
- Adding [`YAML`-Forms][11] as pull request template.

## v0.4.1

---

- Change from `MarkDown` based issue templates to [`YAML`-Forms][11] by GitHub
  as issue and feature request templates.

## v0.4.0

---

- Create [SECURITY policy][8] for the `spectrafit` application.
- Adding [dependabot][9] for updating `poetry.lock`, `pyproject.toml` and GitHub
  Action workflow.
- Adding a [codeql-analysis][10]
- Increasing the coverage level

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
[4]: https://github.com/Anselmoo/spectrafit/blob/main/CONTRIBUTING.md
[5]: https://codecov.io/gh/Anselmoo/spectrafit
[6]: https://github.com/marketplace/actions/pre-commit
[7]: https://mypy.readthedocs.io/en/stable/
[8]: https://github.com/Anselmoo/spectrafit/security
[9]: https://dependabot.com
[10]: https://securitylab.github.com/tools/codeql/
[11]:
  https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository
[12]: https://git-lfs.github.com
[13]: https://github.com/apps/stale
