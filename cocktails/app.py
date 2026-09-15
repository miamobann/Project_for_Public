import json
import os
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
from openai import OpenAI
import requests

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key or api_key == "YOUR_OPENAI_API_KEY":
    raise ValueError(
        ".env 파일에 올바른 OPENAI_API_KEY가 설정되지 않았습니다."
    )

client = OpenAI(api_key=api_key)

COCKTAIL_API_URL = "https://www.thecocktaildb.com/api/json/v1/1/search.php"

# 선택용 기본 칵테일 목록 (TheCocktailDB 검색 검증 완료 목록)
POPULAR_COCKTAILS = [
    "Mojito",
    "Old Fashioned",
    "Margarita",
    "Cosmopolitan",
    "Martini",
    "Manhattan",
    "Daiquiri",
    "Whiskey Sour",
    "Negroni",
    "Espresso Martini",
    "Dry Martini",
    "Pina Colada",
    "Blue Hawaii",
    "Moscow Mule",
]


def get_recommendation_from_openai(mood_text: str):
    prompt = f"""
사용자가 다음과 같은 기분이나 상황을 입력했습니다:
"{mood_text}"

이 기분에 어울리는 칵테일 하나를 추천하세요.
단, TheCocktailDB에서 검색 가능하도록 널리 알려진 칵테일의 공식 영문명이어야 합니다. (예: "Old Fashioned", "Mojito", "Margarita")

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


def get_mood_from_cocktail(cocktail_name: str):
    prompt = f"""
칵테일 이름: "{cocktail_name}"

이 칵테일의 풍미, 도수, 역사, 분위기를 고려했을 때, 어떤 기분이나 상황에 마시는 것이 가장 어울리는지 감성적으로 설명해 주세요.

반드시 아래 JSON 포맷으로만 응답하세요:
{{
    "suggested_mood": "어울리는 대표 기분 키워드 (예: 차분하게 하루를 정리하고 싶은 밤, 지친 일상을 벗어나 산뜻한 환기가 필요한 순간)",
    "reason": "이 칵테일이 왜 해당 기분에 어울리는지에 대한 감성적인 바텐더의 설명 (한국어 2문장 내외)"
}}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an articulate, poetic bartender.",
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
    return render_template("index.html", cocktails=sorted(POPULAR_COCKTAILS))


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


@app.route("/recommend-by-cocktail", methods=["POST"])
def recommend_by_cocktail():
    cocktail_name = request.form.get("cocktail_name", "").strip()
    if not cocktail_name:
        return redirect(url_for("index"))

    try:
        mood_data = get_mood_from_cocktail(cocktail_name)
        cocktail_info = fetch_cocktail_details(cocktail_name)

        if not cocktail_info:
            cocktail_info = fetch_cocktail_details("Mojito")

        return render_template(
            "result.html",
            mood=mood_data.get("suggested_mood"),
            reason=mood_data.get("reason"),
            cocktail=cocktail_info,
        )
    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)