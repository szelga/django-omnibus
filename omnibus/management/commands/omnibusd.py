import logging

from django.core.management.base import BaseCommand
from django.utils.module_loading import import_by_path
from tornado import ioloop
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_unix_socket

from ...pubsub import PubSub
from ...settings import (
    SERVER_PORT, AUTHENTICATOR_FACTORY, CONNECTION_FACTORY, WEBAPP_FACTORY,
    DIRECTOR_ENABLED, FORWARDER_ENABLED, SERVER_HOST)


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Initialize pubsub helper.
        pubsub = PubSub()

        if DIRECTOR_ENABLED:
            logger.info('Starting director.')
            pubsub.init_director()

        if FORWARDER_ENABLED:
            logger.info('Starting forwarder.')
            pubsub.init_forwarder()

        # Get factories for connection and tornado webapp.
        authenticator_factory = import_by_path(AUTHENTICATOR_FACTORY)
        connection_factory = import_by_path(CONNECTION_FACTORY)
        webapp_factory = import_by_path(WEBAPP_FACTORY)

        # Create app
        app = webapp_factory(connection_factory(authenticator_factory(), pubsub))
        if SERVER_PORT is None:
            # Listen on UNIX socket
            server = HTTPServer(app)
            socket = bind_unix_socket(SERVER_HOST)
            server.add_socket(socket)
        else:
            # Listen on SERVER_HOST:SERVER_PORT
            if SERVER_HOST:
                app.listen(SERVER_PORT, address=SERVER_HOST)
            else:
                app.listen(SERVER_PORT)

        loop = ioloop.IOLoop().instance()
        try:
            logger.info('Starting omnibusd.')
            loop.start()
        except KeyboardInterrupt:
            logger.info('Received KeyboardInterrup, stopping omnibusd.')
            loop.stop()
