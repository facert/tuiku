from flask import Flask
from flask import render_template
from work import generate
from flask import request, jsonify
import redis
import pymongo
from work import MailToKindle
import os


app = Flask(__name__)


def get_redis():
	redis_conf = {
		'host': '127.0.0.1',
		'port': 6379,
		'db': 0
	}

	pool = redis.ConnectionPool(host=redis_conf['host'], port=redis_conf['port'], db=redis_conf['db'])
	return redis.StrictRedis(connection_pool=pool)


def connect_to_database():
    connection = pymongo.Connection('localhost', 27017)
    db = connection.kindle_db
    return db


redis = get_redis()
db = connect_to_database()


@app.route('/')
def index():
	return render_template("index.html")


@app.route('/send/', methods=['POST'])
def send():
	email = request.form.get("email", None)
	address = request.form.get("address", None)
	if email and address:
		mobi = db.kindle.find({"address": address}).count()
		if mobi:

			print "already exists"
			question_id = address.split("/")[-1]
			mobi_path = os.path.join(os.path.join(os.getcwd(), "mobis"), question_id+".mobi")
			mk = MailToKindle(mobi_path, email)
			mk.send_mail()
		else:
			redis.lpush("kindle", address+";"+email)
			db.kindle.insert({"address": address, "email": email})
		return jsonify({"code": 0})
	return jsonify({"code": 412})


@app.route('/setting')
def setting():
	return render_template("amazon_setting.html")

