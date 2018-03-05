import asyncore
import smtpd
import time


class Server(smtpd.DebuggingServer):
    def __init__(self, localaddr, remoteaddr, fake_lag=None):
        super().__init__(localaddr, remoteaddr)
        self.fake_lag = fake_lag

    def _print_message_content(self, peer, data):
        inheaders = True
        lines = data.splitlines()
        for line in lines:
            # headers first
            if inheaders and not line:
                peerheader = 'X-Peer: ' + peer[0]
                if not isinstance(peerheader, str):
                    # decoded_data=false; make header match other binary output
                    peerheader = peerheader.decode('utf-8', 'replace')
                print(peerheader)
                inheaders = False
            if not isinstance(line, str):
                line = line.decode('utf-8', 'replace')
            print(line)

    def process_message(self, *args, **kwargs):
        super().process_message(*args, **kwargs)
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
