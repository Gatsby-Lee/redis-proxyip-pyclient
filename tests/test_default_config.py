from be_proxy_ip import ProxyIP


def test_default_config(mocker):

    # mockup time
    MOCK_TIME = 1564683072
    mocker.patch('time.time', return_value=MOCK_TIME)

    from redis_proxyip_client.config import (
        DefaultRedisProxyipConfig,
    )

    from redis_proxyip_client.config.default_config import (
        LUA_GET_PROXYIP_KEYS,
        LUA_RELEASE_PROXYIP_KEYS,
    )

    config = DefaultRedisProxyipConfig
    keys, args = config._get_keys_args_getting_proxyip()
    assert keys == LUA_GET_PROXYIP_KEYS
    assert len(args) == 1

    proxyip_obj = ProxyIP(proxy_ip='1.2.3.4', proxy_port=3333,
                          proxy_username='hello', proxy_pwd='well',
                          request_ip='1.2.4.5', last_request_time=MOCK_TIME)

    keys, args = config._get_keys_args_releasing_proxyip(proxyip_obj)
    assert keys == LUA_RELEASE_PROXYIP_KEYS
    assert args == [proxyip_obj.proxy_id, proxyip_obj.serialize_proxy()]
