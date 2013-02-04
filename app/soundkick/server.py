from multiprocessing import Process, Value, Lock, Pipe
import signal
import json
import cgi
import time

from twisted.web import server, resource
from twisted.internet import reactor

from status import serstat, recstat
from record import record
from upload import upload

from settings_local import *


class HTTPListener(resource.Resource):
    isLeaf = True
    numberRequests = 0

    def __init__(self, stop_semaphore, lock, recording_pipe, recording_status, uploading_status):
        self.stop_semaphore = stop_semaphore
        self.lock = lock
        self.recording_pipe = recording_pipe
        self.recording_status = recording_status
        self.uploading_status = uploading_status

    def render_GET(self, request):
        self.numberRequests += 1
        request.setHeader("content-type", "application/json")
        return json.dumps({'request_num': self.numberRequests,
                'recording_status': self.recording_status.value,
                'uploading_status': self.uploading_status.value, })

    def render_POST(self, request):
        self.numberRequests += 1
        request.setHeader("content-type", "application/json")

        command = {'status': 0}
        for k, v in request.args.items():
            command[k] = cgi.escape(v[0])

        if "command" not in command:
            command['status'] = serstat.ERROR
        elif command['command'] == "record" and self.recording_status.value == recstat.IDLE:
            self.recording_pipe.send(command)
            command['status'] = serstat.OK
        elif command['command'] == "record":
            command['status'] = serstat.ERROR
        elif command['command'] == "stop" and self.recording_status.value != recstat.IDLE:
            stop_semaphore.value = 1
        elif command['command'] == "stop":
            command['status'] = serstat.ERROR
        elif command['command'] == "shutdown":
            print("would shutdown")
        else:
            command['status'] = serstat.NOT_UNDERSTOOD

        return json.dumps({'request_num': self.numberRequests,
                           'recording_status': self.recording_status.value,
                           'uploading_status': self.uploading_status.value,
                           'command': command,
                          })

if __name__ == '__main__':
    stop_semaphore = Value('i', 0)
    lock = Lock()
    recording_status = Value('i', 0)
    uploading_status = Value('i', 0)
    recording_parent_conn, recording_child_conn = Pipe()
    uploading_parent_conn, uploading_child_conn = Pipe()
    recording_process = Process(target=record, args=(stop_semaphore, lock, recording_child_conn, recording_status, uploading_parent_conn))
    uploading_process = Process(target=upload, args=(stop_semaphore, lock, uploading_child_conn, uploading_status))

    # define and set our signal handlers
    def signal_handler(signum, frame):
        print ("caught INT in %s" % __name__)
        lock.acquire()

        if stop_semaphore.value != 2 and __name__ == '__main__':
            stop_semaphore.value = 2
            reactor.stop()

        lock.release()
        time.sleep(2)
        # TODO send terminate signals to pipes to shutdown gracefully
        quit()


    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # fire up our processing threads
    recording_process.start()
    uploading_process.start()

    # start our HTTP listener
    reactor.listenTCP(8080, server.Site(HTTPListener(stop_semaphore=stop_semaphore,
                                                     lock=lock,
                                                     recording_pipe=recording_parent_conn,
                                                     recording_status=recording_status,
                                                     uploading_status=uploading_status)))
    reactor.run()

    # if we've fallen out of our HTTP listener, join recording and uploading processes when they complete
    recording_process.join()
    uploading_process.join()
