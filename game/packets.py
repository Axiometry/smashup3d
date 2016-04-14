# PACKETS
import json
from util import RWLock


class PacketSerializer:
    def __init__(self):
        self._packets_by_class = {}
        self._packets_by_name = {}
        self._packet_lock = RWLock()

    def register(self, packet_class, packet_name=None):
        self._packet_lock.writer_acquire()
        try:
            if packet_name is None:
                packet_name = packet_class.__name__
            if packet_name in self._packets_by_name:
                raise PacketConflictException("Conflicting packet name '" + packet_name + "'")
            self._packets_by_name[packet_name] = packet_class
            self._packets_by_class[packet_class] = packet_name
        finally:
            self._packet_lock.writer_release()

    def unregister(self, packet_class):
        self._packet_lock.writer_acquire()
        try:
            name = self._packets_by_class[packet_class]
            del self._packets_by_class[packet_class]
            del self._packets_by_name[name]
        finally:
            self._packet_lock.writer_release()

    def serialize(self, packet):
        self._packet_lock.reader_acquire()
        try:
            if packet.__class__ not in self._packets_by_class:
                raise BadPacketException("Tried to serialize unknown packet '" + str(packet.__class__) + "'")

            table = {'__packet_name': self._packets_by_class[packet.__class__]}
            for name in vars(packet):
                table[name] = getattr(packet, name)

            return json.dumps(table)
        finally:
            self._packet_lock.reader_release()

    def deserialize(self, string):
        self._packet_lock.reader_acquire()
        try:
            table = json.loads(string)
            if '__packet_name' not in table or table['__packet_name'] not in self._packets_by_name:
                raise BadPacketException("Tried to deserialize unknown packet '" + table)

            packet = self._packets_by_name[table['__packet_name']].__call__()
            targets = [x for x in vars(packet)]
            for f in table:
                if f != '__packet_name':
                    if f not in targets:
                        raise BadPacketException("Bad initialization of packet '" + table['__packet_name'] + "'")
                    setattr(packet, f, table[f])
                    targets.remove(f)
            if len(targets) != 0:
                raise BadPacketException("Bad initialization of packet '" + table['__packet_name'] + "'")
            return packet
        finally:
            self._packet_lock.reader_release()


class BadPacketException(Exception):
    pass


class PacketConflictException(Exception):
    pass


class Packet(object):
    pass
