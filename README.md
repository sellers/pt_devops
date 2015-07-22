# pt_devops
This is the option 1 

deploy.py:  this is the management tool to launch and instance in EC2 

*.yaml :  these are jinja2 templated file that send userdata to EC2 (cloud-init)
  saltmaster.yaml will spin up an ec2 instance as a saltmaster
  option1.yaml is a three-tier architecture of flask+nginx+redis

setup_virtual.sh : this is a script that sets up the virtualenv for flask/python for 
the app - it's invocated by cloud-init and should be replaced with salt. 

pt.py: this is the app (flask)

Purpose:
To complete the following:
a) start an ec2 instance that runs a salt master (inf. setup)
b) start an ec2 instnace that runs a flask+nginx+redis solution
c) deploy a flask app that will test nginx+flask+redis
d) configure and start salt-minion on nginx+flask+redis instance - connecting to A above

Usage:
the Salt version is the first step toward embracing Saltstack,
and migrate away from cloud-init scripts for maintainging things.
cloud-init is awesome, but we may need to do management and auditing
and cloud-init is not as powerful as salt may be for that.  They completment
each other well from what I can gather. 

1) make sure you have a ec2 account to use (and a .boto or /etc/boto.cfg file setup with the info)
2) start the saltmaster: ./deploy.py -t saltmaster.yaml -n my-saltmaster  (you can optionally pass the AWS 
      keys to setup the .boto configs on the instance to use boto tools there with -a; see --help)
3) start the 3-tier app: ./deploy.py -t option1.yaml -n my-three-tier --saltmaster <internal ip of step2 host>
   tip: ./deploy.py --list all will show you the IP
4) visit http://<ip.of.step3.host> and see the flask app respond, click link and see redis data of visitor info
5) ssh to saltmaster instance and run  sudo salt-key -L  and note the minion
requseting access 


todo:
embrace saltstack for management and move some of the cloud-init manual steps to be salt commands
replace setup_virtual.sh script with more cloud-init/salty methods
determine how to auto-add saltkeys (cloud-init callback hook?)
better exception handling
tests
make debian package or setup.py out of the pt.py ?
