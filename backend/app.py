from flask import Flask, request, jsonify, render_template, abort
import io
import sys
import json
import os
from pathlib import Path

app = Flask(__name__)

@app.route("/favicon.ico")
def favicon():
    return app.send_static_file("favicon.ico")

BASE_DIR = Path(__file__).resolve().parent
LESSONS_DIR = BASE_DIR / "lessons"


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/module/<module_id>")
def module_runner(module_id):
    lesson_id = request.args.get("lesson", type=int)

    if lesson_id is None:
        abort(404)

    module_path = LESSONS_DIR / f"{module_id}.json"

    if not module_path.exists():
        return "Module not found", 404

    with open(module_path, "r", encoding="utf-8") as f:
        module = json.load(f)

    lessons = module.get("lessons", [])
    lesson = next((l for l in lessons if l["id"] == lesson_id), None)

    if lesson is None:
        return "Lesson not found", 404

    return render_template(
        "index.html",
        module_id=module_id,
        module_title=module["title"],
        lesson_id=lesson_id,
        lesson=lesson,
        max_lesson=len(lessons)
    )


@app.route("/run", methods=["POST"])
def run_code():
    user_code = request.json.get("code", "")
    module_id = request.json.get("module_id")
    lesson_id = request.json.get("lesson_id")

    module_path = LESSONS_DIR / f"{module_id}.json"

    if not module_path.exists():
        return jsonify({"status": "error", "feedback": "Module not found"})

    with open(module_path, "r", encoding="utf-8") as f:
        module = json.load(f)

    lesson = next(
        (l for l in module["lessons"] if l["id"] == lesson_id),
        None
    )

    if lesson is None:
        return jsonify({"status": "error", "feedback": "Lesson not found"})

    expected = lesson.get("expected_output", "").strip()

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        exec(user_code, {})
        output = sys.stdout.getvalue().strip()

        if output == expected:
            result = {
                "status": "correct",
                "output": output,
                "feedback": "[OK] Correct!"
            }
        else:
            result = {
                "status": "incorrect",
                "output": output,
                "feedback": (
                    "[Feedback] Not quite.\n"
                    f"Expected output:\n{expected}"
                )
            }

    except Exception as e:
        result = {
            "status": "error",
            "output": "",
            "feedback": f"[Error] {str(e)}"
        }
    finally:
        sys.stdout = old_stdout

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
