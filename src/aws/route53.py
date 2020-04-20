import boto3
import logging as logger
import uuid
import re
import os

logger.basicConfig(format='%(asctime)s %(levelname)s | %(message)s', level=logger.INFO)

route53 = boto3.client('route53')

default = {"zone_name": os.environ['ZONE_NAME'], "zone_id": os.environ['ZONE_ID']}
octetos = 4
if "OCTETOS" in os.environ:
    try:
        octetos = int(os.environ['OCTETOS'])
        if 2 < octetos > 3:
            logger.error('Octetos must be between 2 and 3')
            exit(1)
    except BaseException as e:
        logger.error('Octetos is not a number: ' + e)
        exit(1)


def get_zone_nome(tags: map):
    for tag in tags:
        if 'ZONE' in tag.get('Key', {}).lstrip().upper():
            logger.info("Nice, I've found a valid zone")
            return tag.get('Value')
    logger.info("Using pre-defined ZONE: {}".format(default['zone_name']))
    return default['zone_name']


def get_host_name(tags: map, zone_name: str, private_ip: str):
    for tag in tags:
        if 'name' == tag.get('Key').lower():
            if private_ip and octetos != 0:
                return tag.get('Value').strip('-') + "-" + "-".join(private_ip.split('.')[-octetos:]) + "." + zone_name
            else:
                return tag.get('Value').strip('-') + "." + zone_name


def create_reverse_lookup_zone(vpc_id: str, reversed_domain_prefix: str, region: str):
    """Creates the reverse lookup zone."""
    print('Creating reverse lookup zone %s' % reversed_domain_prefix + 'in.addr.arpa.')
    route53.create_hosted_zone(
        Name=reversed_domain_prefix + 'in-addr.arpa.',
        VPC={
            'VPCRegion': region,
            'VPCId': vpc_id
        },
        CallerReference=str(uuid.uuid1()),
        HostedZoneConfig={
            'Comment': 'Updated by Lambda DDNS',
        },
    )


def is_dns_hostnames_enabled(vpc: str):
    dns_hostnames_enabled = vpc.describe_attribute(
        DryRun=False,
        Attribute='enableDnsHostnames'
    )
    return dns_hostnames_enabled['EnableDnsHostnames']['Value']


def is_dns_support_enabled(vpc: str):
    dns_support_enabled = vpc.describe_attribute(
        DryRun=False,
        Attribute='enableDnsSupport'
    )
    return dns_support_enabled['EnableDnsSupport']['Value']


def get_hosted_zone_properties(zone_id: str):
    hosted_zone_properties = route53.get_hosted_zone(Id=zone_id)
    hosted_zone_properties.pop('ResponseMetadata')
    return hosted_zone_properties


def associate_zone(hosted_zone_id: str, region, vpc_id):
    """Associates private hosted zone with VPC"""
    route53.associate_vpc_with_hosted_zone(
        HostedZoneId=hosted_zone_id,
        VPC={
            'VPCRegion': region,
            'VPCId': vpc_id
        },
        Comment='Updated by Lambda DDNS'
    )


def get_zone_id(zone_name: str):
    """Given a zone_name it returns the zone_id."""
    if zone_name[-1] != '.':
        zone_name = zone_name + '.'
    hosted_zones = route53.list_hosted_zones()
    x = filter(lambda record: record['Name'] == zone_name, hosted_zones['HostedZones'])
    try:
        zone_id_long = x[0]['Id']
        zone_id = str.split(str(zone_id_long), '/')[2]
        return zone_id
    except:
        return default['zone_id']


def create_resource_record(hostname: str, hosted_zone_name: str, type: str, value: 'ip address'):
    """Give some parameters it will create/update the @type record"""
    logger.info("Updating {} record {} in zone {}".format(type, hostname, hosted_zone_name))
    if hostname[-1] != '.':
        hostname = hostname + '.'
    route53.change_resource_record_sets(
        HostedZoneId=get_zone_id(hosted_zone_name),
        ChangeBatch={
            "Comment": "Updated by Lambda DDNS",
            "Changes": [
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": hostname,
                        "Type": type,
                        "TTL": 60,
                        "ResourceRecords": [
                            {
                                "Value": value
                            },
                        ]
                    }
                },
            ]
        }
    )


def delete_resource_record(hostname: str, hosted_zone_name: str, type: str, value: 'ip address'):
    """Give some parameters it will delete the @type record"""
    logger.info("Deleting {} record {} in zone {}".format(type, hostname, hosted_zone_name))
    if hostname[-1] != '.':
        hostname = hostname + '.'
    route53.change_resource_record_sets(
        HostedZoneId=get_zone_id(hosted_zone_name),
        ChangeBatch={
            "Comment": "Updated by Lambda DDNS",
            "Changes": [
                {
                    "Action": "DELETE",
                    "ResourceRecordSet": {
                        "Name": hostname,
                        "Type": type,
                        "TTL": 60,
                        "ResourceRecords": [
                            {
                                "Value": value
                            },
                        ]
                    }
                },
            ]
        }
    )
    logger.info('Deleted successfuly ;)')


def is_valid_hostname(hostname: str):
    """Check if hosntame is valid."""
    if hostname is None or len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1]
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))
