from flask import Flask, request
from deepface import DeepFace


app = Flask(__name__)


def analyze_image(
    img_path,
    actions=["age", "gender", "emotion", "race"],
    detector_backend="opencv",
    enforce_detection=True,
    align=True,
):
    result = {}
    demographies = DeepFace.analyze(
        img_path=img_path,
        actions=actions,
        detector_backend=detector_backend,
        enforce_detection=enforce_detection,
        align=align,
    )
    result["results"] = demographies
    return result


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

    return demographies


@app.route("/analyze_emotion", methods=["POST"])
def analyze_emotion():
    return analysis_route_functionality(request, actions=["emotion"])


@app.route("/analyze", methods=["POST"])
def analyze():
    return analysis_route_functionality(request)
