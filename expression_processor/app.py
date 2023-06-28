from flask import Flask, request
from deepface import DeepFace


app = Flask(__name__)
gender, race, age = None, None, None


def analyze_image(
    img_path,
    actions=["age", "gender", "emotion", "race"],
    detector_backend="opencv",
    enforce_detection=True,
    align=True,
):
    result = {}
    try:
        demographies = DeepFace.analyze(
            img_path=img_path,
            actions=actions,
            detector_backend=detector_backend,
            enforce_detection=enforce_detection,
            align=align,
        )
        result["results"] = demographies
        return result
    except ValueError as e:
        print(e)
        return None


def analysis_route_functionality(request, actions=["age", "gender", "emotion", "race"]):
    input_args = request.get_json()

    if input_args is None:
        return {"message": "empty input set passed"}

    img_path = input_args.get("img_path")
    if img_path is None:
        return {"message": "you must pass img_path input"}

        demographies = analyze_image(
            img_path=img_path,
            actions=actions,
        )
        if demographies is None:
            return {
                "message": "there seems to have been an issue while analyzing the image"
            }

        return demographies


@app.route("/analyze_emotion", methods=["POST"])
def analyze_emotion():
    return analysis_route_functionality(request, actions=["emotion"])


@app.route("/operator_details", methods=["get"])
def get_operator_details():
    global gender, race, age
    return {
        "gender": gender,
        "race": race,
        "age": age,
    }


@app.route("/analyze", methods=["POST"])
def analyze():
    global gender, race, age
    res = analysis_route_functionality(request)
    # TODO analyze face against db
    if res and res.get("results"):
        gender = res.get("results")[0].get("dominant_gender")
        race = res.get("results")[0].get("dominant_race")
        age = res.get("results")[0].get("age")
        return res
    if res and res.get("message"):
        return res
    return None
