import argparse

class CombinedHelpAction(argparse._HelpAction):
    # https://stackoverflow.com/questions/20094215/argparse-subparser-monolithic-help-output
    # author: grundic, Adaephon
    # explicit: mit license

    #pylint: disable=protected-access

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()

        # retrieve subparsers from parser
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)]
        # there will probably only be one subparser_action,
        # but better save than sorry
        for subparsers_action in subparsers_actions:
            # get all subparsers and print help
            for choice, subparser in subparsers_action.choices.items():
                print(u'')
                print(u"Subparser '{}'".format(choice))
                print(subparser.format_help())

        parser.exit()
