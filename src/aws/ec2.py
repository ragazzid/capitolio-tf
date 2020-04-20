import boto3
import time
import re
import logging as logger

ec2 = boto3.resource('ec2')
compute = boto3.client('ec2')

logger.basicConfig(format='%(asctime)s %(levelname)s | %(message)s', level=logger.INFO)


class Instance:
    def __init__(self, event):
        self.source = event['source']
        self.account = event['account']
        self.version = event['version']
        self.time = event['time']
        self.id = event['detail']['instance-id']
        self.region = event['region']
        self.details = event['detail']
        self.ec2 = self.get_ec2_state(self.id)
        self.tags = self.ec2['Instances'][0]['Tags']
        if self.details['state'] == 'running':
            self.private_ip = self.ec2['Instances'][0]['PrivateIpAddress']
            self.public_ip = self.ec2['Instances'][0]['PublicIpAddress'] if 'PublicIpAddress' in self.ec2['Instances'][0] else ''
            self.private_dns_name = self.ec2['Instances'][0]['PrivateDnsName']
            self.private_host_name = self.private_dns_name.split('.')[0]
            self.public = self.get_public_data()
            self.subnet_id = self.ec2['Instances'][0]['SubnetId']
            self.subnet = ec2.Subnet(self.subnet_id)
            self.cidr_block = self.subnet.cidr_block
            self.subnet_mask = int(self.cidr_block.split('/')[-1])
            self.reversed_ip_address = reverse_list(self.private_ip)
            self.reversed_domain_prefix = reverse_list(get_reversed_domain_prefix(self.subnet_mask, self.private_ip))
            self.vpc_id = self.ec2['Instances'][0]['VpcId']
            self.vpc = ec2.Vpc(self.vpc_id)

    def should_i_run_it(self):
        for tag in self.tags:
            if 'name' == tag.get('Key').lower():
                logger.info("Nice, I've found the tag Name, continuing")
                return True
        logger.error("The tag Name wasn't found :(")
        return False

    def belong_to_asg(self):
        for tag in self.tags:
            if 'aws:autoscaling:groupName' in tag.get('Key') or 'spotinst:aws:ec2:group:name' in tag.get('Key'):
                logger.info("Ow, this instance belongs to an ASG/SpotInst")
                return True
        logger.info("Instance does not belong to an ASG")
        return False

    def get_id(self):
        return self.id

    def get_state(self):
        return self.details['state']

    def get_public_data(self):
        res = {}
        try:
            res["public_ip"] = self.ec2['Instances'][0]['PublicIpAddress']
            res["public_dns_name"] = self.ec2['Instances'][0]['PublicDnsName']
            res["public_host_name"] = self.public_dns_name.split('.')[0]
            return res
        except BaseException as e:
            logger.warning('Instance has no public IP or host name {}'.format(e))

    def wait_for_instance_to_shutdown(self):
        time_to_sleep = 60
        while True:
            r = compute.describe_instance_status(InstanceIds=[self.id])
            if len(r['InstanceStatuses']) > 0 and r['InstanceStatuses'][0]['InstanceState']['Name'] == 'shutting-down':
                logger.info("Instance is still running, let us wait a little bit")
                logger.info("Sleeping for {} seconds".format(time_to_sleep))
                time.sleep(time_to_sleep)
                time_to_sleep += 60
            else:
                break
        return True

    @staticmethod
    def get_ec2_state(instance_id: 'EC2 InstanceID'):
        # Remove response metadata from the response
        ec2_data = compute.describe_instances(InstanceIds=[instance_id])
        ec2_data.pop('ResponseMetadata')
        ec2_data = remove_empty_from_dict(ec2_data)
        ec2_data = ec2_data['Reservations'][0]
        if 'Tags' in ec2_data['Instances'][0]:
            return ec2_data
        else:
            logger.error("The tag Name is required for this script to run")
            raise Exception("Failed to run - Missing tag Name - Check the instance tags")


    @staticmethod
    def get_name_tag(tags: map):
        for tag in tags:
            if 'NAME' in tag.get('Key', {}).lstrip().upper():
                return True
        return False


def remove_empty_from_dict(d: dict):
    """Removes empty keys from dictionary"""
    if type(d) is dict:
        return dict((k, remove_empty_from_dict(v)) for k, v in d.items() if v and remove_empty_from_dict(v))
    elif type(d) is list:
        return [remove_empty_from_dict(v) for v in d if v and remove_empty_from_dict(v)]
    else:
        return d


def reverse_list(ip_address: str):
    """Reverses the order of the instance's IP address and helps construct the reverse lookup zone name."""
    if (re.search('\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', ip_address)) \
            or (re.search('\d{1,3}.\d{1,3}.\d{1,3}\.', ip_address)) \
            or (re.search('\d{1,3}.\d{1,3}\.', ip_address)) \
            or (re.search('\d{1,3}\.', ip_address)):
        ip_address = str.split(str(ip_address), '.')
        ip_address.reverse()
        reversed_list = ''
        for item in ip_address:
            reversed_list = reversed_list + item + '.'
        return reversed_list
    else:
        print("Not a valid ip")
        exit()


def get_reversed_domain_prefix(subnet_mask: str, private_ip: str):
    """Uses the mask to get the zone prefix for the reverse lookup zone"""
    if 32 >= subnet_mask >= 24:
        third_octet = re.search('\d{1,3}.\d{1,3}.\d{1,3}.', private_ip)
        return third_octet.group(0)
    elif 24 > subnet_mask >= 16:
        second_octet = re.search('\d{1,3}.\d{1,3}.', private_ip)
        return second_octet.group(0)
    else:
        first_octet = re.search('\d{1,3}.', private_ip)
        return first_octet.group(0)