import base64
import boto3

kms = boto3.client('kms')


def base64_d(text):
    return base64.b64decode(text)


def decrypt(text):
    return kms.decrypt(CiphertextBlob=base64_d(text))['Plaintext'].decode('utf8')


