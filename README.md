# VFS Appointment Bot
This project takes VFS appointments automatically based on given information in JSON file.
For solving the project you need to have a 2Captcha account.
Google key for google reCaptcha solving
Valid VFS credentials 


## Install guide

    Install these packages: 
    - python3
    - python3-pip
    - google-chrome-stable

    Install requirements:
        pip3 install -r requirements.txt


## Daemonize the application

    Make this file:
        /lib/systemd/system/vfsbot.service
    Put this text into it:
         [Unit]
         Description=VFSBot Service
         After=multi-user.target
        
         [Service]
         Type=idle
         ExecStart=/usr/bin/python3 /{{YOUR PROJECT PATH}}/vfsbot.py > /root/output.log &
        
         [Install]
         WantedBy=multi-user.target

    Run these commands:
        systemctl enable vfsbot
        systemctl start vfsbot

## Maintain Project

    Restarting application:
        to keep logout and login in intervalls, you shoudl restart it 5 times a day
        make a cronjob with:
            crontab -e
            0 */5 * * * systemctl restart vfsbot
            
## Variables and Settings
    Visa Types
        
        2394  Family Reunification
        3617 requency of course in educational or vocational training establishment
        2395 ndependent Professional Activity or Migrants Entrepreneurs
        2401 Medical Treatment
        3615 Residence visas for subordinate work
        3616 retired people, religious and people living on income
        2404 Seasonal Work Purposes (More Than 90 Days And Until 9 Months Per Year)
        3179 Temporary stay visa for research purposes and residence visas for teaching activities oed rofesns
        3178 Temporary stay visas and residence visas for study purposes
        3180 Temporary stay visas for temporary transfer of staff within corporations and residence vndent ctivities or Stup visas
    
