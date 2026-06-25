"""File for configuring test cases"""
import logging
import subprocess
import pytest

from subprocess import PIPE

# class InteractiveCommand(subprocess.Popen):
#     def send(self, text):
#         """Send text to the interactive command"""
#         assert self.stdin is not None
#         assert self.stdout is not None
#         self.stdin.write(text)
#         self.stdin.flush()
#         return self.stdout.readline().decode("utf-8").strip()

#     def read(self):
#         assert self.stdin is not None
#         assert self.stdout is not None
#         return self.stdout.read().decode("utf-8").strip()

#     def terminate(self):
#         assert self.stdin is not None
#         self.stdin.close()
#         self.terminate()
#         self.wait(timeout=0.2)


class CommandRunner:
    """A utility class for running commands and logging info"""

    @staticmethod
    def run(command: str) -> subprocess.CompletedProcess:
        import os
        args = command.split()
        if args and args[0] == "pypi":
            args = ["python", "-m", "pypi_cli"] + args[1:]
        env = os.environ.copy()
        env["COLUMNS"] = "200"
        return subprocess.run(args, check=True, stdout=PIPE, stderr=PIPE, env=env)

    # @staticmethod
    # def run_interactive(command: str) -> "InteractiveCommand":
    #     """Runs a command with popen

    #     Parameters
    #     ----------
    #     command : str
    #         The command content as a string

    #     Returns
    #     -------
    #     InteractiveCommand
    #         The interactive command object
    #     """
    #     return InteractiveCommand(
    #         command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    #     )

    @staticmethod
    def log(text: str) -> None:
        """Logs some information

        Parameters
        ----------
        text : str
            The text to log
        """
        logging.info(text)


@pytest.fixture(scope="module")
def runner():
    """Returns the global CommandRunner instance"""
    return CommandRunner
