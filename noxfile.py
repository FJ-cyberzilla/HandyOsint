import nox

PYTHON_VERSION = "3.12"
SOURCE_DIRS = ["api", "core", "ui"]


@nox.session(python=PYTHON_VERSION)
def lint(session):
    """Run pylint using existing config."""
    session.install("-r", "config/requirements-dev.txt")
    session.install("-r", "config/requirements.txt")
    session.install("pylint")
    session.run("pylint", "--disable=C0305", *SOURCE_DIRS)


@nox.session(python=PYTHON_VERSION)
def tests(session):
    """Run pytest with existing pytest.ini."""
    session.install("-r", "config/requirements-dev.txt")
    session.install("pytest", "pytest-asyncio")
    session.run("pytest", "-q")


@nox.session(python=PYTHON_VERSION)
def format(session):
    """Run black + isort for formatting."""
    session.install("black", "isort")
    session.run("black", ".")
    session.run("isort", ".")


@nox.session(python=PYTHON_VERSION)
def typecheck(session):
    """Run mypy type checking."""
    session.install("-r", "config/requirements-dev.txt")
    session.install("mypy")
    session.run("mypy", *SOURCE_DIRS)


@nox.session(python=PYTHON_VERSION)
def safety(session):
    """Run safety and bandit for security checks."""
    session.install("safety", "bandit")
    session.run("safety", "check", "--full-report")
    session.run("bandit", "-r", "api", "core", "ui")


@nox.session(python=PYTHON_VERSION)
def docs(session):
    """Build documentation with MkDocs."""
    session.install("mkdocs", "mkdocs-material")
    session.run("mkdocs", "build", "--strict")
