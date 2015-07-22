 #!/bin/bash
 # initial hack to get virutalenv setup - ripe for replacement
 cd /home/ubuntu/pt
 virtualenv env
 source env/bin/activate
 pip install flask
 pip install Flask-And-Redis
