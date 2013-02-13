from status import recstat
import signal
from settings_local import *


def upload(stop_semaphore, lock, instructions, s):
    import soundcloud
    import os

    s.value = recstat.IDLE

    signal.signal(signal.SIGINT, signal.SIG_IGN)

    soundcloud_client = soundcloud.Client(client_id=SOUNDCLOUD_CLIENT_ID,
                                          client_secret=SOUNDCLOUD_CLIENT_SECRET,
                                          username=SOUNDCLOUD_USERNAME,
                                          password=SOUNDCLOUD_PASSWORD, )

    while(stop_semaphore.value < 2):
        instruction = instructions.recv()

        #if we get a kill signal, die
        if type(instruction) is str and instruction == "kill":
            print("[%s]: Caught kill instruction, dying." % __name__)
            return

        s.value = recstat.UPLOADING
        print("* uploading")

        try:
            track = soundcloud_client.post('/tracks', track={
                                           'title': SOUNDCLOUD_TITLE_LEADER + instruction['artist'] + " - " + instruction['track'],
                                           'asset_data': open(instruction['filename'], 'rb')
                                           })
            print track.permalink_url
        except Exception, e:
            print("* exception occurred while uploading, message was: " + str(e))
        else:
            os.unlink(instruction['filename'])

        print("* done uploading")
        s.value = recstat.IDLE
