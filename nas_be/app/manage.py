import os
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from app_test import app, db

manager = Manager(app)

@manager.command
def db_run():
	db.drop_all()
	db.create_all()

@manager.command
def run():
    app.run(host="0.0.0.0")

if __name__ == '__main__':
	manager.run()
