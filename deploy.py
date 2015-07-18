#!/usr/bin/env python
'''
script to deploy AWS instances for testing
written by Chris G. Sellers - June 2015
adapted for use with PT
--
purpose is to be a deployment mgt tool for
starting and stoping AWS instances for testing
or management of infrastructures
usage is as defined --help
'''

from boto.ec2.connection import EC2Connection
from jinja2 import Environment as JinjaEnv
from jinja2 import FileSystemLoader as JinjaLoad
import argparse
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

    def __init__(self, hostname, awskeys, templ_file):
        '''
        user data
        add value fast so assume connection/region
        '''
        self.hostname = hostname
        self.templ_file = templ_file
        self.jinjaload = JinjaLoad(searchpath=".")
        self.jinjaenv = JinjaEnv(loader=self.jinjaload)
        self.awskeys = awskeys


    def templ(self):
        '''
        read in the template and parse variables
        '''
        template_values = {
            'hostname' : self.hostname,
            'aws_key' : self.awskeys.split(':')[0],
            'aws_secret' : self.awskeys.split(':')[1],
        }

        template = self.jinjaenv.get_template(self.templ_file)
        userdata = template.render(template_values)
        return(userdata)

class Launch(object):
    '''
    launch an instance
    '''

    def __init__(self, userdata):
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


    def addsecurity(self):
        '''
        set security group
        '''

        conn = EC2Connection()
        try:
            conn.get_all_security_groups(groupnames=['{}'.format(self.ip)])
            return
        except Exception as err:
            print('hi')
        conn.create_security_group(
            self.ip,
            'Access from my IP'
            )
        cidr_ip='{}/32'.format(self.ip)
        conn.authorize_security_group(
                group_name=self.ip,
                ip_protocol='tcp',
                from_port='0',
                to_port='65535',
                cidr_ip=cidr_ip)

    def list(self, inst_id=None):
        '''
        get status of instances
        '''

        try:
            ec2 = EC2Connection()
            if inst_id is None or inst_id == 'all':
                res = ec2.get_all_instances()
            else:
                res = ec2.get_all_instances(instance_ids=inst_id)

            instances = [i for r in res for i in r.instances]
            for inst in instances:
                print(' {} : {} : {}'.format(inst.id, inst._state, inst.ip_address))
        except Exception as err:
            print('issue: {}'.format(err))
        return


    def halt(self, inst_id):
        '''
        halt the instance you started
        '''
        try:
            ec2 = EC2Connection()
            inst = ec2.get_all_instances(instance_ids=inst_id)[0].instances[0]
            res = ec2.terminate_instances(instance_ids=inst_id)
            print inst._state.name
            while not inst._state.name == 'terminated':
                time.sleep(4)
                print('{}{}'.format(inst.__state.name,'..')).rstrip("\n\r")
            print('id {} {} done'.format(inst.id, inst.state_reason))
        except Exception as err:
            print('error {}'.format(err))
        try:
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
            print('launching instance ')
            while not instance.update() == 'running':
                time.sleep(3)
                print('{}'.rstrip('\r\n').format('..')).rstrip('\n\r'),
            print('id {} launched ssh -i ~/.ssh/{}.rsa ubuntu@{}'
                  .format(instance,
                          self.key_pair_name,
                          instance.public_dns_name))
        except Exception as err:
            security_groups=['your-security-group-here']
            print('error launching: {}'.format(err))
        return()


def main():
    '''
    lets do some hdp on aws
    '''
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-t', '--templatefile',
                            help='Jinja2 userdata template file')
        parser.add_argument('-n', '--hostname',
                            help='what hostname to set')
        parser.add_argument('--halt',
                            help='halt/terminate instance ID')
        parser.add_argument('--list',
                            help='list instance ID (or all) ',
                            default=None)
        parser.add_argument('-a', '--awskeys',
                            help='AWS access and secret key : separated',
                            default=':')
        args = parser.parse_args()
        if len(sys.argv) < 2:
            parser.print_usage()
            sys.exit(1)
    except argparse.ArgumentError as arge:
        print('error with argparser {}'.format(arge))
        sys.exit(1)

    if args.list:
        my_inst = Launch('')
        my_inst.list(args.list)
        sys.exit(0)
    if args.halt:
        my_inst = Launch('')
        my_inst.halt(args.halt)
        sys.exit(0)
    my_userdata = Userdata(args.hostname, args.awskeys, args.templatefile)
    my_data = my_userdata.templ()
    my_inst = Launch(my_data)
    my_inst.addsecurity()
    my_inst.launch()


if __name__ == '__main__':
    main()
