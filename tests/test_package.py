"""Package discovery tests."""

import argumap


def test_package_is_importable() -> None:
    """The installed distribution exposes the argumap package."""
    assert argumap.__doc__
