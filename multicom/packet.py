from enum import Enum, unique

@unique
class PacketType(Enum):
    DISCOVERY       = 0 # discovery/reply packet (only returns identifier msg)
    DISCOVERY_HELO  = 1 # discovery reply packet
    PING            = 2 # echo
    GET             = 3 # uses random nonce (does not prevent dupicate callbacks)
    GET_REPLY       = 4 # reply msg after get
    SEND            = 5 # uses nonce (ensures callback only gets called once + order)
    POST            = 6 # uses nonce + sends ack (ensures callback only gets called once + order)
    ACK             = 7 # used to reply after post (contains session id and latest nonce)
