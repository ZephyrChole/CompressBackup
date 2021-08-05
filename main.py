from abc import abstractmethod
import hashlib
import os
import re
import subprocess

SRC = ''
DST = ''


def check_path(dir_path):
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        return True
    else:
        path = os.path.split(dir_path)[0]
        if check_path(path):
            try:
                os.mkdir(dir_path)
                return True
            except:
                return False
        else:
            return False


class Unit:
    def __init__(self, relative_path):
        self.relative_path = relative_path
        self.name = os.path.split(self.relative_path)[1]
        self.local_path = os.path.abspath(os.path.join(SRC, self.relative_path))
        self.remote_folder = os.path.split(os.path.join(DST, self.relative_path))[0]

    @abstractmethod
    def main(self):
        pass


class File(Unit):
    def main(self):
        if self.compress():
            pass

    def compress(self):
        def remove_lock(lock):
            if os.path.exists(lock):
                os.remove(lock)

        def rm_unfinished():
            for i in os.listdir(self.remote_folder):
                if re.match('%s\.7z\.\d{3}' % name, i):
                    os.remove(os.path.join(self.remote_folder, i))

        pwd = hashlib.md5(self.name.encode()).hexdigest()
        name = hashlib.md5(pwd.encode()).hexdigest()
        complete_lock = f'{self.local_path}.complete'
        compressing_lock = f'{self.local_path}.compressing'
        fail_lock = f'{self.local_path}.fail'

        if os.path.exists(complete_lock):
            print('complete')
            remove_lock(fail_lock)
            return True
        else:
            if os.path.exists(compressing_lock):
                print('unfinished')
                rm_unfinished()
            elif os.path.exists(fail_lock):
                print('fail')
                rm_unfinished()
                os.remove(fail_lock)
            else:
                open(compressing_lock, 'w').close()

            return_code = self.start_compress(name, pwd)
            remove_lock(compressing_lock)
            if return_code == 0:
                open(complete_lock, 'w').close()
                remove_lock(fail_lock)
                return True
            else:
                open(fail_lock, 'w').close()
                return False

    def start_compress(self, name, pwd):
        cwd = os.getcwd()
        os.chdir(self.remote_folder)
        p = subprocess.Popen(
            ['7z', 'a', '-v4g', '-mhe', name, self.local_path, f'-p{pwd}'])
        p.wait()
        os.chdir(cwd)
        print('return code is ', p.returncode)
        return p.returncode


class Directory(Unit):
    def main(self):
        check_path(os.path.join(self.remote_folder, self.name))
        l = list(filter(lambda x: not re.search('.+\.(fail)|(compressing)|(complete)$', x), os.listdir(self.local_path)))
        for name in l:
            if not re.search('.+\.(fail)|(compressing)|(complete)$', name):
                r1 = os.path.join(self.relative_path, name)
                if os.path.isfile(os.path.join(self.local_path, name)):
                    u = File(r1)
                else:
                    u = Directory(r1)
                u.main()


class CompressBackup:
    def __init__(self, src, dst):
        global SRC
        global DST
        SRC = src
        DST = dst

    def main(self):
        Directory('').main()


if __name__ == '__main__':
    CompressBackup('./1', './2').main()
