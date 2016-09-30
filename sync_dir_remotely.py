#!/usr/bin/python2.7
#
# This program continuously one-way synchronises one local directory
# into a remote machine.
#
# LocalClient ==> RemoteServer
#
# Usage:
#

#########################################################
# Imports
#########################################################
import argparse
import datetime
import time
import socket



#########################################################
# Functions
#########################################################
def parse_args():
  parser = argparse.ArgumentParser(description='Synchronise a dir remotely.')
  parser.add_argument(
      '-m',
      '--mode',
      required=True,
      type=str,
      choices=('remote', 'local'),
      help='Mode to run this script in.',
  )

  parser.add_argument(
      '-p',
      '--port',
      default=8082,
      type=int,
      help='Remote server listen port.',
  )

  parser.add_argument(
      '-v',
      '--verbosity',
      default=LOG_LEVELS.index('info'),
      type=int,
      choices=range(len(LOG_LEVELS)),
      help='Remote server listen port. levels=[{}]'.format(
          ', '.join(['{}={}'.format(LOG_LEVELS[i], i) \
              for i in range(len(LOG_LEVELS))])),
  )

  parser.add_argument(
      '-r',
      '--remote',
      default='localhost',
      type=str,
      help='Remote machine to connect to.',
  )

  args = parser.parse_args()
  return args



#########################################################
# Remote Server Classes
#########################################################
class RemoteServer(object):
  def __init__(self, args):
    self.log = Logger(RemoteServer.__name__)
    self.log.info('Initing...')
    self._args = args

  def __enter__(self):
    self.log.info('Entering...')
    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self._socket.bind(('', self._args.port))
    return self

  def run(self):
    self.log.info('Running...')
    while True:
      self.log.info('Listening for incoming connections in port [{}]...'.format(
          self._args.port))
      self._socket.listen(1)
      connection, address = self._socket.accept()
      self.log.info('Accepted connection from address: [{}]'.format(str(address)))
      with MessageHandler(connection, address) as handler:
        handler.run()

  def __exit__(self, exc_type, exc_value, traceback):
    self.log.info('Exiting...')
    if self._socket:
      self._socket.close()
      self._socket = None



#########################################################
# Local Client Classes
#########################################################
class LocalClient(object):
  def __init__(self, args):
    self.log = Logger(LocalClient.__name__)
    self.log.info('Initing...')
    self._args = args

  def __enter__(self):
    self.log.info('Entering...')
    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote = self._args.remote
    port = self._args.port
    self.log.info('Trying to connect to [{}:{}]'.format(remote, port))
    self._socket.connect((remote, port))
    self.log.info('Successfully connected to [{}:{}]'.format(
        remote, port))
    return self

  def run(self):
    self.log.info('Running...')

  def __exit__(self, exc_type, exc_value, traceback):
    self.log.info('Exiting...')



#########################################################
# Common Classes
#########################################################
class Logger(object):
  LEVEL = 2

  def __init__(self, log_name):
    self._name = log_name

  def info(self, msg):
    self._log(2, msg)

  def warn(self, msg):
    self._log(1, msg)

  def error(self, msg):
    self._log(0, msg)

  def _log(self, level, msg):
    if level > Logger.LEVEL:
      return

    ts = datetime.datetime.fromtimestamp(time.time()) \
        .strftime('%Y-%m-%d %H:%M:%S.%f')
    level = LOG_LEVELS[level].upper()[0]
    print '[{}][{}]<{}> {}'.format(level, ts, self._name, msg)


class MessageHandler(object):
  def __init__(self, conn, addr):
    self.log = Logger(MessageHandler.__name__)
    self._conn = conn
    self._addr = addr
    self._buffer = []

  def __enter__(self):
    self.log.info('Entering...')
    return self

  def run(self):
    self.log.info('Running...')
    while True:
      data = self._conn.recv(1024)
      datal = len(data)
      if datal == 0:
        self.log.info('Remote client disconnected.')
        return
      elif datal > 0:
        self.log.info('Received [{}] bytes.'.format(datal))
        self._buffer.extend(data)
      else:
        assert False, 'Should never get here!!! recv_bytes=[{}]'.format(datal)


  def __exit__(self, exc_type, exc_value, traceback):
    self.log.info('Exiting...')
    if self._conn:
      self._conn.close()
      self._conn = None



#########################################################
# Constants
#########################################################
LOG_LEVELS = ('error', 'warn', 'info', 'verbose')
LOG = Logger('main')



#########################################################
# Main
#########################################################
def main():
  args = parse_args()
  Logger.LEVEL = args.verbosity
  LOG.info('Mode: [{}]'.format(args.mode))
  if args.mode == 'remote':
    with RemoteServer(args) as server:
      server.run()
  else:
    with LocalClient(args) as client:
      client.run()


if __name__ == '__main__':
  main()

