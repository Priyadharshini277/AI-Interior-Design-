from flask import Flask, render_template, request, redirect, url_for
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ✅ PRIMARY MODEL (FLUX)
PRIMARY_API = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

# ✅ BACKUP MODEL (IMPORTANT)
FALLBACK_API = "https://router.huggingface.co/hf-inference/models/stabilityai/sdxl-turbo"

HEADERS = {
    "Authorization": f"Bearer {os.getenv('HF_TOKEN')}"
}


# 🔥 IMAGE GENERATION FUNCTION
def generate_image(prompt, api_url):
    response = requests.post(api_url, headers=HEADERS, json={"inputs": prompt})

    if response.status_code == 200:
        return response.content

    elif response.status_code == 503:
        print("Model loading... retrying")
        time.sleep(8)
        return generate_image(prompt, api_url)

    else:
        print("ERROR:", response.text)
        return None


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":

        room = request.form["room"]
        style = request.form["style"]
        budget = request.form["budget"]

        # ✅ NEW: CUSTOM PROMPT
        custom_prompt = request.form.get("custom_prompt")

        if custom_prompt and custom_prompt.strip() != "":
            prompt = custom_prompt
        else:
            prompt = f"""
            A {style} {room} interior design,
            {budget} budget,
            modern furniture,
            aesthetic lighting,
            realistic, high detail, 4k quality
            """

        print("PROMPT:", prompt)

        # 🔥 TRY PRIMARY MODEL (FLUX)
        image = generate_image(prompt, PRIMARY_API)

        # 🔁 FALLBACK IF FAILS
        if not image:
            print("Switching to fallback model...")
            image = generate_image(prompt, FALLBACK_API)

        if image:
            file_path = "static/output.png"
            with open(file_path, "wb") as f:
                f.write(image)

            return redirect(url_for("result", room=room, style=style, budget=budget))

        else:
            print("Image generation failed completely")

    return render_template("index.html")


@app.route("/result")
def result():
    room = request.args.get("room")
    style = request.args.get("style")
    budget = request.args.get("budget")

    return render_template("result.html", room=room, style=style, budget=budget)


if __name__ == "__main__":
    app.run(debug=True)