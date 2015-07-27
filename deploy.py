#!/usr/bin/env python
'''
script to manage instances for testing using libcloud
written by Chris G. Sellers - July 2015
adopted from similar tool written using boto
--
purpose is to be a deployment mgt tool for
starting and stoping AWS instances for testing
or management of infrastructures
usage is as defined --help
'''

from boto.ec2.connection import EC2Connection
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from jinja2 import Environment as JinjaEnv
from jinja2 import FileSystemLoader as JinjaLoad
import argparse
import ConfigParser
import time
import sys
import json
try:
    from urllib2 import (urlopen,
                         URLError,
                         Request)
except ImportError:
    from urllib.request import (urlopen,
                                Request)
    from urllib.error import URLError



class Userdata(object):
    '''
    create the userdata from jinja template
    '''

    def __init__(self, hostname, awskeys, templ_file,
                 saltmaster):
        '''
        user data
        add value fast so assume connection/region
        '''
        self.hostname = hostname
        self.templ_file = templ_file
        self.jinjaload = JinjaLoad(searchpath=".")
        self.jinjaenv = JinjaEnv(loader=self.jinjaload)
        self.awskeys = awskeys
        self.saltmaster = saltmaster


    def templ(self):
        '''
        read in the template and parse variables
        '''
        template_values = {
            'hostname' : self.hostname,
            'aws_key' : self.awskeys.split(':')[0],
            'aws_secret' : self.awskeys.split(':')[1],
            'saltmaster' : self.saltmaster,
        }

        template = self.jinjaenv.get_template(self.templ_file)
        userdata = template.render(template_values)
        return(userdata)

class Launch(object):
    '''
    launch an instance
    '''

    def __init__(self, userdata, salt_master=None, hostname='missing'):
        '''
        start instance
        assume AWS stuff configured
        '''

        theurl = urlopen(Request('http://api.ipify.org?format=json'), timeout=30)
        resp = json.loads(str(theurl.read().decode('utf-8')))

        self.userdata = userdata
        self.ami_id = 'ami-5189a661'  # ami-5189a661 = ubuntu.14.04LTS.HVM
        self.key_pair_name = 'aws_pt-user'
        self.instance_type = 't2.micro'
        self.ip = resp['ip'] or None
        self.salt_master = salt_master
        self.hostname = hostname
        self.aws_key = None
        self.aws_secret = None
        self.aws_region = None

    def config(self, cfile=None):
        '''
        read in configuration for connection from file
        like a .boto file or similar
        '''
        if file is not None:
            config_file = ConfigParser.RawConfigParser()
            try:
                config_file.read(cfile)
            except IOError as err:
                print('Error reading config {}:{}'.format(
                    cfile, err))
            self.aws_key = config_file.get('Credentials', 'aws_access_key_id')
            self.aws_secret = config_file.get('Credentials', 'aws_secret_access_key')
            self.aws_region = config_file.get('Boto', 'ec2_region_name')



    def addsecurity(self):
        '''
        set security group
        '''

        conn = EC2Connection(self.aws_key, self.aws_secret, region=self.aws_region)
        try:
            new_group = conn.get_all_security_groups(
                groupnames=['{}'.format(self.ip)])[0]
            print('security group {} already present'.format(self.ip))
        except Exception as err:
            # we poorly assume the err is due to absense not true err :(
            print('hi - new security group needed')
            time.sleep(16)  # wait for instance to have ID/state, should poll
            new_group = conn.create_security_group(
                self.ip,
                'Access from my IP'
                )
            cidr_ip = '{}/32'.format(self.ip)
            conn.authorize_security_group(
                group_name=self.ip,
                ip_protocol='tcp',
                from_port='0',
                to_port='65535',
                cidr_ip=cidr_ip)
        if self.salt_master is not None:
            print('adding salt security group {}'.format(new_group.id))
            time.sleep(4)
            try:
                conn.authorize_security_group(
                    ip_protocol='tcp',
                    from_port='4505',
                    to_port='4506',
                    group_id=new_group.id,
                    src_security_group_group_id=new_group.id)
                print('added')
            except Exception as err:
                print(' * informational note: {}'.format(err))
        return

    def list(self, inst_id=None):
        '''
        get status of instances
        '''

        try:
            ec2_conn = get_driver(Provider.EC2)(self.aws_key, self.aws_secret,
                    region=self.aws_region)
            ###ec2 = EC2Connection()
            if inst_id is None or inst_id == 'all':
                ###res = ec2.get_all_instances()
                instances = ec2_conn.list_nodes()
            else:
                ###res = ec2.get_all_instances(instance_ids=inst_id)
                instances = ec2_conn.list_nodes(ex_node_ids=list(inst_id))

            ###instances = [i for r in res for i in r.instances]
            for inst in instances:
                ###print(' {} : {} : {}|{} : {}'.format(inst.id,
                ###                                  inst._state,
                ###                                  inst.ip_address,
                ###                                  inst.private_ip_address,
                ###                                  inst.tags))
                print(' {} : {} : {}|{} : {}'.format(inst.id,
                                                     inst.extra['status'],
                                                     inst.public_ips,
                                                     inst.private_ips,
                                                     inst.extra['tags']))
        except Exception as err:
            print('issue: {}'.format(err))
        return


    def halt(self, inst_ids):
        '''
        halt the instance you started
        '''
        for inst_id in inst_ids:
            try:
                print('starting halt of {}...'.format(inst_id))
                ec2 = EC2Connection()
                inst = ec2.get_all_instances(instance_ids=inst_id)[0].instances[0]
                res = ec2.terminate_instances(instance_ids=inst_id)
                print('status: {}'.format(inst._state.name))
                while not inst._state.name == 'terminated':
                    inst = ec2.get_all_instances(instance_ids=inst_id)[0].instances[0]
                    time.sleep(3)
                    print('  .. {}{}'.format(inst._state.name, '..')).rstrip("\n")
                print('id {} {} done'.format(inst.id, inst.state_reason))
            except Exception as err:
                print('halt error {}'.format(err))
            try:
                time.sleep(5)  # try to allow coalesce
                ec2.delete_security_group(self.ip)
            except Exception as err:
                print('err rm sec group {}'.format(err))
        return

    def launch(self):
        '''
        launch an instance in eC2
        '''
        try:
            ec2 = EC2Connection()
            res = ec2.run_instances(self.ami_id,
                                    instance_type=self.instance_type,
                                    key_name=self.key_pair_name,
                                    security_groups=['{}'.format(self.ip)],
                                    user_data=self.userdata)

            instance = res.instances[0]
            sys.stdout.write('launching instance ')
            while not instance.update() == 'running':
                time.sleep(3)
                sys.stdout.write('. ')
                sys.stdout.flush()
            print('\nid {} launched ssh -i ~/.ssh/{}.rsa ubuntu@{}'
                  .format(instance,
                          self.key_pair_name,
                          instance.public_dns_name))
        except Exception as err:
            print('error launching: {}'.format(err))
        try:
            ec2.create_tags([instance.id], {"Name": self.hostname})
        except Exception as err:
            print('error setting instance tag name {}'.format(err))
        return()


def main():
    '''
    lets do some hdp on aws
    '''
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', '--config',
                            help='boto/libcloud config data',
                            default=None)
        parser.add_argument('-t', '--templatefile',
                            help='Jinja2 userdata template file')
        parser.add_argument('-n', '--hostname',
                            help='what hostname to set')
        parser.add_argument('--halt',
                            help='halt/terminate instance ID',
                            nargs='+')
        parser.add_argument('--list',
                            help='list instance ID (or all) ',
                            default=None)
        parser.add_argument('-a', '--awskeys',
                            help='AWS access and secret key : separated',
                            default=':')
        parser.add_argument('--saltmaster',
                            type=str,
                            default=None,
                            help='saltstack master (if desired)',
                            )
        args = parser.parse_args()
        if len(sys.argv) < 2:
            parser.print_usage()
            sys.exit(1)
    except argparse.ArgumentError as arge:
        print('error with argparser {}'.format(arge))
        sys.exit(1)

    if args.list:
        my_inst = Launch('')
        my_inst.config(args.config)
        my_inst.list(args.list)
        sys.exit(0)
    if args.halt:
        my_inst = Launch('')
        my_inst.halt(args.halt)
        sys.exit(0)
    my_userdata = Userdata(args.hostname,
                           args.awskeys,
                           args.templatefile,
                           args.saltmaster)
    my_data = my_userdata.templ()
    my_inst = Launch(my_data, args.saltmaster, args.hostname)
    my_inst.addsecurity()
    my_inst.launch()


if __name__ == '__main__':
    main()
