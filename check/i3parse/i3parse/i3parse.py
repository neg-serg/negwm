# make code as python 3 compatible as possible
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import collections
import itertools
import json
import logging
import os
import string as string_mod
import sys
import io

import graphviz

from . import grammar
from . import combined_help

LOGGER = logging.getLogger()

print_func = print
def print(*_, **__):
    #pylint: disable=redefined-builtin
    raise Exception('Do not use print (see yield in run)')

open_func = open
def open(*_, **__):
    #pylint: disable=redefined-builtin
    raise Exception('Do not use open. Use extended notation')

class NoConfigFileFound(Exception):
    def __init__(self, possibilities):
        Exception.__init__(self)
        self.possibilities = possibilities

    def __str__(self):
        return '{}({!r})'.format(type(self).__name__, self.possibilities)

class ParseError(Exception):
    def __init__(self, line_number, text):
        Exception.__init__(self)
        self.line_number = line_number
        self.text = text

    def __repr__(self):
        return "ParseError({}, {!r})".format(self.line_number, self.text)

    def __str__(self):
        return "ParseError({}, {!r})".format(self.line_number, self.text)

def default_config():
    possible_config_files = default_configs()
    existing_files = list(filter(os.path.exists, possible_config_files))
    return existing_files[0] if existing_files else NoConfigFileFound(possible_config_files)

def default_configs():
    xdg_config_home = os.environ.get(
        'XDG_CONFIG_HOME',
        os.path.join(os.environ.get('HOME', '/'), '.config'))

    xdg_config_dirs = os.environ.get('XDG_CONFIG_DIRS', '/etc/xdg')

    # See Files section in man i3
    return  [
        os.path.join(os.environ.get('HOME', '/'), '.i3/config'),
        os.path.join(xdg_config_home, 'i3/config'),
        '/etc/i3/config',
        os.path.join(xdg_config_dirs, 'i3/config')]

def config_option(parser, name='config'):
    parser.add_argument(name, type=str, help='', nargs='?', default=default_config())

def json_option(parser):
    parser.add_argument('--json', action='store_true', help='Output in machine readable json')


def build_parser():
    parser = argparse.ArgumentParser(description='Inspect your i3 configuration and answer questions', add_help=False)
    parser.add_argument(
        '--help',
        action=combined_help.CombinedHelpAction, help='help for help if you need some help')  # add custom help
    parser.add_argument('--debug', action='store_true', help='Print debug output')
    parsers = parser.add_subparsers(dest='command')

    free = parsers.add_parser('free', help='Find free keys with certain properties')
    free.add_argument(
        '--mode',
        type=str, help='Show keys within this mode', default='default')
    free.add_argument(
        '--shift',
        action='store_true', help='Only return keys with shift', default=None)
    free.add_argument(
        '--no-shift',
        action='store_false', help='Only return keys without shift', default=None, dest='control')
    free.add_argument(
        '--control',
        action='store_true', help='Only return keys with control', default=None)
    free.add_argument(
        '--no-control',
        action='store_false', help='Only return keys without control', default=None, dest='control')
    free.add_argument(
        '--mod1',
        action='store_true', help='Only return keys with Mod1 (alt / meta)', default=None)
    free.add_argument(
        '--no-mod1',
        action='store_false', help='Only return keys without Mod1 (alt / meta)', default=None, dest='control')
    free.add_argument(
        'letters',
        type=str, nargs='?',
        help='Try to return a binding with one of these letters. There are special values :letter: and :number:')

    config_option(free, name='--config')

    modes = parsers.add_parser('modes', help='Show the keybinding modes and how to traverse them')
    config_option(modes)

    mode_graph_parser = parsers.add_parser('mode-graph', help='Show the keybinding modes and how to traverse them')
    config_option(mode_graph_parser)
    mode_graph_parser.add_argument('--drop-key', '-d', help='Ignore this key in all modes', type=str, action='append')
    mode_graph_parser.add_argument('--unicode', '-u', action='store_true', default=False, help='Compress with unicode')

    validate_parser = parsers.add_parser('validate', help='Validate key-bindings file (check if it parses)')
    config_option(validate_parser)

    binding_parser = parsers.add_parser('bindings', help='Show bindings')
    config_option(binding_parser)
    binding_parser.add_argument(
        '--mode', '-m',
        type=str, help='Only should bindings for this mode')
    binding_parser.add_argument(
        '--type', '-t',
        type=str, choices=sorted(set(get_bind_types().values())), help='Only show bindings of this type')
    json_option(binding_parser)
    return parser

def mode_graph(ast, ignore_keys=None):
    if ignore_keys is None:
        ignore_keys = set()
    ignore_keys = set(ignore_keys)

    modes = get_modes(ast)
    graph = collections.defaultdict(list)

    for mode in modes:
        graph[mode] = []

    bindings = get_bindings(ast)
    for b in bindings:
        if b['type'] == 'mode':
            if b['key'] in ignore_keys:
                continue
            graph[b['mode']].append((b['key'], b['mode_target']))
    return graph

def compress_binding(binding):
    output = binding.lower()
    output = output.replace('$mod', '$')
    output = output.replace('mod1', 'M')
    output = output.replace('super', 'S')
    output = output.replace('control', 'C')
    output = output.replace('shift', 's')
    return output

def dump_graph(graph, key_formatter=compress_binding):
    graphviz_graph = graphviz.Digraph()
    for node, neighbours in graph.items():
        graphviz_graph.node(node)
        for k, neighbour in neighbours:
            graphviz_graph.edge(node, neighbour, label=key_formatter(k))
    return graphviz_graph.source

def diacriticize_binding(s):
    "'Creatively' compress binding with diacritics"
    parts = s.split('+')
    key = parts[-1].lower()
    control = shift = modifier = sup = mod1 = False
    for part in parts[:-1]:
        if part.lower() == 'mod1':
            mod1 = True
        if part == 'S':
            sup = True
        if part.lower() == '$mod':
            modifier = True
        if part.lower() == 'shift':
            shift = True
        if part.lower() == 'control':
            control = True

    super_s = u"\u1de4"
    subscript_m = u'\u2098'

    output = key
    if control:
        output = 'C' + output
    if shift:
        output = output.upper()
    if sup:
        output = output + super_s
    if mod1:
        output = output + subscript_m
    if modifier:
        output = '$' + output

    return output

def extended_open(filename):
    if isinstance(filename, NoConfigFileFound):
        raise filename
    else:
        # Make strings "unicode" in both python2 and python3
        return io.open(filename)

def unicode_streams():
    sys.stdout = io.open(sys.stdout.fileno(), 'w', encoding='utf8')
    sys.stdin = io.open(sys.stdin.fileno(), 'r', encoding='utf8')

def main(args=None):
    unicode_streams()
    print_func(u'\n'.join(run(args)))

def run(args=None):
    if '--debug' in sys.argv[1:]:
        logging.basicConfig(level=logging.DEBUG)

    LOGGER.debug('Starting')

    args = build_parser().parse_args(args or sys.argv[1:])

    if args.command == 'mode-graph':
        with extended_open(args.config) as stream:
            input_string = stream.read()
            ast = parse(input_string)

        graph = mode_graph(ast, ignore_keys=args.drop_key)
        key_formatter = diacriticize_binding if args.unicode else compress_binding
        yield dump_graph(graph, key_formatter)
    elif args.command == 'modes':
        with extended_open(args.config) as stream:
            input_string = stream.read()
            ast = parse(input_string)

        for mode in sorted(get_modes(ast)):
            yield mode
    elif args.command == 'validate':
        with extended_open(args.config) as stream:
            input_string = stream.read()
            ast = parse(input_string)
    elif args.command == 'free':
        yield from free_command(args)
    elif args.command == 'bindings':
        yield from bindings_command(args)
    else:
        raise ValueError(args.bindings)


def bindings_command(args):
    with extended_open(args.config) as stream:
        input_string = stream.read()
        ast = parse(input_string)

    # dump_tree(ast)

    bindings = get_bindings(ast)
    sort_key = lambda k: (k['mode'], k['key'])
    for binding in sorted(bindings, key=sort_key):
        if args.mode and args.mode != binding['mode']:
            continue

        if args.type is not None:
            if binding['type'] != args.type:
                continue

        if args.json:
            workspace = (binding.get('i3_complex_action') or dict()).get('workspace')
            data = dict(
                mode=binding['mode'],
                key=binding['key'],
                text=binding['action_text'],
                action_type=binding['type'],
                on_release=binding['release'],
            )
            if workspace is not None:
                data['workspace'] = workspace
            yield json.dumps(data)
        else:
            yield ' '.join([binding['mode'], binding['key'], binding['action_text']])



def mac2unix(x):
    return x.replace(u'\r', u'\n')

def dos2unix(x):
    return x.replace(u'\r\n', u'\n')

def parse(input_string):
    g = grammar.build_grammar()
    return g.parse(
        mac2unix(dos2unix(input_string)))

_get_bind_types = None
def get_bind_types():
    #pylint: disable=global-statement
    global _get_bind_types
    if _get_bind_types is None:
        ACTION_TYPES = dict(
            exec_always='exec',
            exec_action='exec',
            i3_toggle_fullscreen='window',
            border_action='appearance',
            mode_action='mode',
            focus_action='window',
            i3_action='window',
            i3_move_action='window',
            i3_split_action='window',
            i3_layout_action='window',
            i3_modify_float='window',
            i3_workspace_command='workspace',
            i3_resize_action='window',
            scratch_show='window',
        )
        g = grammar.build_grammar()
        actions = [m.name for m in g['bind_action'].members]
        found_types = set(ACTION_TYPES[a] for a in actions)
        if found_types != set(ACTION_TYPES.values()):
            raise ValueError(found_types - set(ACTION_TYPES.values()))
        _get_bind_types = ACTION_TYPES

    return _get_bind_types


def get_modes(ast):
    if ast.expr_name == 'mode_block':
        _, _, (name_node,), _ = ast.children
        if name_node.expr_name == 'quoted_string':
            _, string_node, _ = name_node
            return [string_node.text]
        else:
            raise ValueError(name_node.expr_name)
    else:
        return list(itertools.chain.from_iterable(get_modes(child) for child in ast.children))

def get_bindings(ast, mode_name='default'):
    if ast.expr_name == 'mode_block':
        _, _, (mode_name_node,), _ = ast.children
        _, mode_name, _ = [c.text for c in mode_name_node.children]

    if ast.expr_name == 'bind_statement':
        return [parse_binding(ast, mode_name)]
    else:
        bindings = []
        for child in ast.children:
            bindings.extend(get_bindings(child, mode_name))
        return bindings

def parse_binding(ast, mode_name):
    try:
        return _parse_binding(ast, mode_name)
    except Exception as e:
        line = ast.full_text[:ast.start].count("\n")
        raise ParseError(line, ast.text) from e

def _parse_binding(ast, mode_name):
    _, options, _, key_node, more_options, _, action = ast.children
    key = key_node.text


    option_list = options.text.split() + more_options.text.split()
    release = '--release' in option_list

    next_action = action
    action_infos = []
    while len(next_action.children) != 1:
        print_func('children', action.children)
        action, _, _, _, next_action = action.children
        action_infos.append(parse_action(action))

    action_infos.append(parse_action(next_action.children[0]))

    action_info, = action_infos

    return dict(
        key=key,
        text=ast.text,
        release=release,
        mode=mode_name,
        **action_info)

def parse_action(action):
    #pylint: disable=too-many-branches
    i3_complex_action = i3_action = mode = command = None
    action_text = action.text
    specific_action, = action.children
    if specific_action.expr_name == 'exec_action':
        _exec, bash_exec = specific_action
        command = bash_exec.text
    elif specific_action.expr_name == 'i3_move_action':
        pass
    elif specific_action.expr_name == 'i3_split_action':
        _, _, direction = specific_action
        i3_complex_action = dict(action='split', direction=direction.text)
    elif specific_action.expr_name == 'mode_action':
        _, _, (string_node,) = specific_action.children
        try:
            _, string, _  = string_node
        except ValueError:
            string = string_node
        mode = string.text
    elif specific_action.expr_name == 'focus_action':
        _, _, output, direction = specific_action.children
        i3_complex_action = dict(output=output.text, direction=direction.text, action='focus')
    elif specific_action.expr_name == 'i3_action':
        i3_action = specific_action.text
    elif specific_action.expr_name == 'i3_modify_float':
        i3_action = 'modify_float'
    elif specific_action.expr_name == 'i3_layout_action':
        _, _, layout = specific_action.children
        i3_complex_action = dict(action='layout', layout=layout.text)
    elif specific_action.expr_name == 'i3_workspace_command':
        i3_complex_action = parse_i3_workspace_command(specific_action)
    elif specific_action.expr_name == 'i3_resize_action':
        i3_complex_action = dict(action='resize')
    elif specific_action.expr_name == 'scratch_show':
        i3_action = 'show_scratchpad'
    elif specific_action.expr_name == 'i3_toggle_fullscreen':
        i3_action = 'toggle_fullscreen'
    elif specific_action.expr_name == 'border_action':
        i3_action = 'change_borders'
    else:
        raise ValueError(specific_action.expr_name)

    bind_types = get_bind_types()
    return dict(
        command=command,
        i3_action=i3_action,
        i3_complex_action=i3_complex_action,
        mode_target=mode,
        type=bind_types[specific_action.expr_name],
        action_text=action_text
    )

def parse_i3_workspace_command(specific_action):
    _, _, workspace = specific_action.children
    workspace_target, = workspace.children
    workspace_target_name = workspace_name = None
    if workspace_target.expr_name == 'quoted_string':
        _, workspace_name, _ = workspace_target.children
        workspace_name = workspace_name.text
    elif workspace_target.expr_name == 'number':
        workspace_name = int(workspace_target.text)
    elif workspace_target.expr_name == 'workspace_sentinels':
        workspace_target_name = workspace_target.text
    else:
        raise ValueError(workspace_target.expr_name)
    return dict(
        action='workspace',
        workspace=workspace_name,
        workspace_target=workspace_target_name)

def free_command(args):
    with extended_open(args.config) as stream:
        input_string = stream.read()
        ast = parse(input_string)

    bindings = get_bindings(ast)
    bindings = [binding for binding in bindings if binding['mode'] == args.mode]

    characters = string_mod.ascii_lowercase + string_mod.punctuation + string_mod.digits
    free_keys = [
        parsed_key(c, mod=True, shift=shift, mod1=mod1, control=control)
        for c in characters
        for mod1 in (False, True)
        for control in (False, True)
        for shift in (False, True)
    ]

    if args.control is not None:
        free_keys = [k for k in free_keys if k['control'] == args.control]

    if args.shift is not None:
        free_keys = [k for k in free_keys if k['shift'] == args.shift]

    if args.mod1 is not None:
        free_keys = [k for k in free_keys if k['mod1'] == args.mod1]

    LETTER_SETS = dict(
        letter=string_mod.ascii_lowercase,
        digit=string_mod.digits,
    )

    order_by_letter = True
    if args.letters and args.letters.startswith(':') and args.letters.endswith(':'):
        letters = LETTER_SETS[args.letters.replace(':', '')]
        order_by_letter = False
    else:
        letters = args.letters

    if letters:
        free_keys = [k for k in free_keys if k['key'] in letters]

    for binding in bindings:
        key = parse_key(binding['key'])
        if key in free_keys:
            free_keys.remove(key)

    free_keys.sort(key=key_sorter(letters, order_by_letter))

    for key in free_keys:
        yield format_key(key)



def parse_key(string):
    new_string = None

    while string != new_string:
        if new_string is not None:
            string = new_string
        new_string = string.replace(' ', '')

    parts = string.split('+')
    key = parts[-1].lower()
    control = mod1 = shift = mod = False
    for modifier in parts[:-1]:
        modifier = modifier.lower()
        mod1 |= modifier == 'mod1'
        shift |= modifier == 'shift'
        mod |= modifier == '$mod'
        control |= modifier == 'control'

    return parsed_key(key, mod1=mod1, shift=shift, mod=mod, control=control)

def parsed_key(key, mod1=False, shift=False, mod=False, control=False):
    return dict(mod1=mod1, shift=shift, mod=mod, key=key, control=control)

def format_key(key):
    result = ''

    if key['mod']:
        result += 'Mod+'

    if key['mod1']:
        result += 'Mod1+'

    if key['control']:
        result += 'Control+'

    if key['shift']:
        result += 'Shift+'

    result += key['key']
    return result

def key_sorter(letters, order_by_letter):
    letters = letters or ""
    def key_sort(key):
        num_mods = sum(map(int, (key['shift'], key['control'], key['mod1'], key['mod'])))
        return (
            letters.find(key['key']) if order_by_letter else None,
            num_mods,
            key['key'] not in string_mod.ascii_letters,
            key['key'] not in string_mod.digits,
            key['key'],
            not key['shift'],
            not key['control'],
            not key['mod1'],
            key)
    return key_sort

def dump_tree(ast, depth=0):
    print('    ' * depth + ast.expr_name)
    for x in ast.children:
        dump_tree(x, depth=depth+1)
