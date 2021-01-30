import os
import random
import secrets
from copy import deepcopy
import uuid
import spotipy

from flask import render_template, redirect, url_for, flash, session
from flask.globals import request
from spotipy.exceptions import SpotifyException

import musicrecs.random_words.random_words as random_words

from musicrecs import app
from musicrecs import db
from musicrecs import spotify_iface
from musicrecs import spotify_user
from musicrecs.sql_models import Submission, Round
from musicrecs.forms import NewRoundForm, TrackrecForm, AlbumrecForm
from musicrecs.enums import RoundStatus, MusicType
from musicrecs.exceptions import UserError, InternalError
from musicrecs.spotify.user_spotify import SpotifyUser



'''ROUTES'''


@app.route('/', methods=('GET', 'POST'))
@app.route('/index', methods=('GET', 'POST'))
def index():
    new_round_form = NewRoundForm()

    try:
        if new_round_form.validate_on_submit():
            # Get the new_round_form fields
            description = new_round_form.description.data
            music_type = new_round_form.music_type.data
            snoozin_rec_type = new_round_form.snoozin_rec_type.data

            # Add the round to the database
            new_round = Round(
                description=description,
                music_type=music_type,
                snoozin_rec_type=snoozin_rec_type,
                long_id=secrets.token_urlsafe(16)
            )
            db.session.add(new_round)
            db.session.commit()

            # Go to the page for the new round
            return redirect(url_for('round', long_id=new_round.long_id))

        elif new_round_form.errors:
            raise InternalError(new_round_form.errors)

    except UserError as e:
        flash(e, "warning")
    except InternalError as e:
        flash(e, "danger")

    return render_template('index.html', new_round_form=new_round_form, target_view='sp')


@app.route('/round/<string:long_id>', methods=["GET", "POST"])
def round(long_id):
    # Get the round from the long id
    round = Round.query.filter_by(long_id=long_id).first()

    # Get the recommendation form
    if round.music_type == MusicType.album:
        rec_form = AlbumrecForm()
    elif round.music_type == MusicType.track:
        rec_form = TrackrecForm()
    else:
        raise Exception(f"Unknown music type {round.music_type}")

    if round.status == RoundStatus.submit:
        return render_template('round/submit_phase.html',
                               rec_form=rec_form,
                               round=round)
    elif round.status == RoundStatus.listen or round.status == RoundStatus.revealed:
        submission_list = deepcopy(round.submissions)
        random.shuffle(submission_list)
        music_submissions = {
            submission.user_name: spotify_iface.get_music_from_link(
                round.music_type.name, submission.spotify_link
            ) for submission in submission_list
        }
        return render_template('round/listen_phase.html',
                               music_submissions=music_submissions,
                               round=round,
                               revealed=RoundStatus.revealed)


@app.route('/round/<string:long_id>/advance', methods=['POST'])
def round_advance(long_id):
    # Get the round from the long id
    round = Round.query.filter_by(long_id=long_id).first()

    # Perform actions that are round phase transition specific
    if 'advance_to_listen' in request.form:
        try:
            # Add snoozin's rec:
            new_submission = Submission(
                spotify_link=_get_snoozin_rec(round),
                user_name="snoozin",
                round_id=round.id,
            )
            db.session.add(new_submission)

            # Advance to 'listen' phase
            round.status = RoundStatus.listen

            db.session.commit()
        except UserError as e:
            flash(e, "warning")
        except InternalError as e:
            flash(e, "danger")
    elif 'advance_to_revealed' in request.form:
        round.status = RoundStatus.revealed
        db.session.commit()

    # Go back to the round page
    return redirect(url_for('round', long_id=long_id))


@app.route('/round/<string:long_id>/submit_rec', methods=['POST'])
def round_submit_rec(long_id):
    # Get the round from the long id
    round = Round.query.filter_by(long_id=long_id).first()

    # Get the correct recommendation form
    if round.music_type == MusicType.album:
        rec_form = AlbumrecForm()
    elif round.music_type == MusicType.track:
        rec_form = TrackrecForm()
    else:
        raise Exception(f"Unknown music type {round.music_type}")

    try:
        # Process the music recommendation
        if rec_form.validate_on_submit():
            # Get the rec_form fields
            user_name = rec_form.name.data
            spotify_link = rec_form.spotify_link.data

            # Verify form info
            if _spotify_link_invalid(round.music_type, spotify_link):
                raise UserError(f"Invalid spotify {round.music_type.name} link")
            elif _user_name_taken(user_name, round.submissions):
                raise UserError(f"The name \"{user_name}\" is taken already for this round!")
            elif user_name == "snoozin":
                raise UserError("This town's only big enough for one snoozin...")

            # Add the submission to the database
            new_submission = Submission(
                spotify_link=spotify_link,
                user_name=user_name,
                round_id=round.id,
            )
            db.session.add(new_submission)
            db.session.commit()

            # Alert the user that the form was successfully submitted
            flash("Successfully submitted your recommendation: "
                  f"{_get_music_name_and_artists(round.music_type, spotify_link)}",
                  "success")

            # Reload the round page
            return redirect(url_for('round', long_id=long_id))

        elif rec_form.errors:
            raise InternalError(rec_form.errors)

    except UserError as e:
        flash(e, "warning")
    except InternalError as e:
        flash(e, "danger")

    # Retain form entries when there was a mistake in the submission
    return render_template('round/submit_phase.html',
                           rec_form=rec_form,
                           round=round)


@app.route('/sp_login', methods=['POST'])
def sp_login():
    target_view = 'sp'
    # Create session id for new users
    if not session.get('uuid'):
        print("visitor is unknown")
        session['uuid'] = str(uuid.uuid4())

    auth_result, auth_manager = spotify_user.check_user_auth()

    if auth_result:
        return redirect(url_for(target_view))
    else:
        spotify_user.save_target_view(target_view)
        return redirect(auth_manager.get_authorize_url())


@app.route('/sp_login_success')
def sp_login_success():
    spotify_user.auth_new_user(request.args.get("code"))
    return redirect(url_for(spotify_user.get_target_view()))

@app.route('/sp')
def sp():
    if 'get_current_track' in request.form:
        print(spotify_user.get_current_track())

    return render_template('sp/sp.html')


'''PRIVATE FUNCTIONS'''


def _get_music_name_and_artists(music_type: MusicType, spotify_link: str):
    if not _spotify_link_invalid(music_type, spotify_link):
        music = spotify_iface.get_music_from_link(music_type.name, spotify_link)
        return music.format("text")
    else:
        return ""


def _spotify_link_invalid(music_type: MusicType, spotify_link: str):
    try:
        spotify_iface.get_music_from_link(music_type.name, spotify_link)
        return False
    except SpotifyException:
        return True


def _user_name_taken(user_name, submissions):
    for submission in submissions:
        if submission.user_name == user_name:
            return True
    return False


def _get_snoozin_rec(round):
    snoozin_rec_link = None
    if round.snoozin_rec_type.name == "random":
        rw_gen = random_words.RandomWords()
        num_words = random.randint(1, 2)

        search_term = ""
        while snoozin_rec_link is None:
            search_term = " ".join(
                rw_gen.get_random_words(num_words)
            )
            snoozin_rec_link = spotify_iface.search_for_music(round.music_type.name, search_term)

        # Set the round's search term
        round.snoozin_rec_search_term = search_term
        db.session.commit()

    elif round.snoozin_rec_type.name == "similar":
        submitted_links = [submission.spotify_link for submission in round.submissions]
        snoozin_rec_link = spotify_iface.recommend_music(round.music_type.name, submitted_links)

    return snoozin_rec_link
