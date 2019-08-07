"""
:author: Gatsby Lee
:since: 2019-08-07
"""


class FailedToGetProxyip(Exception):
    pass


class FailedToReleaseProxyip(Exception):
    pass


__all__ = (
    'FailedToGetProxyip',
    'FailedToReleaseProxyip',
)
