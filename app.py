#!flask/bin/python
from flask import Flask, jsonify, request, render_template, redirect, Response
from utils import connect_db, authenticate_linkedin, getenv, save_linkedin_profile
import json
import os
from uuid import uuid4
from werkzeug.routing import BaseConverter


app = Flask(__name__)

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter

"""UI Routes"""

@app.route('/details/<regex(".+"):client_code>/', methods=['GET'])
def details(client_code):
	return render_template('index.html', client_code=client_code)

@app.route('/get_user/', methods=['GET'])
def get_user():
	client_id = getenv('LINKEDIN_CLIENT_ID')
	scope = 'r_fullprofile r_emailaddress'
	state = str(uuid4()).replace('-','')
	client_code = request.args['client_code']
	redirect_uri = '%s/oauth/%s/' % (str(getenv('PATH_URL')), client_code)
	url = 'https://www.linkedin.com/uas/oauth2/authorization?response_type=code&client_id=%s&scope=%s&state=%s&redirect_uri=%s' % (client_id, scope, state, redirect_uri)
	return redirect(url)

@app.route('/oauth/<regex(".+"):client_code>/', methods=['GET'])
def oauth(client_code):
	code = request.args['code']
	access_token = authenticate_linkedin(code, client_code)
	user_status = save_linkedin_profile(access_token, client_code)

	if user_status:
		return render_template('error.html')
	else:
		return render_template('success.html')

"""Run server"""
if __name__ == '__main__':
	app.run(debug = True)