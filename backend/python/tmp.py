import re

log = None
with open("dropbox_upload_log.txt", 'r') as f:
    for line in f:
        if re.search('file log at', line):
            log = line

match = re.match(r'.*(?P<url>http.*)', log)
log_url = match.group('url')

print "Setting Dropbox Log URL to {}".format(log_url)