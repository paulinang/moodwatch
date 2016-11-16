#! /bin/bash
cd /home/vagrant/src/project
echo 'it works!' >> file.log
/usr/bin/python test_cron.py
source env/bin/activate && python test_cron_db.py && python cron_mail_test.py