from flask import session

class User:
    def __init__(self):
        self.target_view = dict()

    def save_target_view(self, target_view):
        self.target_view[session.get('uuid')] = target_view

    def get_target_view(self):
        return self.target_view[session.get('uuid')]