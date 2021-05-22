# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    abort,
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from logging import Formatter, FileHandler
from forms import *
from flask_migrate import Migrate
from operator import itemgetter
import re
import logging

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

from models import *

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, _format="medium"):
    date = dateutil.parser.parse(value)
    if _format == "full":
        _format = "EEEE MMMM, d, y 'at' h:mma"
    elif _format == "medium":
        _format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, _format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    """Lists all venues in record."""

    all_venues = Venue.query.all()

    data = []

    cities_states = set()
    for venue in all_venues:
        cities_states.add((venue.city, venue.state))

    cities_states = list(cities_states)
    cities_states.sort(key=itemgetter(1, 0))

    now = datetime.now()

    for loc in cities_states:
        venues_list = []
        for venue in all_venues:
            if (venue.city == loc[0]) and (venue.state == loc[1]):

                venue_shows = Show.query.filter_by(venue_id=venue.id).all()
                num_upcoming = 0
                for show in venue_shows:
                    if show.start_time > now:
                        num_upcoming += 1

                venues_list.append(
                    {
                        "id": venue.id,
                        "name": venue.name,
                        "num_upcoming_shows": num_upcoming,
                    }
                )

        data.append({"city": loc[0], "state": loc[1], "venues": venues_list})
    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    """Retrieves venue records based on a substring as venue name."""

    search_term = request.form.get("search_term", "").strip()

    all_venues = Venue.query.filter(
        Venue.name.ilike(
            "%" + search_term + "%")).all()
    venue_list = []
    now = datetime.now()
    for venue in all_venues:
        venue_shows = Show.query.filter_by(venue_id=venue.id).all()
        num_upcoming = 0
        for show in venue_shows:
            if show.start_time > now:
                num_upcoming += 1

        venue_list.append({"id": venue.id, "name": venue.name,
                           "num_upcoming_shows": num_upcoming})

    response = {"count": len(all_venues), "data": venue_list}

    return render_template(
        "pages/search_venues.html", results=response, search_term=search_term
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    """Shows detailed info of a particular venue using it's id."""

    venue = Venue.query.get(venue_id)
    if not venue:
        return redirect(url_for("index"))
    else:
        genres = [genre.name for genre in venue.genres]

        past_shows = []
        upcoming_shows = []
        now = datetime.now()

        past = (
            db.session.query(Show) .filter(
                Show.venue_id == venue_id) .filter(
                Show.start_time < now) .join(
                Artist,
                Show.artist_id == Artist.id) .add_columns(
                    Artist.id,
                    Artist.name,
                    Artist.image_link,
                Show.start_time) .all())
        for i in past:
            past_shows.append(
                {
                    "artist_id": i[1],
                    "artist_name": i[2],
                    "artist_image_link": i[3],
                    "start_time": str(i[4]),
                }
            )
        past_shows_count = len(past)

        upcoming = (
            db.session.query(Show) .filter(
                Show.venue_id == venue_id) .filter(
                Show.start_time > now) .join(
                Artist,
                Show.artist_id == Artist.id) .add_columns(
                    Artist.id,
                    Artist.name,
                    Artist.image_link,
                Show.start_time) .all())
        for i in upcoming:
            upcoming_shows.append(
                {
                    "artist_id": i[1],
                    "artist_name": i[2],
                    "artist_image_link": i[3],
                    "start_time": str(i[4]),
                }
            )
        upcoming_shows_count = len(upcoming)

        data = {
            "id": venue_id,
            "name": venue.name,
            "genres": genres,
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": (venue.phone[:3] + "-" + venue.phone[3:6] + "-" + venue.phone[6:]),
            "website": venue.website,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description,
            "image_link": venue.image_link,
            "past_shows": past_shows,
            "past_shows_count": past_shows_count,
            "upcoming_shows": upcoming_shows,
            "upcoming_shows_count": upcoming_shows_count,
        }

    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    """Create a venue landing form."""

    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    """Upon submission, inserts a new venue record."""

    try:
        error_in_insert = False
        name = request.form.get("name")
        city = request.form.get("city")
        state = request.form.get("state")
        address = request.form.get("address")
        phone = request.form.get("phone")
        phone = re.sub(r"\D", "", phone)
        genres = request.form.getlist("genres")
        facebook_link = request.form.get("facebook_link")

        seeking_talent = True if "seeking_talent" in request.form else False
        seeking_description = request.form.get("seeking_description")
        image_link = request.form.get("image_link")
        website = request.form.get("website_link")

        new_venue = Venue(
            name=name,
            city=city,
            state=state,
            address=address,
            phone=phone,
            seeking_talent=seeking_talent,
            seeking_description=seeking_description,
            image_link=image_link,
            website=website,
            facebook_link=facebook_link,
        )
        for genre in genres:
            fetch_genre = Genre.query.filter_by(name=genre).one_or_none()
            if fetch_genre:
                new_venue.genres.append(fetch_genre)

            else:
                new_genre = Genre(name=genre)
                db.session.add(new_genre)
                new_venue.genres.append(new_genre)

        db.session.add(new_venue)
        db.session.commit()
    except Exception as e:
        error_in_insert = True
        logger.error("Exception in create_venue_submission(): ")
        logger.error(e)
        db.session.rollback()
    finally:
        db.session.close()

    if not error_in_insert:
        flash(f"Venue {request.form['name']} was successfully listed!")
        return redirect(url_for("index"))
    else:
        flash("An error occurred. Venue {name} could not be listed.")
        logger.error("Error in create_venue_submission()")
        abort(500)


#  Update Venue
#  ----------------------------------------------------------------


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    """Edit a venue landing form. Populates the fields with existing data."""

    venue = Venue.query.get(venue_id)
    if not venue:
        return redirect(url_for("index"))
    else:
        form = VenueForm(obj=venue)

    genres = [genre.name for genre in venue.genres]

    venue = {
        "id": venue_id,
        "name": venue.name,
        "genres": genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": (venue.phone[:3] + "-" + venue.phone[3:6] + "-" + venue.phone[6:]),
        "website_link": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
    }
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    """Upon submission, updates the venue record."""

    name = ""
    try:
        error_in_update = False
        name = request.form.get("name")
        city = request.form.get("city")
        state = request.form.get("state")
        address = request.form.get("address")
        phone = request.form.get("phone")
        phone = re.sub(r"\D", "", phone)
        genres = request.form.getlist("genres")
        facebook_link = request.form.get("facebook_link")

        seeking_talent = True if "seeking_talent" in request.form else False
        seeking_description = request.form.get("seeking_description")
        image_link = request.form.get("image_link")
        website = request.form.get("website_link")

        venue = Venue.query.get(venue_id)
        venue.name = name
        venue.city = city
        venue.state = state
        venue.address = address
        venue.phone = phone

        venue.seeking_talent = seeking_talent
        venue.seeking_description = seeking_description
        venue.image_link = image_link
        venue.website = website
        venue.facebook_link = facebook_link

        venue.genres = []
        for genre in genres:
            fetch_genre = Genre.query.filter_by(name=genre).one_or_none()
            if fetch_genre:
                venue.genres.append(fetch_genre)

            else:
                new_genre = Genre(name=genre)
                db.session.add(new_genre)
                venue.genres.append(new_genre)

        db.session.commit()
    except Exception as e:
        error_in_update = True
        logger.error("Exception in edit_venue_submission(): ")
        logger.error(e)
        db.session.rollback()
    finally:
        db.session.close()

    if not error_in_update:
        flash(f"Venue {request.form['name']} was successfully updated!")
        return redirect(url_for("show_venue", venue_id=venue_id))
    else:
        flash(f"An error occurred. Venue {name} could not be updated.")
        logger.error("Error in edit_venue_submission()")
        abort(500)


#  ----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------


@app.route("/artists")
def artists():
    """Lists all artists in record."""

    all_artists = Artist.query.order_by(Artist.name).all()

    data = []
    for artist in all_artists:
        data.append({"id": artist.id, "name": artist.name})

    return render_template("pages/artists.html", artists=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    """Retrieves artist records based on a substring as artist name."""

    search_term = request.form.get("search_term", "").strip()

    all_artists = Artist.query.filter(
        Artist.name.ilike(
            "%" + search_term + "%")).all()
    artist_list = []
    now = datetime.now()
    for artist in all_artists:
        artist_shows = Show.query.filter_by(artist_id=artist.id).all()
        num_upcoming = 0
        for show in artist_shows:
            if show.start_time > now:
                num_upcoming += 1

        artist_list.append({"id": artist.id,
                            "name": artist.name,
                            "num_upcoming_shows": num_upcoming})

    response = {"count": len(all_artists), "data": artist_list}

    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    """Shows detailed info of a particular artist using it's id."""

    artist = Artist.query.get(artist_id)
    if not artist:
        return redirect(url_for("index"))
    else:
        genres = [genre.name for genre in artist.genres]

        past_shows = []
        upcoming_shows = []
        now = datetime.now()

        past = (
            db.session.query(Show) .filter(
                Show.artist_id == artist_id) .filter(
                Show.start_time < now) .join(
                Venue,
                Show.venue_id == Venue.id) .add_columns(
                    Venue.id,
                    Venue.name,
                    Venue.image_link,
                Show.start_time) .all())
        for i in past:
            past_shows.append(
                {
                    "venue_id": i[1],
                    "venue_name": i[2],
                    "venue_image_link": i[3],
                    "start_time": str(i[4]),
                }
            )
        past_shows_count = len(past)

        upcoming = (
            db.session.query(Show) .filter(
                Show.artist_id == artist_id) .filter(
                Show.start_time > now) .join(
                Venue,
                Show.venue_id == Venue.id) .add_columns(
                    Venue.id,
                    Venue.name,
                    Venue.image_link,
                Show.start_time) .all())
        for i in upcoming:
            upcoming_shows.append(
                {
                    "venue_id": i[1],
                    "venue_name": i[2],
                    "venue_image_link": i[3],
                    "start_time": str(i[4]),
                }
            )
        upcoming_shows_count = len(upcoming)

        data = {
            "id": artist_id,
            "name": artist.name,
            "genres": genres,
            "city": artist.city,
            "state": artist.state,
            "phone": (
                artist.phone[:3] + "-" + artist.phone[3:6] + "-" + artist.phone[6:]
            ),
            "website": artist.website,
            "facebook_link": artist.facebook_link,
            "seeking_venue": artist.seeking_venue,
            "seeking_description": artist.seeking_description,
            "image_link": artist.image_link,
            "past_shows": past_shows,
            "past_shows_count": past_shows_count,
            "upcoming_shows": upcoming_shows,
            "upcoming_shows_count": upcoming_shows_count,
        }

    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    """Edit an artist landing form. Populates the fields with existing data."""

    artist = Artist.query.get(artist_id)

    if not artist:
        return redirect(url_for("index"))
    else:
        form = ArtistForm(obj=artist)

    genres = [genre.name for genre in artist.genres]

    artist = {
        "id": artist_id,
        "name": artist.name,
        "genres": genres,
        "city": artist.city,
        "state": artist.state,
        "phone": (artist.phone[:3] + "-" + artist.phone[3:6] + "-" + artist.phone[6:]),
        "website_link": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
    }

    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    """Upon submission, updates the artist record."""

    name = ""
    try:
        error_in_update = False
        name = request.form.get("name")
        city = request.form.get("city")
        state = request.form.get("state")
        phone = request.form.get("phone")
        phone = re.sub(r"\D", "", phone)
        genres = request.form.getlist("genres")
        facebook_link = request.form.get("facebook_link")

        seeking_venue = True if "seeking_venue" in request.form else False
        seeking_description = request.form.get("seeking_description")
        image_link = request.form.get("image_link")
        website = request.form.get("website_link")

        artist = Artist.query.get(artist_id)
        artist.name = name
        artist.city = city
        artist.state = state
        artist.phone = phone

        artist.seeking_venue = seeking_venue
        artist.seeking_description = seeking_description
        artist.image_link = image_link
        artist.website = website
        artist.facebook_link = facebook_link
        artist.genres = []

        for genre in genres:
            fetch_genre = Genre.query.filter_by(name=genre).one_or_none()
            if fetch_genre:
                artist.genres.append(fetch_genre)

            else:
                new_genre = Genre(name=genre)
                db.session.add(new_genre)
                artist.genres.append(new_genre)

        db.session.commit()

    except Exception as e:
        error_in_update = True
        logger.error("Exception in edit_artist_submission()")
        logger.error(e)
        db.session.rollback()
    finally:
        db.session.close()

    if not error_in_update:
        flash(f"Artist {request.form['name']} was successfully updated!")
        return redirect(url_for("show_artist", artist_id=artist_id))
    else:
        flash(f"An error occurred. Artist {name} could not be updated.")
        logger.error("Error in edit_artist_submission()")
        abort(500)


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    """Create an artist landing form."""

    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    """Upon submission, inserts a new artist record."""

    name = ""
    try:
        error_in_insert = False
        name = request.form.get("name")
        city = request.form.get("city")
        state = request.form.get("state")
        phone = request.form.get("phone")
        phone = re.sub(r"\D", "", phone)
        genres = request.form.getlist("genres")
        facebook_link = request.form.get("facebook_link")

        seeking_venue = True if "seeking_venue" in request.form else False
        seeking_description = request.form.get("seeking_description")
        image_link = request.form.get("image_link")
        website = request.form.get("website_link")

        new_artist = Artist(
            name=name,
            city=city,
            state=state,
            phone=phone,
            seeking_venue=seeking_venue,
            seeking_description=seeking_description,
            image_link=image_link,
            website=website,
            facebook_link=facebook_link,
        )

        for genre in genres:
            fetch_genre = Genre.query.filter_by(name=genre).one_or_none()
            if fetch_genre:
                new_artist.genres.append(fetch_genre)

            else:
                new_genre = Genre(name=genre)
                db.session.add(new_genre)
                new_artist.genres.append(new_genre)

        db.session.add(new_artist)
        db.session.commit()

    except Exception as e:
        error_in_insert = True
        logger.error("Exception in create_artist_submission()")
        logger.error(e)
        db.session.rollback()
    finally:
        db.session.close()

    if not error_in_insert:
        flash(f"Artist {request.form['name']} was successfully listed!")
        return redirect(url_for("index"))
    else:
        flash(f"An error occurred. Artist {name} could not be listed.")
        logger.error("Error in create_artist_submission()")
        abort(500)


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    """Lists all shows in record."""

    data = []
    all_shows = Show.query.all()

    for show in all_shows:
        venue = Venue.query.get(show.venue_id)
        artist = Artist.query.get(show.artist_id)
        data.append(
            {
                "venue_id": show.venue_id,
                "venue_name": venue.name,
                "artist_id": show.artist_id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": format_datetime(str(show.start_time)),
            }
        )
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    """Create a show landing form."""

    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    """Upon submission, inserts a new show record."""

    errors = {"invalid_artist_id": False, "invalid_venue_id": False}

    try:
        artist_id = request.form.get("artist_id")
        venue_id = request.form.get("venue_id")
        start_time = request.form.get("start_time")

        found_artist = Artist.query.get(artist_id)
        if found_artist is None:
            errors["invalid_artist_id"] = True

        found_venue = Venue.query.get(venue_id)
        if found_venue is None:
            errors["invalid_venue_id"] = True

        if found_venue is not None and found_artist is not None:
            new_show = Show(
                start_time=start_time, artist_id=artist_id, venue_id=venue_id
            )
            db.session.add(new_show)
            db.session.commit()

    except Exception as e:
        logger.error("Exception in create_show_submission()")
        logger.error(e)
        db.session.rollback()
    finally:
        db.session.close()

    if errors["invalid_artist_id"]:
        flash("Invalid artist id! Check again.")
        logger.error("Error in create_show_submission()")
    elif errors["invalid_venue_id"]:
        flash("Invalid venue id! Check again.")
        logger.error("Error in create_show_submission()")
    else:
        flash("Show was successfully listed!")

    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
