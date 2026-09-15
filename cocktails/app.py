import json
import os
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
from openai import OpenAI
import requests

# .env 파일에서 환경변수 로드
load_dotenv()

app = Flask(__name__)

# 환경변수에서 API 키 추출
api_key = os.getenv("OPENAI_API_KEY")

if not api_key or api_key == "YOUR_OPENAI_API_KEY":
    raise ValueError(
        ".env 파일에 올바른 OPENAI_API_KEY가 설정되지 않았습니다."
    )

client = OpenAI(api_key=api_key)

COCKTAIL_API_URL = "https://www.thecocktaildb.com/api/json/v1/1/search.php"


def get_recommendation_from_openai(mood_text: str):
    prompt = f"""
사용자가 다음과 같은 기분이나 상황을 입력했습니다:
"{mood_text}"

이 기분에 어울리는 칵테일 하나를 추천하세요.
단, TheCocktailDB에서 검색 가능하도록 널리 알려진 칵테일의 공식 영문명이어야 합니다. (예: "Old Fashioned", "Mojito", "Margarita", "Martini", "Cosmopolitan", "Manhattan", "Daiquiri")

반드시 아래 JSON 포맷으로만 응답하세요:
{{
    "cocktail_name": "칵테일 영문 이름",
    "reason": "이 칵테일을 추천하는 감성적인 이유 (한국어 1~2문장)"
}}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a professional bartender who understands emotions.",
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    return json.loads(response.choices[0].message.content)


def fetch_cocktail_details(cocktail_name: str):
    response = requests.get(
        COCKTAIL_API_URL, params={"s": cocktail_name}, timeout=5
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("drinks"):
        return None

    drink = data["drinks"][0]

    ingredients = []
    for i in range(1, 16):
        ing = drink.get(f"strIngredient{i}")
        measure = drink.get(f"strMeasure{i}")
        if ing:
            text = f"{ing} ({measure.strip()})" if measure else ing
            ingredients.append(text)

    return {
        "name": drink.get("strDrink"),
        "category": drink.get("strCategory"),
        "glass": drink.get("strGlass"),
        "instructions": drink.get("strInstructions"),
        "image": drink.get("strDrinkThumb"),
        "ingredients": ingredients,
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/recommend", methods=["POST"])
def recommend():
    mood = request.form.get("mood", "").strip()
    if not mood:
        return redirect(url_for("index"))

    try:
        rec_data = get_recommendation_from_openai(mood)
        cocktail_info = fetch_cocktail_details(rec_data["cocktail_name"])

        if not cocktail_info:
            cocktail_info = fetch_cocktail_details("Mojito")
            rec_data["cocktail_name"] = "Mojito"

        return render_template(
            "result.html",
            mood=mood,
            reason=rec_data.get("reason"),
            cocktail=cocktail_info,
        )
    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)