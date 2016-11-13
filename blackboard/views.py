"""
Routes and views for the flask application.
"""

import os
from datetime import datetime
from flask import render_template
from blackboard import app
from blackboard.model import Model#, model

Model()

@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        dev_name=os.environ['DEV_NAME'],
        year=datetime.now().year,
        metrics=sorted(Model().output),
        groups=sorted(Model().output['Test 1']),
        json_data=Model().json_output,
        json_info=Model().json_info
    )

@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        dev_name=os.environ['DEV_NAME'],
        dev_email=os.environ['DEV_EMAIL'],
        year=datetime.now().year,
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )