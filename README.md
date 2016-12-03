# MoodWatch
![alt-text](https://github.com/qwnpng/moodwatch/blob/master/screenshots/index.JPG)

MoodWatch helps users be mindful of their mental well-being. Users record numerical ratings of their moods for events and days. To keep users active, a daily email reminder is sent to those who have not logged that day. These records are displayed in an interactive chart to help users gain perspective by adjusting the time scale and viewing statistical. A special user account is available to healthcare professionals who provide patients with a second set of eyes. These accounts allow access to information users have agreed to share. Physicians get a high level view of their patient's logs, as well as the ability to prescribe medication and contact other professionals who share the same patient to discuss treatment.

## Technologies Used
PostgreSQL, SQLAlchemy, Python, Bcrypt, Pandas, Cron, Flask, Flask-Mail, Jinja, Javascript, Jquery, AJAX, Bootstrap, Chart.js

## Features
### Recording Moods and Medications Over Time
Users are able to keep track of their moods by numerically rating days and events. Physicians and their patients also get to look back at changes in their medications. User resources are stored in a PostgreSQL database which are mapped to Python classes using Flask-SQLAlchemy ORM.
![alt-text](https://github.com/qwnpng/moodwatch/blob/master/screenshots/basic_dashboard.JPG)

### Interactive Visualization Of Moods Over Time
Using the chart.js library, users' mood logs are visualized on a line chart. The Python Pandas library has been used to do statistical analysis such as moving average and standard deviation. The mood charts have interactive features such as changing the time window and visibility of different datasets. This is accomplished with a combination of AJAX requests for specific datasets and Jquery event listeners plus DOM element manipulation.
![alt-text](https://github.com/qwnpng/moodwatch/blob/master/screenshots/interactive_chart.gif)

### Automatic Email Reminders To Stay Active
Users are reminded to stay active in logging moods through daily email reminders. A cron job is scheduled to run in the later part of each day, running a Python script that queries the database for inactive users and send email reminders with the Flas-Mail extension. 