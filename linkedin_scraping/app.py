import os
from linkedin_api import Linkedin # https://github.com/tomquirk/linkedin-api
from dotenv import load_dotenv
from flask import Flask, request

load_dotenv()
app = Flask(__name__)

# Authenticate using any Linkedin account credentials
api = Linkedin(os.getenv('LINKEDIN_USERNAME'), os.getenv('LINKEDIN_PASSWORD'))

@app.route('/linkedInScore', methods = ['GET'])
def index():
    if request.json and 'operator' in request.json:
        operator = request.json['operator']

        found_user = api.search_people(operator)[0]

        # get profile
        profile = api.get_profile(found_user['public_id'])
        keys_of_interest = ['industryName', 'student', 'experience', 'education', 'publications', 'certifications', 'projects']
        slim_profile = {}

        # copy keys of interest to new dict
        for key in keys_of_interest:
            if key in profile:
                slim_profile[key] = profile[key]

        return slim_profile
    else:
        return 'Was not able to find body which specifies the operator'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5000')