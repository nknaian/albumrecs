import random
import re
import time

import snoozingmail
import albumrecs.spotify.random_spotify as random_spotify


"""regex used to find spotify album link in message body of an email"""
ALBUM_LINK_RE = "https:\\/\\/open.spotify.com\\/album\\/.{22}"


class AlbumRecs:
    """Album recommendation manager class. Interfaces with
    gmail through snoozingmail to get recommendations from
    participants. Interfaces with spotify through spotipy to
    get a random album to add to the mix.
    """

    def __init__(self, gmail_credentials, group_name=None):
        self.album_recs = {}
        self.snoozin = snoozingmail.Snoozin(gmail_credentials)
        self.random_spotify = random_spotify.RandomSpotify()

        if group_name:
            self.GROUP_NAME = group_name
        else:
            self.GROUP_NAME = ""

        random.seed(time.time())

    def get_shuffled_participants(self):
        participants = []
        for participant in self.album_recs.keys():
            participants.append(participant)
        random.shuffle(participants)
        return participants

    def get_shuffled_album_recs(self):
        recs = []
        for rec in self.album_recs.values():
            recs.append(rec)
        random.shuffle(recs)
        return recs

    def send(self):
        # Set who the email will be sent to
        to = ""
        for participant in self.get_shuffled_participants():
            to += "{}; ".format(participant)

        # Set the subject of the email
        subject = "albumrecs"

        # Create the body of the email
        message_text = (
            "snoozin and {} present their latest albumrecs:\n\n"
        ).format(self.GROUP_NAME if self.GROUP_NAME != "" else "friends")

        for i, rec in enumerate(self.get_shuffled_album_recs()):
            message_text += "albumrec {}:\n{}\n".format(i+1, rec)

        # Send the email
        self.snoozin.send(to, subject, message_text)

    def add_from_gmail(self):
        # Find matching albumrec emails
        group_search = ":{}".format(self.GROUP_NAME)
        query = (
            "subject:albumrec{} AND is:unread AND in:inbox "
        ).format(group_search if self.GROUP_NAME != "" else "")

        msg_ids = self.snoozin.get_matching_msgs(query)

        # Add the newest album rec from each sender
        for msg_id in msg_ids:
            sender = self.snoozin.get_sender(msg_id)
            if sender not in self.album_recs:
                # Mark message as read
                self.snoozin.remove_msg_labels(msg_id, ['UNREAD'])

                # Add the spotify link from the message body to the album_recs
                message_body = self.snoozin.get_msg_body(msg_id)
                if message_body:
                    album_link_re = re.search(ALBUM_LINK_RE, message_body)
                    if album_link_re is None:
                        error_msg = (
                            "Error: spotify album link not found for "
                            "message: {} from: {}"
                        ).format(msg_id, sender)
                        print(error_msg)
                    else:
                        # Add sender's album_link to the album_recs
                        self.album_recs[sender] = album_link_re.group(0)

    def add_snoozin_rec(self):
        sender = "snoozinforabruisin@gmail.com"
        self.album_recs[sender] = self.random_spotify.get_random_album()