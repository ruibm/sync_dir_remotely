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
    self.assertEqual(2308, len(files))


class StateDifferTest(unittest.TestCase):
  def test_one_dir_one_file_no_diff(self):
    src = (
      { 'my_file.txt': (0, 'super md5')},
    )
    dst = (
      { 'my_file.txt': (0, 'super md5')},
    )
    differ = StateDiffer()
    result = differ.diff(src, dst)
    self.assertEqual(1, len(result))
    self.assertEqual(0, len(result[0]))

  def test_one_dir_one_file_diff_md5(self):
    src = (
      { 'my_file.txt': (0, 'super md5')},
    )
    dst = (
      { 'my_file.txt': (0, 'different md5')},
    )
    differ = StateDiffer()
    result = differ.diff(src, dst)
    self.assertEqual(1, len(result))
    self.assertEqual(1, len(result[0]))
    self.assertEqual('my_file.txt', result[0][0])

  def test_one_dir_one_file_does_not_exist_in_dst(self):
    src = (
      { 'my_file.txt': (0, 'super md5')},
    )
    dst = (
      {},
    )
    differ = StateDiffer()
    result = differ.diff(src, dst)
    self.assertEqual(1, len(result))
    self.assertEqual(1, len(result[0]))
    self.assertEqual('my_file.txt', result[0][0])

  def test_one_dir_one_file_does_not_exist_in_src(self):
    src = (
      {},
    )
    dst = (
      { 'my_file.txt': (0, 'different md5')},
    )
    differ = StateDiffer()
    result = differ.diff(src, dst)
    self.assertEqual(1, len(result))
    self.assertEqual(0, len(result[0]))



#########################################################
# Constants
#########################################################



#########################################################
# Main
#########################################################

if __name__ == '__main__':
  Logger.LEVEL = 3
  unittest.main(verbosity=2)

