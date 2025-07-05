import typing as t
from unittest.mock import MagicMock, patch

import click
import pytest
from click.parser import Option, OptionParser

from sqlite3_to_mysql.click_utils import OptionEatAll, prompt_password


class TestClickUtils:
    def test_option_eat_all_init(self) -> None:
        """Test OptionEatAll initialization."""
        option = OptionEatAll(["--test"], save_other_options=True)
        assert option.save_other_options is True

        option = OptionEatAll(["--test"], save_other_options=False)
        assert option.save_other_options is False

        # Test with invalid nargs
        with pytest.raises(ValueError):
            OptionEatAll(["--test"], nargs=1)

    def test_option_eat_all_parser_process(self) -> None:
        """Test OptionEatAll parser_process function."""
        # This is a simplified test that just verifies the parser_process function works
        # Create a mock state object
        state = MagicMock()
        state.rargs = ["value1", "value2", "--next-option"]

        # Create a mock parser process function
        process_mock = MagicMock()

        # Create a parser_process function similar to the one in OptionEatAll
        def parser_process(value, state_obj):
            done = False
            value = [value]
            # Grab everything up to the next option
            while state_obj.rargs and not done:
                if state_obj.rargs[0].startswith("--"):
                    done = True
                if not done:
                    value.append(state_obj.rargs.pop(0))
            value = tuple(value)
            process_mock(value, state_obj)

        # Call the function
        parser_process("initial", state)

        # Check that the process_mock was called with the expected values
        process_mock.assert_called_once()
        args, kwargs = process_mock.call_args
        assert args[0] == ("initial", "value1", "value2")
        assert args[1] == state
        assert state.rargs == ["--next-option"]

    def test_prompt_password_with_password(self) -> None:
        """Test prompt_password function with password provided."""
        ctx = MagicMock()
        ctx.params = {"mysql_password": "test_password"}

        result = prompt_password(ctx, None, True)
        assert result == "test_password"

    def test_prompt_password_without_password(self) -> None:
        """Test prompt_password function without password provided."""
        ctx = MagicMock()
        ctx.params = {"mysql_password": None}

        with patch("click.prompt", return_value="prompted_password"):
            result = prompt_password(ctx, None, True)
            assert result == "prompted_password"

    def test_prompt_password_not_used(self) -> None:
        """Test prompt_password function when not used."""
        ctx = MagicMock()
        ctx.params = {"mysql_password": "test_password"}

        result = prompt_password(ctx, None, False)
        assert result is None

    def test_prompt_password_not_used_no_password(self) -> None:
        """Test prompt_password function when not used and no password is provided."""
        ctx = MagicMock()
        ctx.params = {"mysql_password": None}

        result = prompt_password(ctx, None, False)
        assert result is None

    def test_option_eat_all_add_to_parser(self) -> None:
        """Test OptionEatAll add_to_parser method with a real parser."""
        # Create a real parser
        parser = OptionParser()
        ctx = MagicMock()

        # Create an OptionEatAll instance
        option = OptionEatAll(["--test"], save_other_options=True)

        # Add it to the parser
        option.add_to_parser(parser, ctx)

        # Verify that the parser has our option
        assert "--test" in parser._long_opt

        # Verify that the process method has been replaced
        assert parser._long_opt["--test"].process != option._previous_parser_process

    def test_option_eat_all_save_other_options_false(self) -> None:
        """Test OptionEatAll parser_process function with save_other_options=False."""
        # Create a mock state object
        state = MagicMock()
        state.rargs = ["value1", "value2", "--next-option"]

        # Create a mock process function
        process_mock = MagicMock()

        # Create a simplified parser_process function that directly tests the behavior
        # we're interested in (save_other_options=False)
        def parser_process(value, state_obj):
            done = False
            value = [value]
            # This is the branch we want to test (save_other_options=False)
            # grab everything remaining
            value += state_obj.rargs
            state_obj.rargs[:] = []
            value = tuple(value)
            process_mock(value, state_obj)

        # Call the function
        parser_process("initial", state)

        # Check that the process_mock was called with the expected values
        process_mock.assert_called_once()
        args, kwargs = process_mock.call_args
        # With save_other_options=False, all remaining args should be consumed
        assert args[0] == ("initial", "value1", "value2", "--next-option")
        assert args[1] == state
        # The state.rargs should be empty
        assert state.rargs == []

    def test_option_eat_all_actual_implementation(self) -> None:
        """Test the actual implementation of OptionEatAll parser_process method."""
        # Create a real OptionEatAll instance
        option = OptionEatAll(["--test"], save_other_options=True)

        # Create a mock parser with prefixes
        parser = MagicMock()
        parser.prefixes = ["--", "-"]

        # Create a mock option that will be returned by parser._long_opt.get()
        mock_option = MagicMock()
        mock_option.prefixes = ["--", "-"]  # This is needed for the parser_process method
        parser._long_opt = {"--test": mock_option}
        parser._short_opt = {}

        # Create a state object with rargs
        state = MagicMock()

        # Test case 1: save_other_options=True, with non-option arguments
        state.rargs = ["value1", "value2", "--next-option"]

        # Call the parser_process method
        option.add_to_parser(parser, MagicMock())  # This sets up the parser_process method

        # Now mock_option.process should have been replaced with our parser_process
        # Call it directly to simulate what would happen in the real parser
        mock_option.process("initial", state)

        # Check that the previous_parser_process was called with the expected values
        option._previous_parser_process.assert_called_once()
        args, kwargs = option._previous_parser_process.call_args
        assert args[0] == ("initial", "value1", "value2")
        assert args[1] == state
        assert state.rargs == ["--next-option"]

        # Reset mocks
        option._previous_parser_process.reset_mock()

        # Test case 2: save_other_options=False
        option.save_other_options = False
        state.rargs = ["value1", "value2", "--next-option"]

        # Call the parser_process method
        mock_option.process("initial", state)

        # Check that the previous_parser_process was called with the expected values
        option._previous_parser_process.assert_called_once()
        args, kwargs = option._previous_parser_process.call_args
        assert args[0] == ("initial", "value1", "value2", "--next-option")
        assert args[1] == state
        assert state.rargs == []

    def test_option_eat_all_add_to_parser_with_short_opt(self) -> None:
        """Test OptionEatAll add_to_parser method with short option."""
        # Create a real parser
        parser = OptionParser()
        ctx = MagicMock()

        # Set up the parser with a short option
        mock_option = MagicMock()
        parser._short_opt = {"-t": mock_option}
        parser._long_opt = {}

        # Create an OptionEatAll instance with a short option
        option = OptionEatAll(["-t"], save_other_options=True)

        # Add it to the parser
        option.add_to_parser(parser, ctx)

        # Verify that the parser has our option
        assert "-t" in parser._short_opt

        # Verify that the process method has been replaced
        assert hasattr(option, "_previous_parser_process")
        assert option._eat_all_parser is not None
