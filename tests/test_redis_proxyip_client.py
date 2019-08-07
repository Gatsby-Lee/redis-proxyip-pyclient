import json
import pytest

from redis_proxyip_client import RedisProxyipClient


@pytest.fixture
def client():
    return RedisProxyipClient()


def test_init_proxyip_with_default_config(client):

    from redis_proxyip_client.config.default_config import (
        LUA_GET_PROXYIP,
        LUA_RELEASE_PROXYIP,
    )

    c = RedisProxyipClient()
    assert c._lua_getting_proxyip.script == LUA_GET_PROXYIP
    assert c._lua_releasing_proxyip.script == LUA_RELEASE_PROXYIP


def test_get_proxyip_with_default_config_no_available_proxyip(client):

    from redis_proxyip_client.config.default_config import (
        PROXYIP_POOL,
        IN_USE_PROXYIP_POOL,
        USED_PROXYIP_POOL,
    )
    from redis_proxyip_client.excep import FailedToGetProxyip

    client._redis.delete(PROXYIP_POOL)
    client._redis.delete(IN_USE_PROXYIP_POOL)
    client._redis.delete(USED_PROXYIP_POOL)

    with pytest.raises(FailedToGetProxyip):
        client.get_proxyip()


def test_get_proxyip_with_default_config(client, mocker):

    MOCK_TIME = 1564683072
    mocker.patch('time.time', return_value=MOCK_TIME)

    from redis_proxyip_client.config.default_config import (
        PROXYIP_POOL,
        IN_USE_PROXYIP_POOL,
        USED_PROXYIP_POOL,
    )

    PROXYIP_INFO = [
        1,  # proxy_id
        '1.2.3.4',  # proxy_ip
        3999,  # proxy_port
        'hello-proxy',  # proxy_username
        'hellop-proxy-pwd',  # proxy_pwd
        -1,  # last_request_time
        11,  # num_ok_requests
        22,  # num_banned_requests
        33,  # num_timedout_requests
        44,  # counted
        '4.5.6.7',  # request_ip
    ]
    proxyip_json = json.dumps(PROXYIP_INFO)
    client._redis.delete(PROXYIP_POOL)
    client._redis.delete(IN_USE_PROXYIP_POOL)
    client._redis.delete(USED_PROXYIP_POOL)

    client._redis.lpush(PROXYIP_POOL, proxyip_json)
    proxyip_obj = client.get_proxyip()
    assert client._redis.llen(PROXYIP_POOL) == 0
    assert client._redis.hlen(IN_USE_PROXYIP_POOL) == 1
    assert proxyip_obj.proxy_id == PROXYIP_INFO[0]
    assert proxyip_obj.proxy_ip == PROXYIP_INFO[1]
    assert proxyip_obj.proxy_port == PROXYIP_INFO[2]
    assert proxyip_obj.proxy_username == PROXYIP_INFO[3]
    assert proxyip_obj.proxy_pwd == PROXYIP_INFO[4]
    assert proxyip_obj.last_request_time == PROXYIP_INFO[5]
    assert proxyip_obj.num_ok_requests == PROXYIP_INFO[6]
    assert proxyip_obj.num_banned_requests == PROXYIP_INFO[7]
    assert proxyip_obj.num_timedout_requests == PROXYIP_INFO[8]
    assert proxyip_obj.counted == PROXYIP_INFO[9]
    assert proxyip_obj.request_ip == PROXYIP_INFO[10]

    EXPECTED_PROXYIP_JSON_IN_USE = [
        1,  # proxy_id
        '1.2.3.4',  # proxy_ip
        3999,  # proxy_port
        'hello-proxy',  # proxy_username
        'hellop-proxy-pwd',  # proxy_pwd
        str(MOCK_TIME),  # last_request_time
        11,  # num_ok_requests
        22,  # num_banned_requests
        33,  # num_timedout_requests
        44,  # counted
        '4.5.6.7',  # request_ip
    ]

    ret_proxip_json_in_use = client._redis.hget(
        IN_USE_PROXYIP_POOL, proxyip_obj.proxy_id)

    assert EXPECTED_PROXYIP_JSON_IN_USE == json.loads(ret_proxip_json_in_use)


def test_release_proxyip_with_default_config(client, mocker):

    from redis_proxyip_client.config.default_config import (
        PROXYIP_POOL,
        IN_USE_PROXYIP_POOL,
        USED_PROXYIP_POOL,
    )

    # cleanup queue
    client._redis.delete(PROXYIP_POOL)
    client._redis.delete(IN_USE_PROXYIP_POOL)
    client._redis.delete(USED_PROXYIP_POOL)

    # mockup time
    MOCK_TIME = 1564683072
    mocker.patch('time.time', return_value=MOCK_TIME)

    # generate dummy proxyip
    PROXYIP_INFO = [
        1,  # proxy_id
        '1.2.3.4',  # proxy_ip
        3999,  # proxy_port
        'hello-proxy',  # proxy_username
        'hellop-proxy-pwd',  # proxy_pwd
        -1,  # last_request_time
        11,  # num_ok_requests
        22,  # num_banned_requests
        33,  # num_timedout_requests
        44,  # counted
        '4.5.6.7',  # request_ip
    ]
    proxyip_json = json.dumps(PROXYIP_INFO)

    # add dummy data
    client._redis.lpush(PROXYIP_POOL, proxyip_json)

    # checkout ip / modify it
    proxyip_obj = client.get_proxyip()
    proxyip_obj.num_ok_requests = 100
    proxyip_obj.num_banned_requests = 200
    proxyip_obj.num_timedout_requests = 300

    client.release_proxyip(proxyip_obj)
    assert client._redis.llen(PROXYIP_POOL) == 0
    assert client._redis.llen(IN_USE_PROXYIP_POOL) == 0
    assert client._redis.llen(USED_PROXYIP_POOL) == 1
