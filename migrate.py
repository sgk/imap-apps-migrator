#!/usr/bin/python
#vim:set fileencoding=utf-8

#
# IMAP4 to Google Apps email migration tool.
#
# Copyright (c) 2013 by Shigeru KANEMOTO
#

import gdata.apps.migration.service
import gdata.apps.service
import gdata.service

import imaplib
import email
import re
import sys
import argparse
import getpass
import csv

IMAP_NOSELECT = r'\Noselect'
IMAP_SEEN = r'\Seen'
IMAP_FLAGGED = r'\Flagged'
IMAP_DRAFT = r'\Draft'

migration_prefix = u'移行'
migration_nodate = u'移行/日付なし'
default_date = 'Thu, 1 Jan 1970 00:00:00 +0000'

def progress(a, b):
  sys.stdout.write('%d / %d\r' % (a, b))
  sys.stdout.flush()

class IMAPsource:
  re_flags = re.compile(r'^\d+ \(FLAGS \((?P<flags>.*)\)\)$')
  re_folder = re.compile(r'^\((?P<flags>[^x]*)\) "(?P<delimiter>[^"]*)" "(?P<folder>[^"]+)"$')
  re_utf7 = re.compile(r'&([^-]*)-')

  def __init__(self, server):
    self.conn = imaplib.IMAP4(server)
    self.n_folders = 0
    self.n_messages = 0
    self.n_errors = 0

  def login(self, user, password):
    self.conn.login(user, password)

  def logout(self):
    self.conn.logout()

  def decode(self, s):
    def decode_group(m):
      if s == '':
        return '&'
      return ('+' + m.group(1).replace(',', '/') + '-').decode('utf-7')
    return self.re_utf7.sub(decode_group, s)

  def folders(self):
    response, data = self.conn.list()
    for folder in data:
      m = self.re_folder.match(folder)
      if IMAP_NOSELECT in m.group('flags').split():
        continue
      folder = m.group('folder')
      label = self.decode(folder).split(m.group('delimiter'))
      yield folder, label

  def messages(self, folder):
    try:
      self.conn.select(folder, readonly=True)
      response, data = self.conn.search(None, 'UNDELETED')
      messages = data[0].split()
      self.n_folders += 1
    except imaplib.IMAP4.error:
      print 'Could not select folder "%s".' % self.decode(folder)
      return

    n = 0
    for message in messages:
      n += 1
      progress(n, len(messages))
      try:
        response, data = self.conn.fetch(message, '(FLAGS)')
        flags = self.re_flags.match(data[0]).group('flags').split()
        response, data = self.conn.fetch(message, '(BODY.PEEK[])')
        rfc822 = data[0][1]
        self.n_messages += 1
        yield flags, rfc822
      except imaplib.IMAP4.error:
        print 'Error retriving message %s in "%s".' % (message, folder)
        self.n_errors += 1

class AppsDestination:
  re_header = re.compile(r'^(.*?)\r?\n\r?\n', re.DOTALL)

  def __init__(self, domain, email, password):
    self.service = gdata.apps.migration.service.MigrationService(
      email=email,
      password=password,
      domain=domain,
      source='sgk-imap4-migration'
    )
    self.service.ProgrammaticLogin()
    self.n_messages = 0
    self.n_errors = 0

  def sink(self, username, rfc822, properties, labels):
    try:
      self.service.ImportMail(
        user_name=username,
        mail_message=rfc822,
        mail_item_properties=properties,
        mail_labels=labels
      )
      self.n_messages += 1
    except gdata.apps.service.AppsForYourDomainException, e:
      print e
      print self.re_header.match(rfc822).group(1)
      print
      self.n_errors += 1

class Migrate:
  def __init__(self, domain, admin, password):
    self.dst = AppsDestination(domain, admin, password)
    self.domain = domain

  def migrate(self, imapserver, login, password, appsusername):
    src = IMAPsource(imapserver)
    src.login(login, password)

    for folder, label in src.folders():
      if label[0] == 'INBOX':
        label.pop(0)
      label.insert(0, migration_prefix)
      label = '/'.join(label)
      print label

      for flags, rfc822 in src.messages(folder):
        labels = [label]
        message = email.message_from_string(rfc822)
        if not message.has_key('Date'):
          message['Date'] = default_date
          rfc822 = message.as_string()
          labels.append(migration_nodate)

        properties = []
        if IMAP_SEEN not in flags:
          properties.append('IS_UNREAD')
        if IMAP_FLAGGED in flags:
          properties.append('IS_STARRED')
        if IMAP_DRAFT in flags:
          properties.append('IS_DRAFT')

        self.dst.sink(appsusername, rfc822, properties, labels)

    src.logout()

    print 'Retrieved from %s@%s; %d messages %d errors.' % (
      login, imapserver,
      src.n_messages, src.n_errors,
    )
    print 'Fed into %s@%s; %d messages %d errors.' % (
      appsusername, self.domain,
      self.dst.n_messages, self.dst.n_errors,
    )

def main():
  parser = argparse.ArgumentParser(
      description='IMAP4 to Google Apps email migration tool.')
  parser.add_argument('--domain', required=True,
      help='Google Apps hosted domain name.')
  parser.add_argument('--admin', required=True,
      help='Google Apps domain admin account.')
  parser.add_argument('--password',
      help='Password for admin account.')
  parser.add_argument('--server', required=True,
      help='IMAP4 server FQDN.')
  parser.add_argument(
    '--user', action='append',
    nargs=3, metavar=('login', 'password', 'username'),
    help='User information for migration; IMAP4 login name, password, Google Apps username'
  )
  parser.add_argument(
    '--csv', action='append', nargs=1,
    help='Read user information from CSV file.'
  )

  args = parser.parse_args()
  if '@' not in args.admin:
    args.admin += '@' + args.domain

  if args.user == None:
    args.user = []
  for fname in args.csv:
    try:
      with open(fname[0], 'r') as fp:
        for line in csv.reader(fp):
          if len(line) == 0:
            continue
          elif line[0].startswith('#'):
            continue
          elif len(line) < 3:
            print '%s: CSV rows must have at least 3 columns.' % fname[0]
          args.user.append(line[0:3])
    except IOError, e:
      print '%s: %s' % (e.strerror, e.filename)
      sys.exit(1)

  if len(args.user) == 0:
    print 'No user specified either in command line and CSV file.'
    sys.exit(1)

  try:
    if not args.password:
      args.password = getpass.getpass('Admin Password: ')
    migrate = Migrate(args.domain, args.admin, args.password)
    for login, password, username in args.user:
      print 'Migrating %s to %s' % (login, username)
      migrate.migrate(args.server, login, password, username)
  except gdata.service.BadAuthentication, e:
    print e
    sys.exit(1)
  except imaplib.IMAP4.error, e:
    print '%s: %s' % (login, e)
    sys.exit(1)
  except KeyboardInterrupt:
    sys.exit(1)

if __name__ == '__main__':
  main()
