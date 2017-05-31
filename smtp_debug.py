import asyncore
import smtpd
import time


class Server(smtpd.DebuggingServer):
    def __init__(self, localaddr, remoteaddr, fake_lag=None):
        super().__init__(localaddr, remoteaddr)
        self.fake_lag = fake_lag

    def process_message(self, *args, **kwargs):
        super(Server, self).process_message(*args, **kwargs)
        if self.fake_lag:
            time.sleep(self.fake_lag)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=1025)
    parser.add_argument('--lag', type=float)
    args = parser.parse_args()
    Server((args.host, args.port), None, fake_lag=args.lag)
    asyncore.loop()
