chef_cookbook_manager
=====================

Automatically manage chef cookbook repos.

Usage: ccm.py [options]

Options:
  -h, --help            show this help message and exit
  -c FOLDER, --create=FOLDER
                        create a ccm.json manifest with cookbooks installed in
                        the supplied folder.
  -i, --install         installs chef cookbooks definded in ccm.json.
  -u, --update          pulls latest version of cookbook repo for each
                        cookbook in manifest.
  -p, --purge           deletes chef cookbooks that are not listed in the
                        manifest.


