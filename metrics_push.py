import tnetstring
import zmq
from prometheus_client import CollectorRegistry, Gauge, Histogram, push_to_gateway
from prometheus_client.exposition import basic_auth_handler

_INF = float("inf")


class PushpinMetricsClient(object):

    def __init__(self, sock_addr, prom_addr, prom_basic_auth_user, prom_basic_auth_passwd):
        ctx = zmq.Context()
        self.sock = ctx.socket(zmq.SUB)
        self.sock.connect(sock_addr)
        self.sock.setsockopt(zmq.SUBSCRIBE, b"report ")
        self.registry = CollectorRegistry()
        self.prom_addr = prom_addr
        self.prom_basic_auth_user = prom_basic_auth_user
        self.prom_basic_auth_passwd = prom_basic_auth_passwd
        self.init_metrics()

    def auth_handler(self, url, method, timeout, headers, data):
        username = self.prom_basic_auth_user
        password = self.prom_basic_auth_passwd
        return basic_auth_handler(url, method, timeout, headers, data, username, password)

    def start_push(self):
        while True:
            m_raw = self.sock.recv().decode("ISO-8859-1")  # .decode("ISO-8859-1")
            mtype, mdata = m_raw.split(" ", 1)
            if mdata[0] != "T":
                print("unsupported format")
                continue
            m = tnetstring.loads(mdata[1:].encode("ISO-8859-1"))
            print("%s %s" % (mtype, m))
            self.send_prom_push_gateway(msg_type=mtype, msg=m)

    def init_metrics(self):
        self.conns_gauge = Gauge("pushpin_concurrent_connections",
                                 "maximum concurrent connections measured since the last report",
                                 registry=self.registry, labelnames=["instance"])

        self.sent_msgs_gauge = Histogram("pushpin_sent_messages",
                                         "number of messages delivered to receivers (of all transports) since the "
                                         "last report",
                                         registry=self.registry, labelnames=["instance"])

        self.received_msgs_gauge = Histogram("pushpin_received",
                                             "number of published messages received since the last report",
                                             registry=self.registry, labelnames=["instance"])

        self.minutes_connections_alive = Histogram("pushpin_minutes",
                                                   "number of minutes all connections remained connected since last "
                                                   "report",
                                                   registry=self.registry, labelnames=["instance"])

    def send_prom_push_gateway(self, msg_type, msg):

        self.conns_gauge.labels(msg.get(b"from", "").decode("ISO-8859-1")).set(msg.get(b"connections", 0))

        self.sent_msgs_gauge.labels(msg.get(b"from", "").decode("ISO-8859-1")).observe(msg.get(b"sent", 0))

        self.received_msgs_gauge.labels(msg.get(b"from", "").decode("ISO-8859-1")).observe(msg.get(b"received", 0))

        self.minutes_connections_alive.labels(msg.get(b"from", "").decode("ISO-8859-1")).observe(msg.get(b"minutes", 0))

        push_to_gateway(self.prom_addr, job="pushpin", registry=self.registry, handler=basic_auth_handler)


if __name__ == "__main__":
    pushpin_metrics_client = PushpinMetricsClient("ipc:///usr/local/var/run/pushpin/pushpin-stats",
                                                  "<Host>:<Port>",
                                                  "<BasicAuthUser>",
                                                  "<BasicAuthPasswd>")
    pushpin_metrics_client.start_push()
