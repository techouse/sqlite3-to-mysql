"""Click utilities."""

import click


class OptionEatAll(click.Option):
    """Taken from https://stackoverflow.com/questions/48391777/nargs-equivalent-for-options-in-click#answer-48394004."""  # noqa: ignore=E501 pylint: disable=C0301

    def __init__(self, *args, **kwargs):
        """Override."""
        self.save_other_options = kwargs.pop("save_other_options", True)
        nargs = kwargs.pop("nargs", -1)
        if nargs != -1:
            raise ValueError("nargs, if set, must be -1 not {}".format(nargs))
        super(OptionEatAll, self).__init__(*args, **kwargs)
        self._previous_parser_process = None
        self._eat_all_parser = None

    def add_to_parser(self, parser, ctx):
        """Override."""

        def parser_process(value, state):
            # method to hook to the parser.process
            done = False
            value = [value]
            if self.save_other_options:
                # grab everything up to the next option
                while state.rargs and not done:
                    for prefix in self._eat_all_parser.prefixes:
                        if state.rargs[0].startswith(prefix):
                            done = True
                    if not done:
                        value.append(state.rargs.pop(0))
            else:
                # grab everything remaining
                value += state.rargs
                state.rargs[:] = []
            value = tuple(value)

            # call the actual process
            self._previous_parser_process(value, state)

        retval = super(OptionEatAll, self).add_to_parser(  # pylint: disable=E1111
            parser, ctx
        )
        for name in self.opts:
            # pylint: disable=W0212
            our_parser = parser._long_opt.get(name) or parser._short_opt.get(name)
            if our_parser:
                self._eat_all_parser = our_parser
                self._previous_parser_process = our_parser.process
                our_parser.process = parser_process
                break
        return retval


def prompt_password(ctx, param, use_password):  # pylint: disable=W0613
    """Prompt for password."""
    if use_password:
        mysql_password = ctx.params.get("mysql_password")
        if not mysql_password:
            mysql_password = click.prompt("MySQL password", hide_input=True)

        return mysql_password
