#!/usr/bin/python
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
    return self

  def run(self):
    self.log.info('Running...')

  def __exit__(self, exc_type, exc_value, traceback):
    self.log.info('Exiting...')



#########################################################
# Common Classes
#########################################################
class Logger(object):
  def __init__(self, log_name=''):
    self._name = log_name

  def info(self, msg):
    self._log('INFO', msg)

  def warn(self, msg):
    self._log('WARN', msg)

  def error(self, msg):
    self._log('ERROR', msg)

  def _log(self, level, msg):
    if self._name:
      print '[{}]<{}> {}'.format(level.upper(), self._name, msg)
    else:
      print '[{}] {}'.format(level.upper(), msg)


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
      self.log.info('Received [{}] bytes.'.format(len(data)))
      if len(data) > 0:
        self._buffer.extend(data)

  def __exit__(self, exc_type, exc_value, traceback):
    self.log.info('Exiting...')
    if self._conn:
      self._conn.close()
      self._conn = None



#########################################################
# Constants
#########################################################
LOG = Logger('main')



#########################################################
# Main
#########################################################
def main():
  args = parse_args()
  LOG.info('Mode: [{}]'.format(args.mode))
  if args.mode == 'remote':
    with RemoteServer(args) as server:
      server.run()
  else:
    with LocalClient(args) as client:
      client.run()


if __name__ == '__main__':
  main()

