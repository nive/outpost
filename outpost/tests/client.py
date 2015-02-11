import requests
import json
import sys
import logging
import time

import multiprocessing

class ClientRunner(multiprocessing.Process):
    name = ""
    loops = 0
    delay = 0
    host = ""
    options = {}
    links = ()
    parameter = {}

    def run(self):
        self.stats = None
        log = logging.getLogger("client")
        #log.info("%s starting "%self.name)
        stats = []
        for i in range(self.loops):
            #log.info("%s loop #%02d"%(self.name,i+1))
            stats.append(self.linklist())
        #log.info("%s finished"%self.name)
        self._kwargs["result"].put(stats)

    def linklist(self):
        stats = []
        for link in self.links:
            stats.append(self.req(link))
        return stats

    def req(self, link):
        time.sleep(self.delay)
        url = self.host+link
        t = time.time()
        try:
            response = requests.request(self.options.get("method","GET"), url, **self.parameter)
            return (link,
                    response.status_code,
                    response.elapsed.microseconds/1000.0/1000.0,
                    len(response.content)+len(str(response.raw.headers)),
                    response.raw.tell(),
                    response.reason
            )
        except requests.exceptions.ConnectionError, e:
            return (link,
                    999,
                    time.time()-t,
                    0,
                    0,
                    str(e)
            )

def report(stats, runtime):
    total = 0
    ok = 0
    dl = 0
    errors = []
    files = {}
    sizes = {}
    for client in stats:
        for loop in client:
            total += len(loop)
            for req in loop:
                if 200<=req[1]<300:
                    ok += 1
                else:
                    errors.append(req)
                file = req[0]
                if not file in files:
                    files[file] = []
                files[file].append(req[2])
                dl += req[4]
                if not file in sizes:
                    sizes[file] = req[3]

    print
    print "Finished", total, "requests in", "%.04f"%runtime, "seconds"
    print "success: ", ok
    print "errors:  ", len(errors)
    print "download:", "%.04f"%(dl/1024.0/1000.0), "MB"
    print
    mlen = 10
    for file in files:
        if len(file)>mlen:
            mlen = len(file)
    for file in files:
        fl = files[file]
        print file, " "*(mlen-len(file)), "- avg", "%.04f"%(sum(fl)/len(fl)), " min", "%.04f"%min(fl), " max", "%.04f"%max(fl), " size", sizes[file]

    for err in errors:
        print err

    return


def run(links):
    logreq = logging.getLogger("requests.packages.urllib3.connectionpool")
    logreq.level = "error"
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("client")
    # set defaults
    loops = links.get("loops") or 5
    clients = links.get("clients") or 20
    delay = links.get("delay") or 0.0
    # get settings
    host = links["host"]
    if host.endswith("/"):
        host = host[:-1]
    links = links["links"]
    log.info("Client settings: %d links, %d clients, %d loops, %f delay"%(len(links), clients, loops, delay))
    log.info("Total: %d requests"%(len(links)*clients*loops))
    log.info("Host: %s"%(host))
    normalized = []
    for l in links:
        if not l.startswith("/"):
            normalized.append("/"+l)
        else:
            normalized.append(l)

    cthreads = []
    result_queue = multiprocessing.Queue()
    for i in range(clients):
        cc = ClientRunner(kwargs={"result":result_queue})
        cc.name = "client#%02d"%i
        cc.loops = loops
        cc.delay = delay
        cc.host = host
        cc.links = list(tuple(normalized))
        cthreads.append(cc)

    runtime = time.time()
    for cc in cthreads:
        cc.start()

    stats = []
    while len(stats)<len(cthreads):
        stats.append(result_queue.get())

    report(stats, time.time()-runtime-0.5)



if __name__ == "__main__":
    loops = clients = delay = 0
    try:
        jsonfile = sys.argv[1]
    except IndexError, e:
        print "Missing argument - %s" % str(e)
        print
        print "Usage:"
        print "bin/python client.py links"
        print
        print "links: json file download links and host."
        print
        print """{"links": ["link1.html","link2.html"], """
        print """ "loops": 10, "clients": 5, """
        print """ "host": "http://127.0.0.1:1234"}"""
        print
        sys.exit(0)

    with open(jsonfile) as file:
        links = json.loads(file.read())

    run(links)

