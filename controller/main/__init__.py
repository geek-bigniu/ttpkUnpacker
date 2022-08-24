import os

from model.mpk import MPK


class Main:
    def __init__(self, args):
        self._args = args

    def run(self):
        for arg in self._args[1:]:
            with open(arg, 'rb') as io:
                _, file_arg = os.path.split(arg)
                print('Loading: %s' % arg)
                mpk = MPK.load(io)

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
