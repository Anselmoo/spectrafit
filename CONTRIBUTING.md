# How to contribute

We are really glad you're reading this, because we need volunteer developers to
help this project `SpectraFit`.

Here are some important resources:

- [Issues](https://github.com/Anselmoo/spectrafit/issues) for open BUG reports
  or feature requests
- [Pull requests](https://github.com/Anselmoo/spectrafit/pulls) for contributing
  code
- Millestones, which are listed below.

## Milestones

- [ ] Introducing a class concept for `SpectraFit` because it i
- [ ] Introducing JupyterLab
- [ ] Implementing genetic solvers for fitting optimization problems
- [ ] Updating the Docker package configuration

## Testing

We are using only [GitHub-Actions][1] for pre-commit testing, the CI/CD pipeline
and the release.

## Submitting changes

Please send a
[GitHub Pull Request to SpectraFit](https://github.com/Anselmoo/spectrafit/pulls)
with a clear list of what you've done (read more about
[pull requests](http://help.github.com/pull-requests/)). We can always use more
test coverage. Please follow our coding conventions (below) and make sure all of
your commits are atomic (one feature per commit).

Always write a clear log message for your commits. One-line messages are fine
for small changes, but bigger changes should look like this:

    $ git commit -m "A brief summary of the commit
    >
    > A paragraph describing what changed and its impact."

## Coding conventions

Start reading our code and you'll get the hang of it. We optimize for
readability:

- We use as formaters:
  - [black](https://black.readthedocs.io/en/stable/)
  - [isort](https://pycqa.github.io/isort/)
  - [flake8](https://flake8.pycqa.org/en/latest/)
- We use the [google convention][2] for docstrings
- We use for `Markdown` and `JSON` [https://prettier.io](https://prettier.io)

## Note:

This template is adapted from [opengovernment][3].

[1]: https://github.com/Anselmoo/spectrafit/actions
[2]: https://google.github.io/styleguide/pyguide.html
[3]:
  https://github.com/opengovernment/opengovernment/blob/master/CONTRIBUTING.md
