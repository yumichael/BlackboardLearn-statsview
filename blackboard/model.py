import re
import pandas as pd
import json
from io import StringIO
from datetime import datetime, timedelta
from pytz import timezone
from blackboard.utility import *

import flask
from blackboard import app
import blackboard.update as update

from flask_apscheduler import APScheduler

class Model(metaclass=Singleton):
    def __init__(self):
        self.update()

    def update(self):
        results = update.pull()
        self.create_with(*results)
        self.timestamp = datetime.now(tz=timezone("EST"))
        self.transform()

    def create_with(self, grades_raw, group_dict):

        # First, we set up the tables we can make out of grades_raw

        grades_data = pd.read_table(StringIO(grades_raw))
        raw_cols = grades_data.columns
        raw_cols = raw_cols.map(lambda x: x.replace(' ', '_').replace('#', '') if isinstance(x, str) else x)
        grades_data.columns = raw_cols

        student_info, grades_lookup = grades_data[raw_cols[:5]], grades_data[raw_cols[6:]]
        grade_cols = grades_lookup.columns
        # Clean the quiz/test names
        pts_re = re.compile(":_([0-9.]*)]")
        metric_names = grade_cols.map(lambda x: x[:x.index('_[')])
        points_possible = grade_cols.map(lambda x: pts_re.search(x).group(1))
        grades_lookup.columns = metric_names

        metric_info = pd.DataFrame([metric_names, points_possible]).T
        metric_info.columns = ['Metric_Name', 'Points_Possible']

        student_info.index = student_info.Student_ID
        grades_lookup.index = student_info.Student_ID
        metric_info.index = metric_info.Metric_Name

        students = student_info.assign(Full_Name = student_info.First_Name + ' ' + student_info.Last_Name)
        grades = grades_lookup

        # Next, we build more data structures out of group_dict

        student_names = {name: None for name in students.Full_Name}
        teaching_names = {}
        # We must assume that teaching names come up in more than one group
        for group, names in group_dict.items():
            #group = group.replace(' ', '_')
            for name in names:
                if name in student_names:
                    student_names[name] = group
                else:
                    if name not in teaching_names:
                        teaching_names[name] = []
                    teaching_names[name].append(group)
        leader_dict, head_dict = {}, {}
        for name, groups in teaching_names.items():
            if len(groups) > len(group_dict) / 2:
                head_dict[name] = groups
            else:
                leader_dict[name] = groups

        group_info = pd.DataFrame(sorted(group_dict.keys()), columns=["Group_Name"])
        group_info = group_info.assign(Leader_Name="")
        tf = group_info
        for leader, groups in leader_dict.items():
            for group in groups:
                tf.Leader_Name[tf.Group_Name == group] = leader

        group_info.index = group_info.Group_Name
        groups = group_info.assign(Standard=group_info.Leader_Name)
        students = students.assign(Group_Name = students.Full_Name.map(lambda x: student_names[x]))
        metrics = metric_info

        self.data = O(students=students, grades=grades, groups=groups, metrics=metrics)

    def transform(self):
        d = self.data
        table = d.students.join(d.grades)
        table = table.set_index('Group_Name')
        table = table[['Test_1', 'Test_2'] + ['Quiz_' + str(n) for n in range(1, 10)]].stack()
        table = table.groupby(identity).agg(sorted).unstack()
        self.table = table
        
        output = table.to_dict()
        for metric in list(output):
            grades = output.pop(metric)
            for group in list(grades):
                grades['Tut ' + group[-2:]] = grades.pop(group)
            output[metric.replace('_', ' ')] = grades
        self.output = output

        points = d.metrics["Points_Possible"].to_dict()
        for metric in list(points):
            points[metric.replace('_', ' ')] = points.pop(metric)
        info = {}
        info['total_points'] = points
        self.info = info

        self.json_output = json.dumps(self.output)
        self.json_info = json.dumps(self.info)

# I have no idea how the scheduler below works but it works
# It's copied right from the examples in Flask-APScheduler

class Config(object):
    JOBS = [
        {
            'id': 'keep_fresh',
            'func': 'blackboard.model:keep_fresh',
            'args': (),
            'trigger': 'interval',
            'hours': 12
        }
    ]

    SCHEDULER_VIEWS_ENABLED = True

def keep_fresh():
    Model().update()

app.config.from_object(Config())

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
