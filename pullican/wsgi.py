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
import hmac, hashlib


def application(environ, resp):
    # Doing the usual environment variable handling in application, cause it's all in environ
    
    # Email logging setup
    SMTP_SERVER = environ.get('PULLICAN_SMTP_SERVER','rcsmtp.rc.fas.harvard.edu')
    ADMIN_EMAILS = environ.get('PULLICAN_ADMIN_EMAILS','akitzmiller@g.harvard.edu')
    ADMIN_EMAIL_LIST = re.split('\s*,\s*', ADMIN_EMAILS)
    
    logger = logging.getLogger()
    handler = SMTPHandler(SMTP_SERVER,'rchelp@fas.harvard.edu',ADMIN_EMAIL_LIST,'Pullican error on %s' % socket.gethostname())
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    
    txt = ''
    resp("200 OK", [ ('Content-Type', 'text/plain') ])
    
    try:
        github_event       = environ.get('HTTP_X_GITHUB_EVENT')
        github_delivery    = environ.get('HTTP_X_GITHUB_DELIVERY')
        github_signature   = environ.get('HTTP_X_HUB_SIGNATURE')
        
        
        sourcepath  = environ.get('PULLICAN_SOURCE_PATH')
        contentpath = environ.get('PULLICAN_CONTENT_PATH',os.path.join([sourcepath,'content']))
        themepath   = environ.get('PULLICAN_THEME_PATH',os.path.join([sourcepath,'theme']))
        outputpath  = environ.get('PULLICAN_OUTPUT_PATH','/var/www/html')
        signaturekey   = environ.get('PULLICAN_SIGNATURE_KEY')        
        
        if not sourcepath:
            txt = 'Error: PULLICAN_SOURCE_PATH environment variable must be set.\n'
            logger.error(txt)
            return txt
        
        # Check signature if provided
        if signaturekey:
            payload = environ.get('wsgi.input').read()
            digest = 'sha1=' + hmac.new(signaturekey,payload,hashlib.sha1).hexdigest()
            if github_signature != digest:
                txt = 'Error: Github signature %s does not match the expected value: %s.\n' % (github_signature,digest)
                logger.error(txt)
                resp("403 Forbidden", [ ('Content-Type', 'text/plain') ])
                return txt
            
        # Pull from the repository
        cmd = 'cd %s && git pull' % sourcepath
        proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = proc.communicate()
        if proc.returncode != 0:
            txt = 'Error: Could not perform repository update with cmd %s: %s' % (cmd,stderr + stdout)
            logger.error(txt)
            return txt

        # Check paths
        for pathname,pathvalue in {'PULLICAN_SOURCE_PATH' : sourcepath, 'PULLICAN_CONTENT_PATH' : contentpath, 'PULLICAN_OUTPUT_PATH' : outputpath, 'PULLICAN_THEME_PATH' : themepath}.iteritems():
            if not os.path.exists(pathvalue):
                txt += '%s %s does not exist' % (pathname,pathvalue)
        if txt != '':
            logger.error(txt)
            return txt + '\n'
        
        
        # Process the content with pelican
        cmd = 'PYTHONPATH={sourcepath} pelican {contentpath} -t {themepath} -o {outputpath} -s {sourcepath}/publishconf.py'.format(sourcepath=sourcepath,contentpath=contentpath,themepath=themepath,outputpath=outputpath)
        proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = proc.communicate()
        if proc.returncode != 0:
            txt = 'Error: Could not process pelican content with cmd %s: %s' % (cmd,stderr + stdout)
            logger.error(txt)
            return txt
                 
            
        txt = 'OK'
    except Exception as e:
        txt = 'Error: %s\n%s' % (str(e),traceback.format_exc())
        logger.error(txt)
        resp("500 Internal Server Error", [ ('Content-Type', 'text/plain') ])
        return txt

    return txt + '\n'
