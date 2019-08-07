"""
:author: Gatsby Lee
:since: 2019-08-06
"""
import json
import time

from be_proxy_ip import ProxyIP
from redis_proxyip_client.excep import (
    FailedToGetProxyip,
    FailedToReleaseProxyip,
)

LUA_GET_PROXYIP = """
local p_json = false
local hset_r = false
local rpush_r = false
local max_retry_for_lpop = 2
local max_retry = 3
for i=1,max_retry_for_lpop do
    p_json = redis.call('lpop', KEYS[1])
    if p_json ~= false then
        break
    end
end

if p_json ~= false then
    local p = cjson.decode(p_json)
    p[6] = ARGV[1]
    local updated_p = cjson.encode(p)
    for i=1,max_retry do
        hset_r = redis.call('hset', KEYS[2], p[1], updated_p)
        if hset_r ~= false then break end
    end

    -- failed to set proxy in hash::checked_out_proxy_servers
    -- push it back to list:proxy_servers
    if hset_r == false then
        for i=1,max_retry do
            rpush_r = redis.call('rpush', KEYS[1], p_json)
            if rpush_r ~= false then break end
        end

        -- if successfully pushing back to available pool, reset p_json
        -- otherwise, just use it. anyway it will be lost since fail to hset and rpush
        if rpush_r ~= false then
            p_json = false
        end
    end
end

return {p_json, hset_r, rpush_r}
"""

LUA_RELEASE_PROXYIP = """
local hdel_r = false
local rpush_r = false
local hset_r = false
local max_retry = 3

for i=1,max_retry do
    hdel_r = redis.call('hdel', KEYS[1], ARGV[1])
    if hdel_r ~= false then break end
end

if hdel_r ~= false then
    for i=1,max_retry do
        rpush_r = redis.call('rpush', KEYS[2], ARGV[2])
        if rpush_r ~= false then break end
    end

    if rpush_r == false then
        for i=1,max_retry do
            hset_r = redis.call('hset', KEYS[1], ARGV[2])
            if hset_r ~= false then break end
        end
    end
end

return {rpush_r, hdel_r, hset_r}
"""

PROXYIP_POOL = 'list:proxy_servers'
USED_PROXYIP_POOL = 'list:used_proxy_servers'
IN_USE_PROXYIP_POOL = 'hash::checked_out_proxy_servers'

LUA_GET_PROXYIP_KEYS = [
    PROXYIP_POOL,
    IN_USE_PROXYIP_POOL,
]

LUA_RELEASE_PROXYIP_KEYS = [
    IN_USE_PROXYIP_POOL,
    USED_PROXYIP_POOL,
]


class DefaultRedisProxyipConfig(object):

    @classmethod
    def get_lua_getting_proxyip(cls):
        return LUA_GET_PROXYIP

    @classmethod
    def _get_keys_args_getting_proxyip(cls):
        return (LUA_GET_PROXYIP_KEYS, [int(time.time())],)

    @classmethod
    def _handler_getting_proxyip_response(cls, redis_response):
        if redis_response is None or redis_response[0] is None:
            raise FailedToGetProxyip()

        proxyip_tuple = json.loads(redis_response[0])
        proxyip_obj = ProxyIP.create_from_tuple(proxyip_tuple)
        return proxyip_obj

    @classmethod
    def handler_getting_proxyip(cls, redis_lua_instance):
        keys, args = cls._get_keys_args_getting_proxyip()
        redis_response = redis_lua_instance(keys=keys, args=args)
        return cls._handler_getting_proxyip_response(redis_response)

    @classmethod
    def get_lua_releasing_proxyip(cls):
        return LUA_RELEASE_PROXYIP

    @classmethod
    def _get_keys_args_releasing_proxyip(cls, proxyip_obj):
        proxyip_obj.last_request_time = int(time.time())
        serialized_proxyip_obj = proxyip_obj.serialize_proxy()
        return (LUA_RELEASE_PROXYIP_KEYS,
                [proxyip_obj.proxy_id, serialized_proxyip_obj],
                )

    @classmethod
    def _handler_releasing_proxyip_response(cls, redis_response):
        if redis_response is None \
                or redis_response[0] is None \
                or redis_response[1] is None:
            raise FailedToReleaseProxyip()

    @classmethod
    def handler_releasing_proxyip(cls, redis_lua_instance, proxyip_obj):
        keys, args = cls._get_keys_args_releasing_proxyip(proxyip_obj)
        redis_response = redis_lua_instance(keys=keys, args=args)
        return cls._handler_releasing_proxyip_response(redis_response)


__all__ = (
    'LUA_GET_PROXYIP',
    'LUA_RELEASE_PROXYIP',
    'LUA_GET_PROXYIP_KEYS',
    'LUA_RELEASE_PROXYIP_KEYS',
    'IN_USE_PROXYIP_POOL',
    'PROXYIP_POOL',
    'USED_PROXYIP_POOL',
    'DefaultRedisProxyipConfig',
)
