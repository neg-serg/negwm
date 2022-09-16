import os
import json
import subprocess
import pytest

import mock

import i3parse.i3parse

HERE = os.path.dirname(__file__)


def test_files():
    with mock.patch('os.environ', dict(HOME='/home/user')):
        assert i3parse.i3parse.default_configs() == [
            '/home/user/.i3/config', '/home/user/.config/i3/config',
            '/etc/i3/config', '/etc/xdg/i3/config']

    with mock.patch('os.environ', dict(
            HOME='/home/user',
            XDG_CONFIG_HOME='/xdg_home',
            XDG_CONFIG_DIRS='/xdg_dirs')):
        assert i3parse.i3parse.default_configs() == [
            '/home/user/.i3/config', '/xdg_home/i3/config',
            '/etc/i3/config', '/xdg_dirs/i3/config']

def test_run():
    subprocess.check_output(["i3parse", "--help"])

def test_consistency():
    config_file = os.path.join(HERE, 'config1')
    output = run(['bindings', config_file])
    assert output == """\
default 214 mode "code"
default mod+t mode "test"
test q mode "default"
"""

def test_executable():
    # Ensure that args are read correctly
    config_file = os.path.join(HERE, 'config1')
    output = run(['free', '--config', config_file])
    assert output.startswith('Mod+a')

def test_free():
    config_file = os.path.join(HERE, 'config1')
    output = run(['free', '--config', config_file])
    assert output.startswith('Mod+a\nMod+b\nMod+c\n'), output
    assert len(output.splitlines()) == 544 # consistency testing

def test_free_letter_sort():
    config_file = os.path.join(HERE, 'config1')
    output = run(['free', '--config', config_file, 'hey'])
    assert output.startswith('Mod+h')
    assert output.index('Mod+h')  < output.index('Mod+e') < output.index('Mod+y')

def test_cover_mode_graph():
    config_file = os.path.join(HERE, 'config1')
    output = run(['mode-graph', config_file])

def test_cover_modes():
    config_file = os.path.join(HERE, 'config1')
    output = run(['modes', config_file])

def test_cover_validate():
    config_file = os.path.join(HERE, 'config1')
    output = run(['validate', config_file])

def dont_test_complete_config():
    # This is takine a while to get implemented
    # leave this disableed for now
    config_file = os.path.join(HERE, 'completeconfig')
    output = run(['validate', config_file])


def test_new_windows():
    # This is takine a while to get implemented
    # leave this disableed for now
    config_file = os.path.join(HERE, 'new_float.config')
    output = run(['validate', config_file])


def test_no_quote():
    # This is takine a while to get implemented
    # leave this disableed for now
    config_file = os.path.join(HERE, 'mode_no_quote.config')
    output = run(['bindings', config_file])


def test_comment():
    config_file = os.path.join(HERE, 'comment.config')
    output = run(['validate', config_file])


def test_bind_options():
    config_file = os.path.join(HERE, 'bindoptions.config')
    run(['validate', config_file])
    output = run(['bindings', '--json', config_file])
    for line in output.splitlines():
        data = json.loads(line)
        key = data['key']
        if key == 'a':
            assert data['on_release']
        elif key == 'b':
            assert data['on_release']
        elif key == 'c':
            assert not data['on_release']
        else:
            raise ValueError(key)


def test_border():
    config_file = os.path.join(HERE, 'bindborders.config')
    run(['validate', config_file])
    output = run(['bindings', config_file])
    assert output.startswith('default $mod+n border normal')

def test_dos():
    config_file = os.path.join(HERE, 'dos.config')
    output = run(['validate', config_file])

def test_cover_validate():
    config_file = os.path.join(HERE, 'config1')
    output = run(['validate', config_file])

def test_no_default_config():
    with mock.patch('i3parse.i3parse.default_configs', lambda: ['/doesnotexist']):
        with pytest.raises(i3parse.i3parse.NoConfigFileFound) as e:
            run(['mode-graph'])

        assert '/doesnotexist' in str(e)

def test_cover_help():
    with pytest.raises(SystemExit):
        run(['--help'])

def run(args):
    return '\n'.join(i3parse.i3parse.run(args)) + '\n'
