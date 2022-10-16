<!-- @format -->

# CHANGELOG

---

> See also: [https://github.com/Anselmoo/spectrafit/releases][1]

## v0.12.0

---

- Adding metrics for regression analysis as part of the post analysis; see also
  [sklearn-metrics-regression][23]
- Add [art][24] for generating ASCII Decor in the terminal / output.
- Using transposed dataframes for the tabulated output to the terminal.
- Change `global` to `global_` to avoid keyword clash.
- Add plugin for [jupyter-notebook][25] integration in VSCode; see also
  [jupyter-notebook-VSCode][26]
- Change `Dockerimage` to use [jupyter/scipy][27] as base image, see also
  [SpectraFit-Dockerfile][31]
- Adding devcontainer for VSCode; see also [devcontainer][30]
- Change from `to_dict(orient="list")` to `to_dict(orient="split")` for the
  `json` output for including the index.
- Add link to the [GitHub Advisory Database][28] for security issues in the
  `Security nodes`.
- Add CI-Test for `devcontainer` in VSCode; see also [devcontainer-ci][29].
- Add [`pyupgrade`][32] to pre-commit hooks.

## v0.11.0

---

- Focus on maintenance fixed for the `spectrafit` package:
  - [Synk][21] security vulnerabilities fixed
  - [SonarCloud][22] code quality fixed

## v0.10.4

---

- Update docs with topics: ``Changelog`, `README`, `Security`, `Licencse`
- Add docs for `conda` installation

## v0.10.1 - v.10.3

---

- Downgrading `numdifftools` and `openpyxl` for compatibility with the
  [conda-forge-formula][20]

## v0.10.0

---

- Refactor the `pyproject.toml` file for getting it working with `conda`.

## v0.9.0

---

- Adding Python 3.10 support
- Adding [Athena file][19] support
- Increasing code quality by using [`pylint`][18]
- Adding plugin support for `SpectraFit`
  - Starting with input file converter

## v0.8.6

---

- Updating the way of poetry caching
- Update docker actions
- Fixed typo in README.md

## v0.8.3 - v0.8.5

---

- Dependency and GitHub Action Updates

## v0.8.2

---

- Refactor buffer of the _covariance matrix_

## v0.8.1

---

- Updating all `raise` statements
- Add [prettier][17] to CI/CD workflow

## v0.8.0

---

- Introduced smaller enhancement:
  - Printout of the fit parameters in the output file: True/False &#8594; [0, 1,
    2]
  - Keyword check for `SpectraFit`
- Fix smaller bugs:
  - `Pseudo-Voigt` power factor from 0.25 &#8594; 0.2
  - Correct type-definitions for `SpectraFit`

## v0.7.1

---

- Maintenance of the `SpectraFit` package

## v0.7.0

---

- Introducing automatic peak detection for spectra fitting; see also SciPy's
  [`find_peaks`][16]

## v0.6.1

---

- Reformat the [README.md][14] for [PyPi - SpectraFit][15]

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
[11]: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository
[12]: https://git-lfs.github.com
[13]: https://github.com/apps/stale
[14]: https://github.com/Anselmoo/spectrafit/blob/main/README.md
[15]: https://pypi.org/project/spectrafit/
[16]: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
[17]: https://prettier.io
[18]: https://github.com/PyCQA/pylint
[19]: http://bruceravel.github.io/demeter/documents/Athena/index.html
[20]: https://anaconda.org/conda-forge/spectrafit
[21]: https://docs.snyk.io/products/snyk-open-source/language-and-package-manager-support/snyk-for-python
[22]: https://sonarcloud.io
[23]: https://scikit-learn.org/stable/modules/model_evaluation.html
[24]: https://www.4r7.ir
[25]: https://jupyter.org
[26]: https://code.visualstudio.com/docs/datascience/jupyter-notebooks
[27]: https://github.com/jupyter/docker-stacks/blob/main/scipy-notebook/Dockerfile
[28]: https://github.com/advisories?query=type%3Areviewed+ecosystem%3Apip
[29]: https://github.com/marketplace/actions/devcontainers-ci
[30]: https://github.com/Anselmoo/spectrafit/pkgs/container/spectrafit-devcontainer
[31]: https://github.com/Anselmoo/spectrafit/pkgs/container/spectrafit
[32]: https://github.com/Anselmoo/spectrafit/blob/6ca69132a199d3bf458927cf3d4ce6f8fdef0eae/.pre-commit-config.yaml
