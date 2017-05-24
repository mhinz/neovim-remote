#!/usr/bin/env python3

import os
import time
import signal
import subprocess
import nvr

def test_open_and_write_file():
    env = {'NVIM_LISTEN_ADDRESS': '/tmp/pytest_nvimsock'}
    env.update(os.environ)

    with subprocess.Popen(['nvim', '-nu', 'NORC', '--headless'], close_fds=True,
                          env=env) as proc:
        time.sleep(1)
        argv = ['nvr', '-c', 'e /tmp/pytest_file | %d | exe "norm! iabc" | w']
        nvr.main(argv=argv, env=env)
        proc.send_signal(signal.SIGTERM)

    with open('/tmp/pytest_file') as f:
        assert 'abc\n' == f.read()
