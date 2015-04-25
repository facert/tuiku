"""
    idocument.manage
    ~~~~~~~~~~~~~~~~~~~~

    This script provides some easy to use commands for
    creating the database with or without some sample content.
    You can also run the development server with it.
    Just type `python manage.py` to see the full list of commands.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys

from flask import current_app
from werkzeug.utils import import_string
from flask.ext.script import (Manager, Shell, Server, prompt, prompt_pass,
                              prompt_bool)

from application import app

manager = Manager(app)

# Run local server
manager.add_command("runserver", Server("0.0.0.0", port=8080))



if __name__ == "__main__":
    manager.run()
