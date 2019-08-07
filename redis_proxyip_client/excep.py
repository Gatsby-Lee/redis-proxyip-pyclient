"""
:author: Gatsby Lee
:since: 2019-08-07
"""


class FailedToGetProxyipException(Exception):
    pass


class FailedToReleaseProxyipException(Exception):
    pass


__all__ = (
    'FailedToGetProxyipException',
    'FailedToReleaseProxyipException',
)
