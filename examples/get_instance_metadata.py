'''
Sample of usage of DottedDict. This example is a replacement for the get_instance_metadata call
that was in boto2, but not included in boto3. On an ec2 instance run the following to get:

In [2]: instance = get_instance_metadata()

In [3]: instance
Out[3]:
{u'account_id': u'957704715687',
 u'architecture': u'x86_64',
 u'availability_zone': u'us-east-1c',
 u'billing_products': None,
 u'devpay_product_codes': None,
 u'image_id': u'ami-6057e21a',
 u'instance_id': u'i-0b593c97b120320f3',
 u'instance_type': u't2.micro',
 u'kernel_id': None,
 u'marketplace_product_codes': None,
 u'pending_time': u'2017-11-10T06:23:15Z',
 u'private_ip': u'172.31.84.125',
 u'ramdisk_id': None,
 u'region': u'us-east-1',
 u'version': u'2017-09-30'}

In [4]: instance.availability_zone
Out[4]: u'us-east-1c'

In [5]: instance.region
Out[5]: u'us-east-1'
'''

import json
import string
import urllib3

from dotted_dict import DottedDict


def get_instance_metadata():
    '''
    Get the instance metadata and return an DottedDict with the values.
    '''
    http = urllib3.PoolManager()
    response = http.request(
        'GET',
        'http://169.254.169.254/latest/dynamic/instance-identity/document'
    )
    data = json.loads(response.data)
    return DottedDict({uncamel(k): v for k, v in data.items()})


def uncamel(name):
    '''
    Helper method to convert camel cased names to underscored.
    '''
    for char in string.uppercase:
        name = name.replace(char, '_{0}'.format(char.lower()))
    return name
