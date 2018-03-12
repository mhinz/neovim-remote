#!/usr/bin/env python3

import os
import time
import signal
import subprocess
import nvr

env = {'NVIM_LISTEN_ADDRESS': '/tmp/pytest_nvimsock'}
testfile = '/tmp/pytest_file'


class Nvim:
    nvim = None

    def start(self, env=env):
        env.update(os.environ)
        self.nvim = subprocess.Popen(['nvim', '-nu', 'NORC', '--headless'],
                                close_fds=True, env=env)
        time.sleep(1)

    def stop(self):
        self.nvim.send_signal(signal.SIGTERM)


def test_open_and_write_file():
    nvim = Nvim()
    nvim.start()
    argv = ['nvr', '-c', 'e /tmp/pytest_file | %d | exe "norm! iabc" | w']
    nvr.main(argv, env)
    nvim.stop()
    with open('/tmp/pytest_file') as f:
        assert 'abc\n' == f.read()
    os.remove(testfile)
