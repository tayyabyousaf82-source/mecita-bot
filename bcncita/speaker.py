import os
from shutil import which


class eSpeakSpeaker:
    @classmethod
    def is_applicable(cls):
        return which("espeak") is not None

    def say(self, phrase):
        os.system("espeak '" + phrase + "'")


class saySpeaker:
    @classmethod
    def is_applicable(cls):
        return which("say") is not None

    def say(self, phrase):
        os.system("say '" + phrase + "'")


class wSaySpeaker:
    @classmethod
    def is_applicable(cls):
        return which("wsay") is not None

    def say(self, phrase):
        os.system('wsay "' + phrase + '"')


class SilentSpeaker:
    """No-op speaker for headless/server environments (e.g. Railway, Docker)."""

    @classmethod
    def is_applicable(cls):
        return True

    def say(self, phrase):
        pass  # silent


def new_speaker():
    for cls in [eSpeakSpeaker, saySpeaker, wSaySpeaker, SilentSpeaker]:
        if cls.is_applicable():
            return cls()
