#!/usr/bin/env python3

"""
Ensures that root certificates are reloaded as well.
"""

from common import LOCALHOST, RootCert, STATUS_PORT, SocketPair, TcpServer, TlsClient, print_ok, run_ghostunnel, terminate
import time
import signal
import os

if __name__ == "__main__":
    ghostunnel = None
    try:
        # create certs
        root = RootCert('root')
        root.create_signed_cert('server')
        root.create_signed_cert('client')

        # start ghostunnel
        ghostunnel = run_ghostunnel(['server',
                                     '--listen={0}:13001'.format(LOCALHOST),
                                     '--target={0}:13002'.format(LOCALHOST),
                                     '--keystore=server.p12',
                                     '--status={0}:{1}'.format(LOCALHOST,
                                                               STATUS_PORT),
                                     '--cacert=root.crt',
                                     '--allow-ou=client'])

        # connect with client, confirm that the tunnel is up
        pair = SocketPair(TlsClient('client', 'root', 13001), TcpServer(13002))
        pair.validate_can_send_from_client(
            "hello world", "1: client -> server")
        pair.validate_can_send_from_server(
            "hello world", "1: server -> client")
        pair.validate_closing_client_closes_server(
            "1: client closed -> server closed")

        # Regenerate root certificates and reload
        RootCert.cleanup_certs(['root', 'client', 'server'])
        root.__init__('root')
        root.create_signed_cert('server')
        root.create_signed_cert('client')

        ghostunnel.send_signal(signal.SIGUSR1)
        time.sleep(3)
        
        # Make sure everything still works
        pair = SocketPair(TlsClient('client', 'root', 13001), TcpServer(13002))
        pair.validate_can_send_from_client(
            "hello world", "1: client -> server")
        pair.validate_can_send_from_server(
            "hello world", "1: server -> client")
        pair.validate_closing_client_closes_server(
            "1: client closed -> server closed")

        print_ok("OK")
    finally:
        terminate(ghostunnel)
