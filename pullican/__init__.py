'''
Simple wsgi application for building a Pelican website.  

Does a git pull on the source path, then performs a Pelican transform

At minimum, PULLICAN_SOURCE_PATH must be set to the location of the git repository.
By default, content will be in PULLICAN_SOURCE_PATH/content, theme is PULLICAN_SOURCE_PATH/theme, and output is to /var/www/html

@author: Aaron Kitzmiller <aaron_kitzmiller@harvard.edu>
@copyright: 2016 The Presidents and Fellows of Harvard College. All rights reserved.
@license: GPL v2.0
'''

import os, traceback, subprocess, re, socket
import logging
from logging.handlers import SMTPHandler


# Email logging setup
SMTP_SERVER = os.environ.get('PULLICAN_SMTP_SERVER','rcsmtp.rc.fas.harvard.edu')
ADMIN_EMAILS = os.environ.get('PULLICAN_ADMIN_EMAILS','akitzmiller@g.harvard.edu')
ADMIN_EMAIL_LIST = re.split('\s*,\s*', ADMIN_EMAILS)

logger = logging.getLogger()
handler = SMTPHandler(SMTP_SERVER,'rchelp@fas.harvard.edu',ADMIN_EMAIL_LIST,'Pullican error on %s' % socket.gethostname())
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def run(environ, resp):
    txt = ''
    resp("200 OK", [ ('Content-Type', 'text/plain') ])
    
    try:
        github_event       = environ.get('X-GitHub-Event')
        github_delivery    = environ.get('X-GitHub-Delivery')
        github_signature   = environ.get('X-Hub-Signature')
        
        
        sourcepath  = os.environ.get('PULLICAN_SOURCE_PATH')
        contentpath = os.environ.get('PULLICAN_CONTENT_PATH',os.path.join([sourcepath,'content']))
        themepath   = os.environ.get('PULLICAN_THEME_PATH',os.path.join([sourcepath,'theme']))
        outputpath  = os.environ.get('PULLICAN_OUTPUT_PATH','/var/www/html')
        signature   = os.environ.get('PULLICAN_SIGNATURE')
        
        
        if not sourcepath:
            txt = 'Error: PULLICAN_SOURCE_PATH environment variable must be set.\n'
            logger.error(txt)
            return txt
        
        # Check paths
        for pathname,pathvalue in {'PULLICAN_SOURCE_PATH' : sourcepath, 'PULLICAN_CONTENT_PATH' : contentpath, 'PULLICAN_OUTPUT_PATH' : outputpath, 'PULLICAN_THEME_PATH' : themepath}.iteritems():
            if not os.path.exists(pathvalue):
                txt += '%s %s does not exist' % (pathname,pathvalue)
        if txt != '':
            logger.error(txt)
            return txt + '\n'
        
        # Check signature if provided
        if signature:
            if github_signature != signature:
                txt = 'Error: Github signature does not match the expected value.\n'
                logger.error(txt)
                return txt
            
        # Pull from the repository
        cmd = 'cd %s && git pull' % sourcepath
        proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = proc.communicate()
        if proc != 0:
            txt = 'Error: Could not perform repository update with cmd %s: %s' % (cmd,stderr + stdout)
            logger.error(txt)
            return txt
        
        
        # Process the content with pelican
        cmd = 'pelican {contentpath} -t {themepath} -o {outputpath}'.format(contentpath=contentpath,themepath=themepath,outputpath=outputpath)
        proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = proc.communicate()
        if proc != 0:
            txt = 'Error: Could not process pelican content with cmd %s: %s' % (cmd,stderr + stdout)
            logger.error(txt)
            return txt
                 
            
        
    except Exception as e:
        txt = 'Error: %s\n%s' % (str(e),traceback.format_exc())
        logger.error(txt)
        
    return txt + '\n'
