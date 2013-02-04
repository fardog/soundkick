from status import recstat
from settings_local import *


def record(stop_semaphore, lock, instructions, s, uploading_pipe):
    import datetime
    import uuid
    import pyaudio
    import wave

    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100

    s.value = recstat.IDLE

    while(stop_semaphore.value < 2):
        instruction = instructions.recv()
        s.value = recstat.PREPARING
        instruction['date'] = str(datetime.datetime.now())
        instruction['filename'] = MEDIA_PATH + str(uuid.uuid4()) + '.wav'

        if "artist" not in instruction:
            instruction['artist'] = u"NORTH"

        if "track" not in instruction:
            instruction['track'] = instruction['date']

        p = pyaudio.PyAudio()

        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        print("* recording")

        wf = wave.open(instruction['filename'], 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)

        s.value = recstat.RECORDING

        while(True):
            data = stream.read(CHUNK)
            wf.writeframes(data)
            if stop_semaphore.value > 0:
                lock.acquire()
                break

        print("* done recording")

        stream.stop_stream()
        stream.close()
        wf.close()
        p.terminate()
        s.value = recstat.IDLE
        if stop_semaphore.value == 1:
            stop_semaphore.value = 0
        lock.release()

        instruction['command'] = "upload"
        uploading_pipe.send(instruction)
