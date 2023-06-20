import json
import os
import openai
import re
from linkedin_api import Linkedin  # https://github.com/tomquirk/linkedin-api
from dotenv import load_dotenv
from flask import Flask, request
from linkedin_scraper import Person, actions
from selenium import webdriver
from dotenv import load_dotenv

PROMPT = 'I have a JSON document containing information about an individuals work experience with industrial robots. Can you please analyze this document and provide me with a score on a scale of 1-5 for how well the individual has experience with industrial robots? This experience could also come from industrial settings including automation, where one could assume connection to robots. 1 should be the lowest value and even be returned if the individual has no experience, or its level can not be determined. Please answer with a JSON document of the following structure: {"score": x, "reasoning": y}, where you can fill in x and y. Here is the JSON document you should use as input: '
KEYS_OF_INTEREST = [
    "industryName",
    "student",
    "experience",
    "education",
    "publications",
    "certifications",
    "projects",
]

load_dotenv()
app = Flask(__name__)

# Authenticate using any Linkedin account credentials
api = Linkedin(os.getenv("LINKEDIN_USERNAME"), os.getenv("LINKEDIN_PASSWORD"))
openai.api_key = os.getenv("OPENAI_KEY")


def del_attribute(dict, key, attribute=[]):
    for element in dict[key]:
        for attr in attribute:
            if attr in element:
                del element[attr]


def slim_down_profile(big_profile):
    # copy keys of interest to new dict
    slim_profile = {}
    for key in KEYS_OF_INTEREST:
        if key in big_profile:
            slim_profile[key] = big_profile[key]
            if key == "projects":
                del_attribute(slim_profile, key, attribute=["members"])
            if key == "certifications":
                del_attribute(slim_profile, key, attribute=["authority", "timePeriod"])
            if key == "publications":
                del_attribute(slim_profile, key, attribute=["authors", "description"])
            if key == "experience":
                del_attribute(
                    slim_profile,
                    key,
                    attribute=[
                        "entityUrn",
                        "geoLocationName",
                        "locationName",
                        "timePeriod",
                        "companyUrn",
                        "companyLogoUrl",
                        "$anti_abuse_metadata",
                        "geoUrn",
                        "region",
                    ],
                )
            if key == "education":
                del_attribute(
                    slim_profile,
                    key,
                    attribute=[
                        "entityUrn",
                        "school",
                        "schoolUrn",
                        "courses",
                        "degreeUrn",
                        "honors",
                    ],
                )

    return slim_profile


def alternative_scraping(operator_linkeddin_url):
    driver = webdriver.Chrome()
    email = os.getenv("LINKEDIN_USERNAME")
    password = os.getenv("LINKEDIN_PASSWORD")
    actions.login(driver, email, password)
    person = Person(operator_linkeddin_url, driver=driver)

    profile_dict = {"name": person.name, "about": person.about}

    edu_list = []
    for edu in person.educations:
        edu_dict = {}
        edu_dict["institution_name"] = edu.institution_name
        edu_dict["industry"] = edu.industry
        edu_dict["from_date"] = edu.from_date
        edu_dict["to_date"] = edu.to_date
        edu_dict["description"] = edu.description
        edu_dict["degree"] = edu.degree
        edu_list.append(edu_dict)
    profile_dict["education"] = edu_list

    exp_list = []
    for exp in person.experiences:
        exp_dict = {}
        exp_dict["institution_name"] = exp.institution_name
        exp_dict["industry"] = exp.industry
        exp_dict["from_date"] = exp.from_date
        exp_dict["to_date"] = exp.to_date
        exp_dict["description"] = exp.description
        exp_dict["position_title"] = exp.position_title
        exp_dict["duration"] = exp.duration
        exp_dict["location"] = exp.location
        exp_list.append(exp_dict)
    profile_dict["experience"] = exp_list

    acc_list = []
    for acc in person.accomplishments:
        acc_dict = {}
        acc_dict["category"] = acc.category
        acc_dict["title"] = acc.title
        acc_list.append(acc_dict)
    profile_dict["accomplishments"] = acc_list

    int_list = []
    for interest in person.interests:
        int_dict = {}
        int_dict["title"] = interest.title
        int_list.append(int_dict)
    profile_dict["interests"] = int_list

    # print(profile_dict)
    return profile_dict


@app.route("/linkedInScore", methods=["GET"])
def index():
    if request.json and "operator" in request.json:
        operator = request.json["operator"]

        # found_user = api.search_people(operator)[0]

        # get profile
        # profile = api.get_profile(found_user["public_id"])

        # copy keys of interest to new dict
        # slim_profile = slim_down_profile(profile)

        new_profile = alternative_scraping(operator)

        combined_prompt = PROMPT + json.dumps(
            new_profile, default=lambda o: "<not serializable>"
        )

        try:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": combined_prompt},
                ],
            )
            return completion.choices[0].message.content
        except Exception as e:
            return {
                "score": 0,
                "reasoning": "There seems to be an issue with the OpenAI API: "
                + str(e),
            }
    else:
        return {
            "score": 0,
            "reasoning": "Was not able to find somebody which specifies the operator",
        }


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="5000")
