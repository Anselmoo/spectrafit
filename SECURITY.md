# Security Policy

This document describes the security policy for [SpectraFit][1].

## Supported Versions

Our current policy is to support the latest version of [SpectraFit][2] and the
last two minor releases.

## Security Checks

Currently, the following security checks are implemented in the CI pipelines or
as third-party services:

| Tool                     | Checks                                                                        |       Implemented as        |
| :----------------------- | :---------------------------------------------------------------------------- | :-------------------------: |
| [GitHub's CodeQL][3]     | Used to check for potential vulnerabilities in the code.                      |     :hammer_and_wrench:     |
| [Synk][4]                | Used to check for known vulnerabilities in the dependencies.                  |           :robot:           |
| [SonarCloud][5]          | Used to find code quality issues and potential vulnerabilities.               |           :robot:           |
| [GitHub's Dependabot][6] | Used to check for outdated dependencies.                                      |           :robot:           |
| [Pre-commit][7]          | Used to check for code quality and formatting issues.                         | :hammer_and_wrench: :robot: |
| [Codecov][8]             | Used to check for coverage rate to ensure that the code is completely tested. | :hammer_and_wrench: :robot: |

Additionally, branch protection rules are used to ensure that the code is
reviewed before it is merged into the main branch.

## Reporting a Vulnerability

If you find a vulnerability, please report it by opening an issue [here][9].
Please use the `vulnerability` template and provide as much information as
possible.

> Current Python vulnerabilities can be found at the [:link:GitHub's Advisory
> Database][10]. See also: [:link:GitHub's Security Lab][11].

[1]: https://github.com/Anselmoo/spectrafit/
[2]: https://github.com/Anselmoo/spectrafit/releases
[3]: https://securitylab.github.com/tools/codeql/
[4]: https://synk.io/
[5]: https://sonarcloud.io/
[6]: https://github.com/dependabot
[7]: https://pre-commit.com/
[8]: https://codecov.io/
[9]: https://github.com/Anselmoo/spectrafit/issues/new/choose
[10]: https://github.com/advisories?query=type%3Areviewed+ecosystem%3Apip
[11]: https://securitylab.github.com/
