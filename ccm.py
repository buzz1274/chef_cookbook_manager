#!/usr/bin/python

"""
Copyright (c) 2015 David Exelby

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from optparse import OptionParser
from StringIO import StringIO
from subprocess import CalledProcessError
import shutil
import subprocess
import ConfigParser
import os
import json
import sys

if sys.platform != 'win32':
    GREEN = '\033[92m'
    RED = '\033[91m'
    END = '\033[0m'
else:
    GREEN = ''
    RED = ''
    END = ''

class CCMExceptpion(Exception):
    pass

def main():
    parser = OptionParser()
    parser.add_option("-s", "--snapshot", dest="snapshot", metavar="FOLDER",
                      help="create a ccm.json manifest with cookbooks "\
                           "installed in the supplied folder.")
    parser.add_option("-i", "--install", action="store_true", dest="install",
                      help="installs chef cookbooks definded in ccm.json.")
    parser.add_option("-u", "--update", action="store_true", dest="update",
                      help="updates the cookbook repos to the commit hash "\
                           "defined in ccm.json.")
    parser.add_option("-f", "--force-update", action="store_true", dest="force_update",
                      help="pulls the latest version of cookbook repo for each "\
                           "cookbook in manifest.")
    parser.add_option("-p", "--purge", action="store_true", dest="purge",
                      help="deletes chef cookbooks that are not listed in the "\
                           "manifest.")

    (options, args) = parser.parse_args()

    if options.snapshot:
        snaphsot_manifest(options.snapshot)
    elif options.install:
        update_cookbooks(False)
    elif options.update:
        update_cookbooks(False)
    elif options.force_update:
        update_cookbooks(True)
    elif options.purge:
        purge_cookbooks()
    else:
        print "%sPlease supply a valid argument%s" % (RED, END,)
        parser.print_help()

def snaphsot_manifest(folder):
    """
    snapshot a cookbook manifest containg name, repo url and
    commit id each cookbook used.
    """
    folder = folder.strip('/')

    if not os.path.exists(folder):
        print "%sFolder %s does not exist%s" % (RED, folder, END,)
        sys.exit()
    else:
        manifest = {'base_folder': folder,
                    'cookbooks': []}

        for dirs in os.walk(folder).next()[1]:
            git_config_path = '%s/%s/.git/config' % (folder, dirs,)
            if os.path.exists(folder):
                repo_url = get_repo_url(git_config_path)
                commit_hash = subprocess.check_output(['git', 'rev-parse', '--verify', 'HEAD'],
                    cwd='%s/%s/' % (folder,dirs,))
                if repo_url and commit_hash:
                    manifest['cookbooks'].append({'install_path': dirs,
                                                  'repo_url': repo_url,
                                                  'commit_hash': commit_hash.strip()})

        try:
            f = open('ccm.json', 'w')
            f.write(json.dumps(manifest, indent=4, sort_keys=True))
        except:
            print "%sUnable to write ccm.json%s" % (RED, END,)
            sys.exit()

def update_cookbooks(force_update):
    """
    runs git pull/clone for each cookbook in the manifest
    """
    manifest = read_manifest()
    cwd = os.path.dirname(os.path.realpath('ccm.json'))
    for cookbook in manifest['cookbooks']:
        path = "%s/%s/%s" % (cwd, manifest['base_folder'],
                             cookbook['install_path'],)

        try:
            with open(os.devnull, "w") as f:
                if os.path.exists(path):
                    message = 'Updating'
                    subprocess.check_call(["git", "pull"],
                        cwd=path, stdout=f, stderr=f)
                else:
                    message = 'Cloning'
                    os.mkdir(path)
                    subprocess.check_call(["git", "clone", cookbook['repo_url'], "."],
                        cwd=path, stdout=f, stderr=f)

                if not force_update and cookbook['commit_hash']:
                    subprocess.check_call(["git", "reset", "--hard", cookbook['commit_hash']],
                        cwd=path, stdout=f, stderr=f)

            print "%s %s..........%sDONE%s" % (message, cookbook['install_path'], GREEN, END,)
        except CalledProcessError:
            print "%s %s..........%sFAILED%s" % (message, cookbook['install_path'], RED, END,)
        except KeyboardInterrupt:
            print "%sUser exited%s" % (RED, END,)
            sys.exit()
        except:
            print "%sAn error occurred%s" % (RED, END,)
            sys.exit()

def purge_cookbooks():
    """
    delete cookbooks that are not in the manifest
    """
    manifest = read_manifest()
    cookbooks = []
    cwd = os.path.dirname(os.path.realpath('ccm.json'))

    for cookbook in manifest['cookbooks']:
        cookbooks.append(cookbook['install_path'])

    for dirs in os.walk(manifest['base_folder']).next()[1]:
        if dirs not in cookbooks:
            response = None
            while not response:
                response = raw_input("%s not in manifest file.Delete[Y/N]..." % (dirs,))
                if response.lower() not in ['y', 'n']:
                    print "%sPlease enter Y or N%s" % (RED, END,)
                    response = None

            if response.lower() == 'y':
                path = '%s/%s/%s' % (cwd, manifest['base_folder'], dirs)
                try:
                    shutil.rmtree(path)
                except OSError:
                    print "%sFailed to delete %s%s" % (RED, dirs, END,)

def read_manifest():
    try:
        manifest = open('ccm.json', 'r')
        manifest = json.loads(manifest.read())
        if ('base_folder' not in manifest or
            'cookbooks' not in manifest):
            raise CCMExceptpion('Invalid manifest file')

        return manifest
    except CCMExceptpion, e:
        print "%s%s%s" % (RED, e, END,)
    except:
        print "%sUnable to read ccm.json%s" % (RED, END,)
        sys.exit()

def get_repo_url(file):
    """
    opens/reads a git config file
    """
    try:
        with open(file) as f:
            c = f.readlines()
        cp = ConfigParser.ConfigParser()
        cp.readfp(StringIO(''.join([l.lstrip() for l in c])))

        return cp.get('remote "origin"', 'url')
    except:
        return False


if __name__ == "__main__":
    main()
