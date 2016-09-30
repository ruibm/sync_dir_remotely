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
import json
import socket
import struct
import time



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
      self.log.info('Accepted connection from address: [{}]'.format(
          str(address)))
      with StreamHandler(connection) as handler:
        handler.run()

  def __exit__(self, exc_type, exc_value, traceback):
    self.log.info('Exiting...')
    if exc_type and exc_value and traceback:
      self.log.error('Received exception type=[{}] value=[{}] traceback=[{}]'\
          .format(exc_type, exc_value, traceback))
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
    self._serde = MessageSerde()

  def __enter__(self):
    self.log.info('Entering...')
    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self._socket.settimeout(1.0) # seconds
    remote = self._args.remote
    port = self._args.port
    self.log.info('Trying to connect to [{}:{}]'.format(remote, port))
    self._socket.connect((remote, port))
    self.log.info('Successfully connected to [{}:{}]'.format(
        remote, port))
    return self

  def run(self):
    self.log.info('Running...')
    while True:
      try:
        with StreamHandler(self._socket, close_on_exit=False) as handler:
          handler.run()
      except socket.timeout:
        # Nothing to receive from the server.
        pass

      msg = Message(MessageType.PING_REQUEST)
      self.sendMessage(msg)

  def sendMessage(self, message):
    data = self._serde.serialise(Message(MessageType.PING_REQUEST))
    self._socket.sendall(data)

  def __exit__(self, exc_type, exc_value, traceback):
    self.log.info('Exiting...')
    if self._socket:
      self._socket.close()
      self._socket = None



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


class StreamHandler(object):
  def __init__(self, socket, close_on_exit=True):
    self.log = Logger(StreamHandler.__name__)
    self._socket = socket
    self._close_on_exit = close_on_exit
    self._buffer = ''
    self._serde = MessageSerde()
    self._handler = MessageHandler()

  def __enter__(self):
    self.log.info('Entering...')
    return self

  def run(self):
    self.log.info('Running...')
    while True:
      data = self._socket.recv(1024)
      datal = len(data)
      if datal == 0:
        self.log.info('Remote client disconnected.')
        return
      elif datal > 0:
        self.log.info('Received [{}] bytes.'.format(datal))
        self._buffer += data
        message, unused = self._serde.deserialise(self._buffer)
        self._buffer = unused
        if message != None:
          response = self._handler.handleMessage(message)
          if response != None:
            response_data = self._serde.serialise(response)
            self._socket.sendall(response_data)
      else:
        assert False, 'Should never get here!!! recv_bytes=[{}]'.format(datal)

  def __exit__(self, exc_type, exc_value, traceback):
    self.log.info('Exiting...')
    if self._close_on_exit and self._socket:
      self._socket.close()
      self._socket = None


class MessageType(object):
  PING_REQUEST = 0
  PING_RESPONSE = 1

class Message(object):
  def __init__(self, message_type):
    self.type = message_type
    self.body = {}


class MessageSerde(object):
  def __init__(self):
    self.log = Logger(MessageSerde.__name__)

  def serialise(self, message):
    """ Returns a list of bytes containing the serialised msg/ """
    output = ''
    serialized_body = json.dumps(message.body)
    self.log.warn("rui " + str(message.type))
    output += struct.pack('>i', message.type)
    output += struct.pack('>l', len(serialized_body))
    output += serialized_body
    return output

  def deserialise(self, input):
    """ Returns a tuple (Message, UnusedBytesList) """
    if len(input) < 12:
      return (None, input)
    self.log.info('input=[{}]'.format(input))
    message = Message(struct.unpack('>i', input[0:4]))
    body_size = struct.unpack('>l', input[4:12])
    if len(input) < 12 + body_size:
      return (None, input)
    raw_body = input[12:body_size + 12]
    message.update(json.loads(raw_body))
    return (Message, input[body_size + 12:])


class MessageHandler(object):
  def __init__(self):
    self.log = Logger(MessageHandler.__name__)

  def handleMessage(message):
    self.log.info("Handling message of type: [{}]".format(message.type))
    # Odd numbered MessageType's are responses.
    if message.type % 2 == 1:
      return None
    # TODO(ruibm): Do the proper thing instead of just mirroring.
    response = Message(message.PING_RESPONSE)
    self.log.info("Responding with message of type: [{}]".format(response.type))
    return Message(message.PING_RESPONSE)




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

