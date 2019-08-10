"""
:author: Gatsby Lee
:since: 2019-08-06
"""
from redis_proxyip_client.third_party import (
    ProxyIP,
    Redis,
)
from redis_proxyip_client.config.default_config import (
    DefaultRedisProxyipConfig,
)


class RedisProxyipClient(object):

    def __init__(self,
                 redis_kwargs_dict=None,
                 config_class=DefaultRedisProxyipConfig):

        self._config = DefaultRedisProxyipConfig

        if redis_kwargs_dict is not None:
            self._redis = Redis(**redis_kwargs_dict)
        else:
            self._redis = Redis()

        self._lua_getting_proxyip = self._redis.register_script(
            self._config.get_lua_getting_proxyip()
        )
        self._lua_releasing_proxyip = self._redis.register_script(
            self._config.get_lua_releasing_proxyip()
        )

    def get_proxyip(self):
        """
        Get proxyip
        """
        return self._config.handler_getting_proxyip(self._lua_getting_proxyip)

    def release_proxyip(self, proxyip_obj):
        """
        Release proxyip
        """
        return self._config.handler_releasing_proxyip(
            self._lua_releasing_proxyip, proxyip_obj)


class NoProxyipClient(object):

    def __init__(self):
        self._proxy_obj = ProxyIP.create_noproxy()

    def get_proxyip(self):
        return self._proxy_obj

    def release_proxyip(self, proxy_obj):
        pass


class OneProxyipClient(object):

    def __init__(self, proxyip_obj):
        self._proxyip_obj = proxyip_obj

    def get_proxyip(self):
        return self._proxyip_obj

    def release_proxyip(self, proxy_obj):
        pass
