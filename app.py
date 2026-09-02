import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request

#from main.py import [function], [function]

# Configure application
app = Flask(__name__)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///info.db")

# Global variables
location_id = 0
choice = 0
error_message = ""
redirect_link = ""
just_entered = True
correct_accusation = True


@app.route("/")
def index():
    """Main game -- everything up to accusation"""
    global correct_accusation
    correct_accusation = True
    return render_template("homepage.html")


@app.route("/instructions")
def instructions():
    """How to play"""
    return render_template("instructions.html")


@app.route("/swl")
def swl():
    """All suspects, weapons, and locations"""
    return render_template("swl.html")


@app.route("/entered")
def entered():
    """Tells user they entered the mansion"""
    return render_template("entered.html")


@app.route("/location-change", methods=["GET", "POST"])
def location_change():
    """User picks which location they want to move to"""

    global location_id
    global error_message
    global redirect_link
    global just_entered

    if request.method == "POST":
        #save location to global variable
        location_id = request.form.get("location")

        try:
            location_id = int(location_id)
        except:
            error_message = "Something went wrong."
            redirect_link = "/location"
            return redirect("/error")

        #go to next page
        return redirect("/location")

    locations = db.execute("SELECT location FROM set_1")
    loc_1 = locations[0]["location"]
    loc_2 = locations[1]["location"]
    loc_3 = locations[2]["location"]

    just_entered = True

    return render_template("location-change.html", loc_1=loc_1, loc_2=loc_2, loc_3=loc_3)


@app.route("/location", methods=["GET", "POST"])
def location():
    """Inside location."""

    global choice
    global error_message
    global redirect_link

    if request.method == "POST":
        #save location to global variable
        choice = request.form.get("option")

        try:
            choice = int(choice)
        except:
            error_message = "Something went wrong."
            redirect_link = "/location"
            return redirect("/error")

        if choice == 4:
            return redirect("/accuse-suspect")
        elif choice == 3:
            return redirect("/location-change")
        else:
            return redirect("/response") #safeguard this against malicious users who place a different value other than 1-4

    #enter table for location, and find the options
    info = db.execute("SELECT location, description, option_1, option_2 FROM set_1 WHERE id IS ?", location_id)

    name = info[0]["location"]
    desc = "You enter the " + name.lower() + ". " + info[0]["description"]
    opt_1 = info[0]["option_1"]
    opt_2 = info[0]["option_2"]

    #variable "first" for if the user just entered (came from loc_change or not (came from response)) -- if not, get rid of desc and say "you're still in the {{loc}}"
    if just_entered == False:
        desc = "You're still in the " + name.lower() + "."

    #redirect to error w/ 404 or something message if user accesses /location before /location-change

    #send location name and rsos to render template
    return render_template("location.html", name=name, desc=desc, opt_1=opt_1, opt_2=opt_2)


@app.route("/response")
def response():
    """Result of user's choice."""
    global just_entered

    just_entered = False

    #enter table for location, and find the response
    info = db.execute("SELECT response_1, response_2 FROM set_1 WHERE id IS ?", location_id)

    if choice == 1:
        response = info[0]["response_1"]
    else: #protect against inspect later
        response = info[0]["response_2"]

    return render_template("response.html", response=response)


@app.route("/accuse-suspect", methods=["GET", "POST"])
def accuse_suspect():
    """User chooses the suspect they think was part of the murder"""
    global correct_accusation
    global error_message
    global redirect_link

    if request.method == "POST":
        suspect = request.form.get("suspect")

        if not suspect:
            error_message = "Something went wrong."
            redirect_link = "/accuse-suspect"
            return redirect("/error")

        if suspect == "incorrect":
            correct_accusation = False

        return redirect("/accuse-weapon")

    return render_template("accuse-suspect.html")


@app.route("/accuse-weapon", methods=["GET", "POST"])
def accuse_weapon():
    """User chooses the weapon they think was part of the murder"""
    global correct_accusation
    global error_message
    global redirect_link

    if request.method == "POST":
        weapon = request.form.get("weapon")

        if not weapon:
            error_message = "Something went wrong."
            redirect_link = "/accuse-weapon"
            return redirect("/error")

        if weapon == "incorrect":
            correct_accusation = False

        return redirect("/accuse-location")

    return render_template("accuse-weapon.html")


@app.route("/accuse-location", methods=["GET", "POST"])
def accuse_location():
    """User chooses the location they think was part of the murder"""
    global correct_accusation
    global error_message
    global redirect_link

    if request.method == "POST":
        location = request.form.get("location")

        if not location:
            error_message = "Something went wrong."
            redirect_link = "/accuse-location"
            return redirect("/error")

        if location == "incorrect":
            correct_accusation = False

        if correct_accusation == True:
            return redirect("/winner")
        return redirect("/loser")

    locations = db.execute("SELECT location FROM set_1")
    loc_1 = locations[0]["location"]
    loc_2 = locations[1]["location"]
    loc_3 = locations[2]["location"]

    return render_template("accuse-location.html", loc_1=loc_1, loc_2=loc_2, loc_3=loc_3)


@app.route("/winner")
def winner():
    """Winning screen"""
    return render_template("winner.html")


@app.route("/loser")
def loser():
    """Losing screen"""
    return render_template("loser.html")


@app.route("/error")
def error():
    """Error screen"""
    return render_template("error.html", error_message=error_message, redirect_link=redirect_link)



""" LEGACY
@app.route("/final-accusation", methods=["GET", "POST"])
def final_accusation():
    #User makes their final accusation
    global error_message
    global redirect_link

    if request.method == "POST":
        suspect = request.form.get("suspect")
        weapon = request.form.get("weapon")
        location = request.form.get("location")

        if not suspect or not weapon or not location:
            error_message = "Your accusation was incomplete!"
            redirect_link = "/final-accusation"
            return redirect("/error")
        if suspect == "correct" and weapon == "correct" and location == "correct":
            return redirect("/winner")
        return redirect("/loser")
    return render_template("final-accusation.html")
"""
