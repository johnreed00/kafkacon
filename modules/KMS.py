# -*- coding: utf-8 -*-
import boto3
import base64
import aws_encryption_sdk
from aws_encryption_sdk.key_providers.kms import KMSMasterKey
from botocore.exceptions import ClientError, ParamValidationError, EndpointConnectionError, ConnectTimeoutError
from debug import errx, debug, trace

class aws(object):
    """aws boto3 class"""
    name = "aws"
    region = None

    conf = {
        'EncryptionAlgorithm': 'SYMMETRIC_DEFAULT'
    }

    ErrHandler = {}

    def __init__(self, conf=None):
        self.name = self.getname()
        self.getconf(conf)
        self.client = self.connect()
        
    def getconf(self, conf):
        pass

    def connect(self):
        pass

    def getname(self):
        return self.__class__.__name__

    def botoHandler(self, call=None, key=None, **kwargs):
        items = {}
        data = self.boto_method_handler(call=call, **kwargs)
        try:
            items = data[key]
        except:
            pass

        return { key: items }

    def boto_method_handler(self, call=None, **kwargs):
        data = {}

        trace({
            'timestamp': time.time(),
            'call': call
        })

        try:
            data = call(**kwargs)
        except ConnectTimeoutError as error:
            debug(level=1, service=self.name, error=error)

        except EndpointConnectionError as error:
            debug(level=1, service=self.name, error=error)

        except ClientError as error:
            try:
                errcode = error.response['Error']['Code']
                data['ErrorData'] = self.ErrHandler.get(errcode, errx)(error)
            except:
                debug(level=1, service=self.name, region=self.region)
                raise

        except (ValueError, TypeError, ParamValidationError) as error:
            debug(level=1, service=self.name, region=self.region)
            raise

        try:
            del data['ResponseMetadata']
        except:
            pass

        return data

class KMS(aws):
    """KMS boto3 class"""
    name = "KMS"
    service = "kms"

    def connect(self):
        try:
            self.region = self.conf['region']
        except:
            errx('Option region is not defined')

        return boto3.client(self.service, region_name=self.region)

    def getconf(self, conf):
        try:
            self.conf.update(conf['services'][self.name])
        except:
            errx("No KMS configuration found")

        trace(self.conf)

    def decode(self, data):
        CiphertextBlob = data
        if type(data).__name__ != 'bytes':
            CiphertextBlob = base64.b64decode(data)

        return CiphertextBlob

    def decrypt_all(self, iterable):
        if isinstance(iterable, dict):
            for key, value in iterable.items():
                if not (isinstance(value, dict) or isinstance(value, list)):
                    if type(value).__name__ == 'bytes':
                        iterable[key] = self.decrypt(value)
                else:
                    self.decrypt_all(value)
        elif isinstance(iterable, list):
            for value in iterable:
                self.decrypt_all(value)

    def decrypt(self, data):
        try:
            KeyId = self.conf['KeyId']
        except:
            errx("No KeyId found in configuration file")

        return self.botoHandler(
            call=self.client.decrypt, key='Plaintext',
            CiphertextBlob=self.decode(data), KeyId=KeyId,
            EncryptionAlgorithm=self.conf['EncryptionAlgorithm']
        )

class AWSEncryptionSDK(KMS):
    """AWSEncryptionSDK boto3 class"""
    name = "AWSEncryptionSDK"

    KeyId = None
    EncryptionContext = None

    def getconf(self, conf):
        try:
            self.conf.update(conf['services'][self.name])
        except:
            errx("No AWSEncryptionSDK configuration found")

        try:
            self.KeyId = self.conf['KeyId']
            self.EncryptionContext = self.conf['encryption_context']
        except:
            errx("No KeyId/encryption_context found in configuration file")

        trace(self.conf)

    def connect(self):
        pass

    def encrypt(self, data):
        master_key = KMSMasterKey(key_id=self.KeyId)
        ciphertext, _encrypt_header = aws_encryption_sdk.encrypt(
            source=data, encryption_context=self.EncryptionContext, key_provider=master_key
        )

        assert ciphertext != data
        return ciphertext

    def decrypt(self, data):
        master_key = KMSMasterKey(key_id=self.KeyId)
        decrypted, decrypt_header = aws_encryption_sdk.decrypt(source=self.decode(data), key_provider=master_key)
        assert set(self.EncryptionContext.items()) <= set(decrypt_header.encryption_context.items())
        return decrypted
