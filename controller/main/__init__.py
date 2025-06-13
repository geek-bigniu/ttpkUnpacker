import os

from model.mpk import MPK

# Author 52pojie l2399007164
class Main:
    def __init__(self, args):
        self._args = args

    def run(self):
        if(len(self._args)<2):
            print("Use :python3 main.py js/xxx.ttpkg.js")
            exit()
        for arg in self._args[1:]:
            with open(arg, 'rb') as pkgfile:
                _, file_arg = os.path.split(arg)
                print('Loading: %s' % arg)
                mpk = MPK.load(pkgfile)
                for i in mpk.files:
                    file = mpk.file(i)
                    if file['offset'] != 0:
                        if file['name'] == '':
                            file['name'] = 'unknown_%s' % i
                        print('Unpacking: %s' % file['name'])
                        path_file = '%s_unpack/%s' % (arg, file['name'])
                        dir_file, _ = os.path.split(path_file)
                        os.makedirs(dir_file, exist_ok=True)
                        with open(path_file, 'wb') as io_file:
                            io_file.write(mpk.data(i))
