from status import recstat
from settings_local import *


def upload(stop_semaphore, lock, instructions, s):
    import soundcloud
    import os

    s.value = recstat.IDLE

    soundcloud_client = soundcloud.Client(client_id=SOUNDCLOUD_CLIENT_ID,
                                          client_secret=SOUNDCLOUD_CLIENT_SECRET,
                                          username=SOUNDCLOUD_USERNAME,
                                          password=SOUNDCLOUD_PASSWORD, )

    while(stop_semaphore.value < 2):
        instruction = instructions.recv()

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
