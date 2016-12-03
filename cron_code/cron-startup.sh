#! /bin/bash
cd /home/vagrant/src/project
echo 'it works!' >> file.log
/usr/bin/python test_cron.py
source env/bin/activate && python cron_mail.py