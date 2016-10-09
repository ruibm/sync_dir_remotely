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
import unittest

from sync_dir_remotely import *



#########################################################
# Functions
#########################################################



#########################################################
# Classes
#########################################################
class MessageSerdeTest(unittest.TestCase):
  def test_symmetry(self):
    serde = MessageSerde()
    message = Message(42)
    key = 'rui'
    value = ['will', 'it', 'work', '?']
    message.body[key] = value
    data = serde.serialise(message)
    actual_msg, unused = serde.deserialise(data)
    self.assertEqual(0, len(unused))
    self.assertEqual(value, actual_msg.body[key])


class DirCrawlerTest(unittest.TestCase):
  def test_crawl_test_folder(self):
    crawler = DirCrawler('test_data/DirCrawlerTest', [r'.*/\..*'])
    files = crawler.crawl()
    self.assertEqual(2, len(files))

  def test_crawl_and_hash_test_folder(self):
    crawler = DirCrawler('test_data/DirCrawlerTest', [r'.*/\..*'])
    files = crawler.crawl_and_hash()
    self.assertEqual(2, len(files))
    for file_path in files:
      self.assertEqual('0af9f1702bc23d5a33268e2755457773',
          files[file_path][1])

  def test_buck_folder(self):
    crawler = DirCrawler('~/buck/src', [r'.*/\..*', r'.*third-party/.*'])
    files = crawler.crawl_and_hash()
    files = crawler.crawl_and_hash(files)
    self.assertEqual(2291, len(files))



#########################################################
# Constants
#########################################################



#########################################################
# Main
#########################################################

if __name__ == '__main__':
  Logger.LEVEL = 3
  unittest.main(verbosity=2)

