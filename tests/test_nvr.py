#!/usr/bin/env python3

import os
import time
import signal
import subprocess
import nvr
import sys
import tempfile

def test_open_and_write_file():
    if sys.platform == 'win32':
        env = {'NVIM_LISTEN_ADDRESS': nvr.create_new_pipe_name()}
    else:
        env = {'NVIM_LISTEN_ADDRESS': '/tmp/pytest_nvimsock'}
        
    env.update(os.environ)

    test_file_path = os.path.join(tempfile.gettempdir(), "pytest_file")
    
    with subprocess.Popen(['nvim', '-nu', 'NORC', '--headless'], close_fds=True,
                          env=env) as proc:
        time.sleep(1)
        
        argv = ['nvr', '-c', 'e {} | %d | exe "norm! iabc" | w'.format(test_file_path)]
        nvr.main(argv=argv, env=env)
        proc.send_signal(signal.SIGTERM)

    with open(test_file_path) as f:
        assert 'abc\n' == f.read()
