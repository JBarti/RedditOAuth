from datetime import datetime
import json
import requests

from flask import Flask, redirect, request, session, jsonify

# date, campaign, spend, clicks, impressions

app = Flask(__name__)
app.config["SECRET_KEY"] = "tajni kljuc"
app.config["DEBUG"] = True

CLIENT_ID = "1Yn1t8lFcixJSw"
CLIENT_SECRET = "uMMpmJYAO2lbU88SYpBaVkDFLngBdQ"
REDIRECT_URL = "http://localhost:3000/reddit_redirect"

TIME_FORMAT = "%Y-%m-%d"
GROUP_BY_SET = {
    "ad_id",
    "ad_group_id",
    "campaign_id and/or one of date",
    "country",
    "metro",
    "interest",
    "community",
    "placement",
}


@app.route("/give_access")
def give_reddit_access():
    url = "https://www.reddit.com/api/v1/access_token"
    duration = "permanent"
    scope = "adsread identity"
    random_string = "asdsad"

    url = f"https://www.reddit.com/api/v1/authorize?client_id={CLIENT_ID}&response_type=code&state={random_string}&redirect_uri={REDIRECT_URL}&duration={duration}&scope={scope}"

    return redirect(url)


@app.route("/reddit_redirect")
def reddit_redirect():
    print(request.args)
    if request.args.get("code"):
        session["code"] = request.args["code"]
        return "You've managed to get reddit user data"


@app.route("/get_access_token")
def get_access_token():
    url = "https://www.reddit.com/api/v1/access_token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "WinsdorTest",
    }
    auth = requests.auth.HTTPBasicAuth(
        username=CLIENT_ID,
        password=CLIENT_SECRET,
    )
    data = {
        "grant_type": "authorization_code",
        "code": session["code"],
        "redirect_uri": REDIRECT_URL,
    }

    response = requests.post(
        url,
        headers=headers,
        auth=auth,
        data=data,
    )

    data = response.json()
    print(data)
    session["access_token"] = data["access_token"]
    session["refresh_token"] = data["refresh_token"]
    return response.text


@app.route("/refresh_access_token")
def refresh_access_token():
    url = "https://www.reddit.com/api/v1/access_token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "WinsdorTest",
    }
    auth = requests.auth.HTTPBasicAuth(
        username=CLIENT_ID,
        password=CLIENT_SECRET,
    )
    data = {
        "grant_type": "refresh_token",
        "refresh_token": session["refresh_token"],
    }

    response = requests.post(
        url,
        headers=headers,
        auth=auth,
        data=data,
    )

    data = response.json()
    session["access_token"] = data["access_token"]
    return response.text


@app.route("/accounts/t2_<account_id>/reports")
def get_reports(account_id):
    with open("./data.json", "r") as file:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        group_by = request.args.get("group_by")
        time_zone_id = request.args.get("time_zone_id")
        reports_data = json.load(file)["reports"]

        if start_date:
            start_date = datetime.strptime(start_date, TIME_FORMAT)
        if end_date:
            end_date = datetime.strptime(end_date, TIME_FORMAT)

        user_reports = reports_data.get(account_id) or {"data": []}
    return jsonify(user_reports)


@app.route("/accounts/t2_<account_id>/campaigns")
@app.route("/accounts/t2_<account_id>/campaigns/<campaign_id>")
def get_campaigns(account_id, campaign_id=None):
    with open("./data.json", "r") as file:
        campaign_data = json.load(file)["campaigns"].get(account_id) or {"data": []}
        print(campaign_data)

        if not campaign_id:
            return jsonify(campaign_data)

        for campaign in campaign_data["data"]:
            if campaign["id"] == campaign_id:
                return jsonify({"data": campaign})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
