import os

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session

# Configure application
app = Flask(__name__)

# Sessions are signed with this key. Set SECRET_KEY in your environment for
# anything you deploy. If it is missing, a random key is generated at startup
# (fine for local play, but everyone's session resets whenever the app restarts).
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///info.db")

# Game state is stored in the session (one private copy per player), not in
# module-level globals, which Flask shares between every visitor. Keys used:
#   location_id         id of the room the player is in
#   choice              the option the player picked in that room (1-4)
#   just_entered        True right after moving rooms, False after an action
#   correct_accusation  False as soon as any accusation pick is wrong
#   error_message, redirect_link   what the error page shows


def fail(message, link):
    """Send the player to the error page, remembering where 'back' should go."""
    session["error_message"] = message
    session["redirect_link"] = link
    return redirect("/error")


@app.route("/")
def index():
    """Start a new game: clear any old progress, then show the homepage"""
    session.clear()
    session["correct_accusation"] = True
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

    if request.method == "POST":
        try:
            location_id = int(request.form.get("location"))
        except (TypeError, ValueError):
            return fail("Something went wrong.", "/location-change")

        # Make sure the chosen location actually exists
        if not db.execute("SELECT id FROM set_1 WHERE id = ?", location_id):
            return fail("Something went wrong.", "/location-change")

        # Save location to this player's session and go to the next page
        session["location_id"] = location_id
        session["just_entered"] = True
        return redirect("/location")

    locations = db.execute("SELECT location FROM set_1 ORDER BY id")
    loc_1 = locations[0]["location"]
    loc_2 = locations[1]["location"]
    loc_3 = locations[2]["location"]

    return render_template("location-change.html", loc_1=loc_1, loc_2=loc_2, loc_3=loc_3)


@app.route("/location", methods=["GET", "POST"])
def location():
    """Inside location."""

    # Player has not picked a room yet (e.g. typed /location into the address bar)
    if "location_id" not in session:
        return redirect("/location-change")

    if request.method == "POST":
        try:
            choice = int(request.form.get("option"))
        except (TypeError, ValueError):
            return fail("Something went wrong.", "/location")

        # Only options 1-4 exist
        if choice not in (1, 2, 3, 4):
            return fail("Something went wrong.", "/location")

        if choice == 4:
            return redirect("/accuse-suspect")
        elif choice == 3:
            return redirect("/location-change")

        # Options 1 and 2 are the actions available in the room
        session["choice"] = choice
        return redirect("/response")

    # Enter table for location, and find the options
    info = db.execute(
        "SELECT location, description, option_1, option_2 FROM set_1 WHERE id = ?",
        session["location_id"],
    )
    if not info:
        return redirect("/location-change")

    name = info[0]["location"]
    desc = "You enter the " + name.lower() + ". " + info[0]["description"]
    opt_1 = info[0]["option_1"]
    opt_2 = info[0]["option_2"]

    # If the player already did something here, don't repeat the room description
    if session.get("just_entered", True) is False:
        desc = "You're still in the " + name.lower() + "."

    return render_template("location.html", name=name, desc=desc, opt_1=opt_1, opt_2=opt_2)


@app.route("/response")
def response():
    """Result of user's choice."""

    # Player has not picked a room and an action yet
    if "location_id" not in session or "choice" not in session:
        return redirect("/location-change")

    session["just_entered"] = False

    # Enter table for location, and find the response
    info = db.execute(
        "SELECT response_1, response_2 FROM set_1 WHERE id = ?",
        session["location_id"],
    )
    if not info:
        return redirect("/location-change")

    if session["choice"] == 1:
        response = info[0]["response_1"]
    else:
        response = info[0]["response_2"]

    return render_template("response.html", response=response)


@app.route("/accuse-suspect", methods=["GET", "POST"])
def accuse_suspect():
    """User chooses the suspect they think was part of the murder"""

    if request.method == "POST":
        suspect = request.form.get("suspect")

        if not suspect:
            return fail("Something went wrong.", "/accuse-suspect")

        if suspect == "incorrect":
            session["correct_accusation"] = False

        return redirect("/accuse-weapon")

    # Starting a fresh accusation, so wipe any result left over from an earlier one
    session["correct_accusation"] = True
    return render_template("accuse-suspect.html")


@app.route("/accuse-weapon", methods=["GET", "POST"])
def accuse_weapon():
    """User chooses the weapon they think was part of the murder"""

    if request.method == "POST":
        weapon = request.form.get("weapon")

        if not weapon:
            return fail("Something went wrong.", "/accuse-weapon")

        if weapon == "incorrect":
            session["correct_accusation"] = False

        return redirect("/accuse-location")

    return render_template("accuse-weapon.html")


@app.route("/accuse-location", methods=["GET", "POST"])
def accuse_location():
    """User chooses the location they think was part of the murder"""

    if request.method == "POST":
        location = request.form.get("location")

        if not location:
            return fail("Something went wrong.", "/accuse-location")

        if location == "incorrect":
            session["correct_accusation"] = False

        if session.get("correct_accusation", True):
            return redirect("/winner")
        return redirect("/loser")

    locations = db.execute("SELECT location FROM set_1 ORDER BY id")
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
    return render_template(
        "error.html",
        error_message=session.get("error_message", "Something went wrong."),
        redirect_link=session.get("redirect_link", "/"),
    )
