from aws import ec2
from aws import route53
from aws import dynamo

from datetime import datetime

import logging as log
import time
import os

log.basicConfig(format='%(asctime)s %(levelname)s | %(message)s', level=log.DEBUG)

log.info('Loading function ' + datetime.now().time().isoformat())
public_prefix = os.environ['PUBLIC_PREFIX'] if 'PUBLIC_PREFIX' in os.environ else "p-"


def sleep():
    time_to_sleep = os.environ['TIME_TO_SLEEP'] if 'TIME_TO_SLEEP' in os.environ else 2
    time_to_sleep = time_to_sleep if time_to_sleep is not "" else 2
    log.info('Sleeping for {} seconds'.format(time_to_sleep))
    time.sleep(int(time_to_sleep))
    log.info("I'm awake")


def handler(event, context):
    log.debug(event)
    try:
        instance = ec2.Instance(event)
    except KeyError as e:
        log.error("I couldn't initiate the instance :(")
        log.error("Error is related to: {}".format(e))
        log.error("ps. Is the instance UP? Does it exist?")
        exit(127)

    table = dynamo.setup()
    log.info('Got the table {}'.format(table))

    zone_name = route53.get_zone_nome(instance.tags)

    use_public_ip = os.environ['PUBLIC'] if 'PUBLIC' in os.environ else False

    if instance.get_state() == 'running':
        if use_public_ip:
            public_ip = instance.public_ip
            private_ip = instance.private_ip
        else:
            private_ip = instance.private_ip

        if instance.belong_to_asg():
            dns_name = route53.get_host_name(instance.tags, zone_name, private_ip)
        else:
            dns_name = route53.get_host_name(instance.tags, zone_name, False).lower()
        if use_public_ip:
            p_dns_name = route53.get_host_name(instance.tags, zone_name, public_ip).lower()

        log.info("Zone\t{}".format(zone_name))
        log.info("Name\t{}".format(dns_name))
        log.info("Adding records")
        dynamo.add_record(table, instance.ec2)
        try:
            route53.create_resource_record(dns_name, zone_name, 'A', private_ip)
            if use_public_ip:
                if instance.belong_to_asg():
                    route53.create_resource_record(p_dns_name, zone_name, 'A', public_ip)
                else:
                    route53.create_resource_record(public_prefix + dns_name, zone_name, 'A', public_ip)
        except BaseException as e:
            log.error("I couldn't add the records, something went wrong :(")
            log.error(e)
    else:
        log.info("Waiting for the instance to shutdown")
        instance.wait_for_instance_to_shutdown()
        log.info("Removing records")
        try:
            d_instance = dynamo.get_record(table, instance.id)
            d_details = d_instance['Item']['InstanceAttributes']['Instances'][0]
            d_instance_tags = d_details['Tags']
            d_private_address = d_details['PrivateIpAddress']
            d_public_address = d_details['PublicIpAddress']
        except Exception:
            log.error('I could not find any DynamoDB record for the instance_id: {}'.format(instance.id))
            exit(127)
        if ec2.Instance.get_name_tag(instance.tags) == ec2.Instance.get_name_tag(d_instance_tags):
            log.info('Found matching Name tags, let us delete/remove it now :)')
            if instance.belong_to_asg():
                dns_name = route53.get_host_name(instance.tags, zone_name, d_private_address)
            else:
                dns_name = route53.get_host_name(instance.tags, zone_name, False).lower()
            if use_public_ip:
                p_dns_name = route53.get_host_name(instance.tags, zone_name, d_public_address).lower()
            try:
                route53.delete_resource_record(dns_name, zone_name, 'A', d_private_address)
                if d_public_address:
                    if instance.belong_to_asg():
                        route53.delete_resource_record(p_dns_name, zone_name, 'A', d_public_address)
                    else:
                        route53.delete_resource_record(public_prefix + dns_name, zone_name, 'A', d_public_address)
                dynamo.remove_record(table, instance.id)
            except BaseException as e:
                log.error("Something went wrong\n{}".format(e))
        else:
            log.error('I could not find any matching tag for Name key, stopping it now ):')


if __name__ == '__main__':
    x = {
        u'account': u'739171219021',
        u'region': u'us-east-1',
        u'detail':
            {u'state': u'shutting-down', u'instance-id': u'i-0c9abe819c87f5271'},
        u'detail-type': u'EC2 Instance State-change Notification',
        u'source': u'aws.ec2',
        u'version': u'0',
        u'time': u'2018-09-27T17:45:50Z',
        u'id': u'82ee8e79-f046-684f-e528-0821cdd5c303',
        u'resources':
            [u'arn:aws:ec2:sa-east-1:739171219021:instance/i-07b5b76738fdb0627']
    }
    handler(x, True)
log.info('End ' + datetime.now().time().isoformat())