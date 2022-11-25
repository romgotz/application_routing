from flask import Flask, render_template, url_for, abort
from random import choice
from markupsafe import escape
import datetime

app = Flask(__name__)
app.debug = True

@app.route('/')
def index():
    return render_template(
        'index.html', 
        random=choice(range(1,46)), 
        utc_dt=datetime.datetime.utcnow()
    )

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/comments/')
def comments():
    comments = ['This is the first comment.',
                'This is the second comment.',
                'This is the third comment.',
                'This is the fourth comment.'
                ]

    return render_template('comments.html', comments=comments)

# The above function returns the HTML code to be displayed on the page

if __name__ == '__main__':
    app.run()