# -*- coding: utf-8 -*-
import sys
import os
import json
import pathlib
basepath = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(str(pathlib.Path(basepath, "modules")))
import config
from Kafka import KafkaConsumer
from KMS import AWSEncryptionSDK, KMS
from debug import errx, debug, trace

def kafka_consume():
    return KafkaConsumer(conf=conf).readMessageByPartitionOffsetAvro()

def aws_encryption_sdk_decrypt(CiphertextBlob):
    return AWSEncryptionSDK(conf=conf).decrypt_all(CiphertextBlob)

def aws_kms_decrypt(CiphertextBlob):
    return KMS(conf=conf).decrypt_all(CiphertextBlob)

def read_stdin():
    data = sys.stdin.read()
    return json.loads(data)

def main():
    input_type = conf['args']['input']
    decrypt_type = conf['args']['decrypt']

    reader = {
        'kafka': kafka_consume,
        'stdin': read_stdin
    }

    decryptor = {
        'aws_encryption_sdk': aws_encryption_sdk_decrypt,
        'aws_kms': aws_kms_decrypt
    }

    CiphertextBlob = reader[input_type]()
    decryptor[decrypt_type](CiphertextBlob)
    trace(CiphertextBlob, debug=True)

if __name__ == '__main__':
    conf = config.getConf(sys.argv[1:])
    exit(main())
