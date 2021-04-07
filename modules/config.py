# -*- coding: utf-8 -*-
import argparse
import json
import sys
import os
import yaml
from debug import errx, debug, trace

def getConf(args):
    global debug

    default_filename = 'config.yaml'
    parser = argparse.ArgumentParser('KafkaCon')
    parser.add_argument('--brokers', type=str, dest='brokers', nargs='*', action='store', default=[], help='The List of brokers to connect (required)')
    parser.add_argument('--offset', type=str, action='store', default=None, help='The offset to seek to (required)')
    parser.add_argument('--topic', type=str, action='store', default=None, help='The topic (required)')
    parser.add_argument('--groupid', type=str, action='store', default=None, help='Client group id string. All clients sharing the same group.id belong to the same group (required)')
    parser.add_argument('--filename', type=str, action='store', default=default_filename, help='The filename to read configuration for KMS/Kafka (optional, default: config.yaml)')
    parser.add_argument('--debug', type=int, action='store', default=0, help='Debug level (0..3) (optional)')
    parser.add_argument('--input', type=str, action='store', default='kafka', help='The input to read CiphertextBlob: kafka|stdin (optional, default:kafka)')
    parser.add_argument('--decrypt', type=str, action='store', default='aws_encryption_sdk', help='The decryption method: aws_encryption_sdk|aws_kms (optional, default:aws_encryption_sdk)')
    options = parser.parse_args(args)

    filename = getattr(options, 'filename')
    debug = getattr(options, 'debug')
    _input = getattr(options, 'input')
    if not (_input == 'kafka' or _input == 'stdin'):
        raise ValueError("'input' value is not valid, must be 'kafka' or 'stdin'")

    decrypt = getattr(options, 'decrypt')
    if not (decrypt == 'aws_encryption_sdk' or decrypt == 'aws_kms'):
        raise ValueError("'decrypt' value is not valid, must be 'aws_encryption_sdk' or 'aws_kms'")

    try:
        fd = open(filename)
    except IOError as error:
        filename = default_filename
        fd = open(filename)

    data = yaml.safe_load(fd)

    conf = {
      'services': data,
      'args': {}
    }

    for key in ['offset', 'topic', 'debug', 'groupid', 'input', 'decrypt']:
        val = getattr(options, key)
        if val != None:
            conf['args'][key] = val

    val = options.brokers
    if val != []:
        conf['args']['brokers'] = str.join(',', val)

    return conf
