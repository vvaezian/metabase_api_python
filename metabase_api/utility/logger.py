import logging
import pathlib
import os
import sys
from typing import Optional


def setup(
    only_to_stdout: bool = False, hint_opt: Optional[str] = None
) -> Optional[pathlib.Path]:
    """
    Properly setups a logger. Writes INFO+ to stdout and DEBUG to a file
    Args:
        only_to_stdout:
        hint_opt: a certain hint used to create the DEBUG file.

    Returns: Optionally (if only_to_stdout == False): a Path, pointing to the DEBUG file.

    """
    log_fmt = "%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s"
    if only_to_stdout:
        logging.basicConfig(format=log_fmt, stream=sys.stdout, level=logging.DEBUG)
        return None
    else:
        user_name = os.environ.get("USER")
        log_dir = pathlib.Path(f"/tmp/{user_name}/logs")
        log_file_name = str(hint_opt if hint_opt is not None else user_name) + "_log"
        log_path = (log_dir / log_file_name).with_suffix(".log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Will log activity into '{log_path}'")
        logging.basicConfig(
            format=log_fmt,
            filename=log_path,
            filemode="w",
            level=logging.DEBUG,
        )
        # stdout
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG if only_to_stdout else logging.INFO)
        stdout_handler.setFormatter(logging.Formatter(log_fmt))
        # I will also change the logging for 'requests' and 'urllib3',
        # because they are VERY noisy
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("hpack").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        # add the handler to the root logger
        logging.getLogger("").addHandler(stdout_handler)
        return log_path


if __name__ == "__main__":
    dict_setup = {"setup1": lambda: setup()}
    for n, f_setup in dict_setup.items():
        f_setup()
        _logger = logging.getLogger(__name__)
        _logger.info(f"[{n}] hello, this is an info")
        _logger.debug(f"[{n}] hello, this is a DEBUG")
        _logger.warning(f"[{n}] hello, this is a WARNING")
        _logger.error(f"[{n}] hello, this is an ERROR")
