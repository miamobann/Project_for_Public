import json
import math
import os
import requests
import folium
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
EXCHANGE_API_KEY = os.getenv("EXCHANGERATE_API_KEY")
KAKAO_JS_KEY = os.getenv("kakao_js_key") or os.getenv("KAKAO_JS_KEY") or os.getenv("kakao_api")
KAKAO_REST_KEY = os.getenv("kakao_rest_key") or os.getenv("KAKAO_REST_KEY") or os.getenv("kakao_api")
OSM_HEADERS = {"User-Agent": "Tripboard/1.0 travel-planner"}

st.set_page_config(page_title="Tripboard | 국내 Kakao · 해외 OSM", page_icon="✦", layout="wide")

CITY_DATA = {
    "서울": {"query": "Seoul", "country": "대한민국", "currency": "KRW", "type": "국내"},
    "부산": {"query": "Busan", "country": "대한민국", "currency": "KRW", "type": "국내"},
    "제주": {"query": "Jeju", "country": "대한민국", "currency": "KRW", "type": "국내"},
    "인천": {"query": "Incheon", "country": "대한민국", "currency": "KRW", "type": "국내"},
    "도쿄": {"query": "Tokyo", "country": "일본", "currency": "JPY", "type": "해외"},
    "오사카": {"query": "Osaka", "country": "일본", "currency": "JPY", "type": "해외"},
    "뉴욕": {"query": "New York", "country": "미국", "currency": "USD", "type": "해외"},
    "파리": {"query": "Paris", "country": "프랑스", "currency": "EUR", "type": "해외"},
    "런던": {"query": "London", "country": "영국", "currency": "GBP", "type": "해외"},
}

COUNTRY_INFO = {
    "KR": ("대한민국", "KRW"), "JP": ("일본", "JPY"), "CN": ("중국", "CNY"),
    "US": ("미국", "USD"), "GB": ("영국", "GBP"), "FR": ("프랑스", "EUR"),
    "DE": ("독일", "EUR"), "IT": ("이탈리아", "EUR"), "ES": ("스페인", "EUR"),
    "AU": ("호주", "AUD"), "CA": ("캐나다", "CAD"), "TH": ("태국", "THB"),
    "VN": ("베트남", "VND"), "SG": ("싱가포르", "SGD"), "TW": ("대만", "TWD"),
}

OSM_FALLBACK_COORDS = {
    "Tokyo": (35.6762, 139.6503),
    "Osaka": (34.6937, 135.5023),
    "New York": (40.7128, -74.0060),
    "Paris": (48.8566, 2.3522),
    "London": (51.5074, -0.1278),
}

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
    :root { --ink:#18221f; --muted:#71807a; --line:#dfe8e2; --paper:#f7faf7; --green:#17634e; --mint:#dceee5; --coral:#e57355; }
    .stApp { background:var(--paper); color:var(--ink); }
    .block-container { max-width:1240px; padding:2rem 3rem 4rem; }
    h1,h2,h3,p,div,button,input { font-family:'Noto Sans KR','DM Sans',sans-serif; }
    .brand { display:flex; justify-content:space-between; color:var(--green); font-weight:800; letter-spacing:.08em; margin-bottom:3.8rem; }
    .brand span { color:var(--muted); font-size:.75rem; font-weight:500; letter-spacing:0; }
    .home { max-width:760px; margin:0 auto 4rem; text-align:center; }
    .eyebrow { color:var(--green); font-size:.74rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; margin-bottom:1rem; }
    .home h1 { font-size:clamp(2.9rem,7vw,6rem); letter-spacing:-.09em; line-height:1; margin:0; }
    .home h1 span { color:var(--green); }
    .home p,.hint,.foot-note { color:var(--muted); line-height:1.8; }
    .hint { font-size:.83rem; text-align:center; margin-top:1rem; }
    .result-head { display:flex; justify-content:space-between; align-items:end; border-bottom:1px solid var(--line); padding-bottom:1.2rem; margin:2.5rem 0 1.3rem; }
    .result-head h2 { margin:0; font-size:2rem; letter-spacing:-.07em; }
    .result-head p { margin:0; color:var(--muted); font-size:.85rem; }
    .place-card,.rate-card { background:white; border:1px solid var(--line); border-radius:12px; padding:.9rem 1rem; margin-bottom:.75rem; min-height:128px; }
    .place-card strong { font-size:1.02rem; }.place-card small,.rate-card p { color:var(--muted); display:block; margin-top:.4rem; line-height:1.5; }
    .place-card .detail { color:var(--muted); font-size:.78rem; margin-top:.65rem; line-height:1.6; }
    .card-label { color:var(--coral); font-size:.7rem; font-weight:800; letter-spacing:.13em; margin-bottom:.5rem; }
    .summary-card { background:var(--green); color:white; border-radius:14px; padding:1.2rem 1.4rem; display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin-bottom:1.6rem; }
    .summary-card > div { border-left:1px solid #ffffff33; padding-left:1rem; }
    .summary-card .muted { color:#c7ddd3; font-size:.7rem; display:block; letter-spacing:.1em; }.summary-card strong { display:block; font-size:1.45rem; margin:.25rem 0; }.summary-card small { color:#c7ddd3; font-size:.78rem; }
    .weather-main { display:flex; align-items:center; gap:.8rem; border-top:1px solid #ffffff33; padding-top:1rem; }.weather-main img { width:58px; }.weather-main strong { font-size:2rem; }
    .summary-metrics { display:grid; grid-template-columns:repeat(3,1fr); gap:.6rem; margin-top:1.3rem; }.summary-metrics div { border-left:1px solid #ffffff33; padding-left:.7rem; color:#c7ddd3; font-size:.78rem; }.summary-metrics b { display:block; color:white; margin-top:.25rem; }
    .empty-map { height:430px; display:grid; place-items:center; color:var(--muted); background:#edf4ef; border-radius:10px; text-align:center; padding:2rem; }
    .route-card { background:#edf4ef; border-radius:12px; padding:1.2rem 1.3rem; margin-top:1.5rem; }
    .route-card h3,.budget-card h3 { margin:0 0 .8rem; font-size:1.05rem; }
    .route-step { display:flex; gap:.8rem; align-items:flex-start; padding:.65rem 0; border-top:1px solid #d5e4db; }
    .route-step:first-of-type { border-top:0; }.route-number { color:var(--coral); font-weight:800; font-size:.78rem; min-width:2rem; }
    .route-step strong { display:block; font-size:.9rem; }.route-step small { color:var(--muted); }
    .budget-card { background:white; border:1px solid var(--line); border-radius:12px; padding:1.2rem 1.3rem; margin-top:1.5rem; }
    .budget-line { display:flex; justify-content:space-between; color:var(--muted); font-size:.86rem; padding:.35rem 0; }.budget-total { border-top:1px solid var(--line); margin-top:.5rem; padding-top:.75rem; font-weight:700; color:var(--ink); }
    .place-grid-title { margin:.8rem 0 .7rem; }
    @media (max-width:760px) { .block-container{padding:1.2rem 1rem 3rem;} .brand{margin-bottom:3rem;} .result-head{display:block;} .result-head p{margin-top:.5rem;} .summary-card{grid-template-columns:1fr;} .summary-card > div{border-left:0;border-top:1px solid #ffffff33;padding: .7rem 0 0;} .summary-card > div:first-child{border-top:0;padding-top:0;} }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=600)
def fetch_weather(city: str):
    if not WEATHER_API_KEY:
        return 0, {"message": "OPENWEATHER_API_KEY가 설정되지 않았습니다."}
    try:
        response = requests.get("https://api.openweathermap.org/data/2.5/weather", params={"q": city, "appid": WEATHER_API_KEY, "units": "metric", "lang": "kr"}, timeout=8)
        return response.status_code, response.json()
    except requests.RequestException as error:
        return 0, {"message": str(error)}


@st.cache_data(ttl=600)
def fetch_rates():
    if not EXCHANGE_API_KEY:
        return 0, {"message": "EXCHANGERATE_API_KEY가 설정되지 않았습니다."}
    try:
        response = requests.get(f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest/USD", timeout=8)
        return response.status_code, response.json()
    except requests.RequestException as error:
        return 0, {"message": str(error)}


@st.cache_data(ttl=600)
def kakao_places(query: str):
    if not KAKAO_REST_KEY:
        return []
    try:
        response = requests.get("https://dapi.kakao.com/v2/local/search/keyword.json", headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}, params={"query": query, "size": 8}, timeout=8)
        return response.json().get("documents", []) if response.status_code == 200 else []
    except requests.RequestException:
        return []


@st.cache_data(ttl=600)
def kakao_category_places(query: str):
    return {
        "관광지": kakao_places(f"{query} 관광지") or [],
        "식당": kakao_places(f"{query} 맛집") or [],
    }


@st.cache_data(ttl=3600)
def osm_places(query: str):
    try:
        response = requests.get("https://nominatim.openstreetmap.org/search", params={"q": query, "format": "jsonv2", "limit": 1, "accept-language": "ko,en"}, headers=OSM_HEADERS, timeout=10)
        response.raise_for_status()
        locations = response.json()
        if not locations:
            return {"관광지": [], "식당": []}, None
        location = locations[0]
        lat, lon = float(location["lat"]), float(location["lon"])
        map_center = {"lat": lat, "lon": lon, "name": location.get("display_name", query)}
        query_text = f'''[out:json][timeout:25];(nwr["tourism"~"attraction|museum|gallery|viewpoint|theme_park|zoo"](around:6000,{lat},{lon});nwr["amenity"~"restaurant|cafe|fast_food|food_court"](around:6000,{lat},{lon});nwr["historic"](around:6000,{lat},{lon}););out center tags;'''
        try:
            response = requests.post("https://overpass-api.de/api/interpreter", data=query_text, headers=OSM_HEADERS, timeout=30)
            response.raise_for_status()
            elements = response.json().get("elements", [])
        except (requests.RequestException, ValueError):
            return {"관광지": [], "식당": []}, map_center

        places = []
        for element in elements:
            tags = element.get("tags", {})
            center = element.get("center", {})
            place_lat = element.get("lat", center.get("lat")); place_lon = element.get("lon", center.get("lon"))
            if not tags.get("name") or place_lat is None or place_lon is None:
                continue
            osm_category = tags.get("tourism") or tags.get("amenity") or tags.get("historic") or "tourist attraction"
            category = "식당" if tags.get("amenity") in {"restaurant", "cafe", "fast_food", "food_court"} else "관광지"
            places.append({"place_name": tags["name"], "category": category, "category_name": osm_category, "address_name": tags.get("addr:street", "OpenStreetMap 장소"), "lat": float(place_lat), "lon": float(place_lon)})
            if len(places) >= 8:
                break
        return {"관광지": [place for place in places if place["category"] == "관광지"], "식당": [place for place in places if place["category"] == "식당"]}, map_center
    except (requests.RequestException, ValueError, KeyError):
        return {"관광지": [], "식당": []}, None


def city_info_from_search(query: str, active_type: str):
    normalized_query = query.strip()
    for city_name, known_info in CITY_DATA.items():
        if normalized_query.casefold() in {city_name.casefold(), known_info["query"].casefold()}:
            return known_info.copy()

    weather_status, weather = fetch_weather(query)
    code = weather.get("sys", {}).get("country", "") if weather_status == 200 else ""
    country, currency = COUNTRY_INFO.get(code, (code or "검색 지역", "USD"))
    if active_type == "국내":
        country, currency = "대한민국", "KRW"
    return {"query": query, "country": country, "currency": currency, "type": active_type}


def flatten_places(place_groups: dict):
    if not isinstance(place_groups, dict):
        return []
    return (place_groups.get("관광지") or []) + (place_groups.get("식당") or [])


def distance_km(first_lat: float, first_lon: float, second_lat: float, second_lon: float):
    latitude_delta = math.radians(second_lat - first_lat)
    longitude_delta = math.radians(second_lon - first_lon)
    first_latitude = math.radians(first_lat)
    second_latitude = math.radians(second_lat)
    value = (math.sin(latitude_delta / 2) ** 2) + (math.sin(longitude_delta / 2) ** 2) * math.cos(first_latitude) * math.cos(second_latitude)
    return 6371 * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def render_map(city_name: str, info: dict, place_groups: dict, center: dict | None):
    places = flatten_places(place_groups)
    if info["type"] == "해외":
        if not center:
            st.markdown('<div class="empty-map">OpenStreetMap에서 위치를 찾지 못했습니다.</div>', unsafe_allow_html=True)
            return
        travel_map = folium.Map(location=[center["lat"], center["lon"]], zoom_start=12, tiles="OpenStreetMap", control_scale=True)
        folium.Marker([center["lat"], center["lon"]], tooltip=center["name"], icon=folium.Icon(color="green")).add_to(travel_map)
        for place in places:
            marker_color = "red" if place.get("category") == "식당" else "orange"
            folium.Marker([place["lat"], place["lon"]], tooltip=place["place_name"], popup=place["category_name"], icon=folium.Icon(color=marker_color, icon="cutlery" if marker_color == "red" else "star")).add_to(travel_map)
        components.html(travel_map.get_root().render(), height=440)
        st.caption("© OpenStreetMap contributors")
        return
    if not KAKAO_JS_KEY or not center:
        st.markdown('<div class="empty-map">Kakao 지도 키 또는 검색 결과를 확인해 주세요.</div>', unsafe_allow_html=True)
        return
    map_html = f'''<html><head><meta charset="utf-8"><style>html,body,#map{{margin:0;width:100%;height:430px;border-radius:10px;overflow:hidden}}</style><script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&autoload=false"></script></head><body><div id="map"></div><script>const places={json.dumps(places, ensure_ascii=False)};kakao.maps.load(function(){{const map=new kakao.maps.Map(document.getElementById("map"),{{center:new kakao.maps.LatLng({center["y"]},{center["x"]}),level:6}});places.forEach(function(p){{new kakao.maps.Marker({{map:map,position:new kakao.maps.LatLng(p.y,p.x)}});}});}});</script></body></html>'''
    components.html(map_html, height=440)


def render_compact_summary(city_name: str, info: dict, weather_status: int, weather: dict, rate_status: int, rates_data: dict):
    weather_text = "날씨 확인 필요"
    weather_value = "--"
    if weather_status == 200:
        weather_text = weather.get("weather", [{}])[0].get("description", "현재 날씨")
        weather_value = f'{weather.get("main", {}).get("temp", 0):.0f}°'

    rate_text = "환율 확인 필요"
    if rate_status == 200 and rates_data.get("result") == "success":
        rates = rates_data.get("conversion_rates", {})
        usd_krw = rates.get("KRW", 1.0)
        currency = info["currency"]
        local_rate = usd_krw / rates.get(currency, 1.0) if currency != "KRW" else 1.0
        rate_text = f"1 {currency} = {local_rate:,.2f} KRW"

    st.markdown(
        f'<div class="summary-card"><div><span class="muted">WEATHER</span><strong>{weather_value}</strong><small>{weather_text}</small></div><div><span class="muted">TRAVEL MONEY</span><strong>환율</strong><small>{rate_text}</small></div><div><span class="muted">DESTINATION</span><strong>{city_name}</strong><small>{info["country"]} · {info["type"]}</small></div></div>',
        unsafe_allow_html=True,
    )
    if weather_status != 200:
        st.caption(f'날씨 API 응답을 확인할 수 없습니다: {weather.get("message", "알 수 없는 오류")}')
    if rate_status != 200 or rates_data.get("result") != "success":
        st.caption(f'환율 API 응답을 확인할 수 없습니다: {rates_data.get("message", rates_data.get("error-type", "알 수 없는 오류"))}')


def render_exchange_calculator(info: dict, rate_status: int, rates_data: dict):
    if rate_status != 200 or rates_data.get("result") != "success":
        return
    rates = rates_data.get("conversion_rates", {})
    currency = info["currency"]
    usd_to_krw = rates.get("KRW")
    currency_rate = rates.get(currency)
    if not usd_to_krw or not currency_rate:
        return
    krw_per_unit = usd_to_krw / currency_rate if currency != "KRW" else 1.0
    st.markdown("#### 환율 계산기")
    calculator_col, result_col = st.columns([1, 1], gap="medium")
    with calculator_col:
        amount_krw = st.number_input("원화 입력", min_value=0, value=100000, step=10000, key=f"krw_amount_{info['query']}")
    converted_amount = amount_krw / krw_per_unit if krw_per_unit else 0
    with result_col:
        st.metric(f"현지 통화 ({currency})", f"{converted_amount:,.2f} {currency}")
    st.caption(f"적용 환율: 1 {currency} = {krw_per_unit:,.2f} KRW")


def render_route_and_budget(place_groups: dict, info: dict, center: dict | None):
    places = flatten_places(place_groups)
    if center and places:
        center_lat = float(center.get("lat", center.get("y")))
        center_lon = float(center.get("lon", center.get("x")))
        for place in places:
            if "lat" in place and "lon" in place:
                place["distance_km"] = distance_km(center_lat, center_lon, place["lat"], place["lon"])
            elif "y" in place and "x" in place:
                place["distance_km"] = distance_km(center_lat, center_lon, float(place["y"]), float(place["x"]))
        places.sort(key=lambda place: place.get("distance_km", 999))

    attractions = [place for place in places if place.get("category") != "식당"]
    restaurants = [place for place in places if place.get("category") == "식당"]
    route_places = (attractions[:2] + restaurants[:1])[:3]
    if route_places:
        route_steps = "".join(f'<div class="route-step"><span class="route-number">0{index}</span><div><strong>{place.get("place_name", "추천 장소")}</strong><small>{"식사" if place.get("category") == "식당" else "관광"} · 약 {place.get("distance_km", 0):.1f}km</small></div></div>' for index, place in enumerate(route_places, 1))
        st.markdown(f'<div class="route-card"><h3>오늘의 추천 동선</h3>{route_steps}</div>', unsafe_allow_html=True)
    else:
        st.info("장소가 확보되면 추천 동선을 표시합니다.")

    days = st.number_input("예상 여행일", min_value=1, max_value=14, value=2, step=1, key=f"trip_days_{info['query']}")
    transport_cost = 15000 * days
    meal_cost = 45000 * days
    activity_cost = 30000 * days
    total_cost = transport_cost + meal_cost + activity_cost
    st.markdown(f'<div class="budget-card"><h3>여행 예산 가이드 · {days}일</h3><div class="budget-line"><span>교통</span><strong>₩{transport_cost:,.0f}</strong></div><div class="budget-line"><span>식비</span><strong>₩{meal_cost:,.0f}</strong></div><div class="budget-line"><span>관광·체험</span><strong>₩{activity_cost:,.0f}</strong></div><div class="budget-line budget-total"><span>예상 합계</span><strong>₩{total_cost:,.0f}</strong></div></div>', unsafe_allow_html=True)


def render_place_group(title: str, places: list[dict], limit: int = 4):
    st.markdown(f'<h5 class="place-grid-title">{title}</h5>', unsafe_allow_html=True)
    if not places:
        st.caption("가까운 장소를 찾지 못했습니다.")
        return
    card_columns = st.columns(2, gap="small")
    for index, place in enumerate(places[:limit], 1):
        address = place.get("road_address_name") or place.get("address_name", "")
        details = []
        if place.get("distance"):
            details.append(f'중심에서 {float(place["distance"]) / 1000:.1f}km')
        elif place.get("distance_km") is not None:
            details.append(f'중심에서 {place["distance_km"]:.1f}km')
        if place.get("phone"):
            details.append(place["phone"])
        if place.get("place_url"):
            details.append(f'<a href="{place["place_url"]}" target="_blank">상세 보기 ↗</a>')
        detail_html = " · ".join(details) or "추천 여행 장소"
        with card_columns[(index - 1) % 2]:
            st.markdown(f'<div class="place-card"><div class="card-label">0{index}</div><strong>{place.get("place_name", "추천 장소")}</strong><small>{place.get("category_name", title)}<br>{address}</small><div class="detail">{detail_html}</div></div>', unsafe_allow_html=True)


def render_results(city_name: str, info: dict):
    if info["type"] == "해외":
        place_groups, center = osm_places(info["query"])
        if center is None and info["query"] in OSM_FALLBACK_COORDS:
            lat, lon = OSM_FALLBACK_COORDS[info["query"]]
            center = {"lat": lat, "lon": lon, "name": city_name}
    else:
        place_groups = kakao_category_places(info["query"])
        all_places = flatten_places(place_groups)
        center = all_places[0] if all_places and "x" in all_places[0] and "y" in all_places[0] else None

    weather_status, weather_data = fetch_weather(info["query"])
    rate_status, rates_data = fetch_rates()
    provider = "OpenStreetMap" if info["type"] == "해외" else "Kakao Map"
    st.markdown(f'<div class="result-head"><div><div class="eyebrow">Your destination</div><h2>{city_name}, {info["country"]}</h2></div><p>{info["type"]} · {provider}</p></div>', unsafe_allow_html=True)
    render_compact_summary(city_name, info, weather_status, weather_data, rate_status, rates_data)
    render_exchange_calculator(info, rate_status, rates_data)

    left, right = st.columns([1.1, 1.35], gap="large")
    with left:
        st.markdown("#### 가까운 장소 추천")
        render_place_group("관광지", place_groups.get("관광지", []))
        render_place_group("식당", place_groups.get("식당", []))
    with right:
        st.markdown("#### 지역 지도")
        with st.container(border=True):
            render_map(city_name, info, place_groups, center)
    st.markdown("### 여행 동선과 예산")
    render_route_and_budget(place_groups, info, center)


def render_tab(active_type: str, placeholder: str, form_key: str):
    st.markdown('<div class="home"><div class="eyebrow">Travel, prepared</div><h1>여행의 시작을<br><span>한 곳에서.</span></h1><p>도시를 검색하면 장소, 지도, 날씨와 환율을 한눈에 확인합니다.</p></div>', unsafe_allow_html=True)
    with st.form(form_key):
        query = st.text_input("여행지 검색", placeholder=placeholder, label_visibility="collapsed")
        submitted = st.form_submit_button("여행지 확인하기", use_container_width=True, type="primary")
    if submitted:
        if not query.strip():
            st.warning("여행할 도시 이름을 입력해 주세요.")
        else:
            st.session_state[f"{active_type}_destination"] = query.strip()
    destination = st.session_state.get(f"{active_type}_destination")
    if destination:
        render_results(destination, city_info_from_search(destination, active_type))


st.markdown('<div class="brand">TRIPBOARD <span>국내는 Kakao · 해외는 OpenStreetMap</span></div>', unsafe_allow_html=True)
domestic_tab, overseas_tab = st.tabs(["국내 여행", "해외 여행"])
with domestic_tab:
    render_tab("국내", "예: 서울, 강릉, 여수", "domestic_search")
with overseas_tab:
    render_tab("해외", "예: 도쿄, 교토, 다낭, 로마", "overseas_search")
