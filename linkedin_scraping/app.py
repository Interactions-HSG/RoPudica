import json
import os
import openai
import re
from linkedin_api import Linkedin
from dotenv import load_dotenv
from flask import Flask, request
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


@app.route("/linkedInScore", methods=["GET"])
def index():
    if request.json and "operator" in request.json:
        operator = request.json["operator"]
        file_name = "../profile-cache/" + operator + ".json"
        # check if file <operator>.json exists in mounted cache dir and if yes, load it
        try:
            with open(file_name) as json_file:
                print("Loading from file")
                profile = json.load(json_file)
                return {
                    "score": profile["score"],
                    "reasoning": "Loaded from profile file",
                }
        except:
            print("Scraping linkedin")
            profile = api.get_profile(operator)

            # copy keys of interest to new dict
            slim_profile = slim_down_profile(profile)

            combined_prompt = PROMPT + json.dumps(
                slim_profile, default=lambda o: "<not serializable>"
            )

            try:
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": combined_prompt},
                    ],
                )
                chat_response = completion.choices[0].message.content
                chat_response = json.loads(chat_response)

                profile["score"] = chat_response.get("score")
                with open(file_name, "w") as outfile:
                    json.dump(profile, outfile)

                return chat_response

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
