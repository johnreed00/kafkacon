# -*- coding: utf-8 -*-
import threading
import logging
import time
import multiprocessing
import io
import struct
import config
from avro.io import BinaryDecoder, DatumReader
from confluent_kafka import Consumer
from confluent_kafka.avro.cached_schema_registry_client import CachedSchemaRegistryClient
from confluent_kafka.avro.serializer import SerializerError
from debug import debug, errx, trace

MAGIC_BYTES = 0

class KafkaConsumer(multiprocessing.Process):

    Conf = {
        'offset': 0,
    }

    ConsumerProperties = {
        'auto.offset.reset': 'earliest'
    }

    DebugOptions = {
        'debug': 'all',
        'log_level': '0'
    }

    consumer = None
    RegistryClient = None

    def __init__(self, conf=None):
        self.getconf(conf)
        self.initSchemaRegistry()
        self.initConsumer()
        if(config.debug >= 3):
            logging.basicConfig( format='%(asctime)s.%(msecs)s:%(name)s:%(thread)d:%(levelname)s:%(process)d:%(message)s', level=logging.DEBUG)

    def getconf(self, conf):
        self.Conf.update(conf['services']['Kafka'])
        self.Conf.update(conf['args'])
        try:
            Properties = self.Conf['properties']
        except:
            self.Conf['properties'] = {}

    def initSchemaRegistry(self):
        try:
            RegistryConfig = {
                'url': self.Conf['schema.registry']
            }
        except:
            return

        self.RegistryClient = CachedSchemaRegistryClient(**RegistryConfig)
        debug(level=1, RegistryClient=self.RegistryClient)

    def assignPartitions(self, consumer, partitions):
        for p in partitions:
            p.offset = int(self.Conf['offset'])

        consumer.assign(partitions)

    def initConsumer(self):
        ConsumerConfig = {
            'bootstrap.servers': str.join(',', self.Conf['brokers']),
            'group.id': self.Conf['groupid']
        }

        ConsumerProperties = {}

        if(config.debug >= 3):
            ConsumerConfig.update(self.DebugOptions)

        trace(ConsumerConfig)
        ConsumerProperties.update(self.ConsumerProperties)
        ConsumerProperties.update(self.Conf['properties'])
        ConsumerConfig.update(ConsumerProperties)
        self.consumer = Consumer(ConsumerConfig)
        self.consumer.subscribe([ self.Conf['topic' ] ], on_assign=self.assignPartitions)

    def unpack(self, payload):
        magic, schema_id = struct.unpack('>bi', payload[:5])

        if magic == MAGIC_BYTES:
            schema = self.RegistryClient.get_by_id(schema_id)
            reader = DatumReader(schema)
            output = BinaryDecoder(io.BytesIO(payload[5:]))
            abc = reader.read(output)
            return abc
        else:
            return payload.decode()

    def readMessageByPartitionOffsetAvro(self):
        _count = False
        print('polling ', end='', flush=True)
        while True:
            try:
                msg = self.consumer.poll(1)
            except SerializerError as e:
                if _count:
                    print('SerializerError')
                print("Message deserialization failed for {}: {}".format(msg, e))
                raise SerializerError

            if msg is None:
                _count = True
                print('.', end='', flush=True)
                continue

            if msg.error():
                if _count:
                    print('msg.error')
                print("AvroConsumer error: {}".format(msg.error()))
                continue

            key, value = self.unpack(msg.key()), self.unpack(msg.value())
            if _count:
                print('ok')
            return value
