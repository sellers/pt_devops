# W. I. P.

# This is an active head/truck, so you should not use it

If you were directed here, you probably should look at the 'salt' branch.

# pt_devops
### This is the option 1 

* `deploy.py`:  this is the management tool to launch and instance in EC2 

* `*.yaml` :  these are jinja2 templated files that send userdata to EC2 (cloud-init)
   *  saltmaster.yaml will spin up an ec2 instance as a saltmaster
   *  option1.yaml is a three-tier architecture of flask+nginx+redis

* `setup_virtual.sh` : this is a script that sets up the virtualenv for flask/python for 
the app - it's invocated by cloud-init and should be replaced with salt.

* `pt.py`: this is the web app (flask), shows visitors

#### Requirements:
1. you need to have an AWS account to use
2. you need to have python with boto support enabled
3. you need to have /etc/boto.cfg or similar setup with key/secret

#### Purpose:
To complete the following:

1. start an ec2 instance that runs a salt master (inf. setup)
2. start an ec2 instnace that runs a flask+nginx+redis solution
3. deploy a flask app that will test nginx+flask+redis
4. configure and start salt-minion on nginx+flask+redis instance - connecting to A above
5. ssh keys for AWS ssh login (call it aws_pt-user for now)

#### Usage:
the Salt version is the first step toward embracing Saltstack,
and migrate away from cloud-init scripts for maintainging things.
cloud-init is awesome, but we may need to do management and auditing
and cloud-init is not as powerful as salt may be for that.  They complement
each other well from what I can gather. 

1. make sure you have a ec2 account to use (and a .boto or /etc/boto.cfg file setup with the info)
2. start the saltmaster: `./deploy.py -t saltmaster.yaml -n my-saltmaster`  (you can optionally pass the AWS 
      keys to setup the .boto configs on the instance to use boto tools there with -a; see --help)
3. start the 3-tier app: `./deploy.py -t option1.yaml -n my-three-tier --saltmaster <internal ip of step2 host>`
   _tip_: `./deploy.py --list all` will show you the IP
4. visit http://\<ip.of.step3.host\> and see the flask app respond, click link and see redis data of visitor info
5. ssh to saltmaster instance and run  `sudo salt-key -L` and note the minion
requesting access 
6. when done - you can use `./deploy.py --halt <instance id>` to halt instances


#### Todo:
* embrace saltstack for management and move some of the cloud-init manual steps to be salt commands
* replace setup_virtual.sh script with more cloud-init/salty methods
* determine how to auto-add saltkeys (cloud-init callback hook?)
* better exception handling
* tests
* make debian package or setup.py out of the pt.py ?
* make deploy.py more pythonic
* make cloud-init templates more generic
* take test pt-dev creds out of yaml files for .boto conf file create
* make keypair for SSH an argument to deploy.py

#### Notes:
* the deploy.py script will open up all TCP ports to your IP address, so if you
  are behind a dynamic IP (e.g. home ISP) you may want to be careful
* the AWS keys for this dev user are in github, so be careful of leaving this
  open on running instances
