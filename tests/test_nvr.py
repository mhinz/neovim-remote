#!/usr/bin/env python3

import os
import time
import subprocess
import uuid
import nvr

# Helper functions

def run_nvim(env):
    nvim = subprocess.Popen(['nvim', '-nu', 'NORC', '--headless'], env=env)
    time.sleep(1)
    return nvim

def run_nvr(cmdlines, env):
    for cmdline in cmdlines:
        nvr.main(cmdline, env)

def setup_env():
    env = {'NVIM_LISTEN_ADDRESS': 'pytest_socket_{}'.format(uuid.uuid4())}
    env.update(os.environ)
    return env

# Tests

def test_remote_send(capsys):
    env = setup_env()
    nvim = run_nvim(env)
    cmdlines = [['nvr', '--nostart', '--remote-send', 'iabc<cr><esc>'],
                ['nvr', '--nostart', '--remote-expr', 'getline(1)']]
    run_nvr(cmdlines, env)
    nvim.terminate()
    out, err = capsys.readouterr()
    assert out == 'abc\n'

# https://github.com/mhinz/neovim-remote/issues/77
def test_escape_filenames_properly(capsys):
    env = setup_env()
    nvim = run_nvim(env)
    cmdlines = [['nvr', '-s', '--nostart', '-o', 'a b|c'],
                ['nvr', '-s', '--nostart', '--remote-expr', 'fnamemodify(bufname(""), ":t")']]
    run_nvr(cmdlines, env)
    nvim.terminate()
    out, err = capsys.readouterr()
    assert out == 'a b|c\n'
