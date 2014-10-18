from optparse import OptionParser
from StringIO import StringIO
import ConfigParser
import os
import json

def main():
    parser = OptionParser()
    parser.add_option("-c", "--create", dest="create", metavar="FOLDER",
                      help="create a ccm.json manifest with cookbooks "\
                           "installed in the supplied folder.")
    parser.add_option("-i", "--install", action="store_true", dest="install",
                      help="installs chef cookbooks definded in ccm.json.")
    parser.add_option("-u", "--update", action="store_true", dest="update",
                      help="pulls latest version of cookbook repo for each "\
                           "cookbook in manifest.")

    (options, args) = parser.parse_args()

    if options.create:
        create_manifest(options.create)
    elif options.install:
        install_cookbooks()
    elif options.update:
        update_cookbooks()

def create_manifest(folder):
    if not os.path.exists(folder):
        print "folder %s does not exist" % (folder,)
        os.exit()
    else:
        manifest = {'base_folder': folder,
                    'manifests': []}

        for dirs in os.walk(folder).next()[1]:
            git_config_path = '%s/%s/.git/config' % (folder, dirs,)
            if os.path.exists(folder):
                repo_url = get_repo_url(git_config_path)
                if repo_url:
                    manifest['manifests'].append({'install_path': dirs,
                                                  'repo_url': repo_url})

        if manifest['manifests']:
            f = open('ccm.json', 'w')
            f.write(json.dumps(manifest))

def install_cookbooks():
    print "install cookbooks"

def updates_cookbooks():
    print "install cookbooks"

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