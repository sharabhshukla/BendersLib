# coding:utf-8

import sys
import logging
import time

from .consts import BendersConsts as CST
# from .core import BendersBase
from . import __version__, __author__, __url__, __copyright__, __license__

logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(console_handler)


# file_handler = logging.FileHandler('log.txt', encoding='utf-8')
# file_handler.setFormatter(logging.Formatter('%(message)s'))
# logger.addHandler(file_handler)


class BendersLogger:

    def __init__(self, benders):
        self.benders = benders
        self.params = benders.params
        self.result = benders.result

    def log_title(self):
        if self.params.log_to_console:
            l = CST.LOG_ITER_WIDTH * 7
            logging.info("=" * l)
            logging.info(f"BendersLib (v{__version__}, {__license__}, {__url__}) by {__author__} ({__copyright__})")
            logging.info("-" * l)

            logging.info(self.benders)
            logging.info(self.benders.master_problem)
            logging.info(self.benders.sub_problem)
            logging.info(self.params)

            logging.info("-" * l)
            logging.info(
                f"{'Iter.':>{CST.LOG_ITER_WIDTH}}, "
                f"{'LB':>{CST.LOG_ITER_WIDTH}}, "
                f"{'UB':>{CST.LOG_ITER_WIDTH}}, "
                f"{'Obj.':>{CST.LOG_ITER_WIDTH}}, "
                f"{'Gap(%)':>{CST.LOG_ITER_WIDTH}}, "
                f"{'Runtime(s)':>{CST.LOG_ITER_WIDTH}}")
            logging.info("-" * l)

    def log_line(self, time_start, time_pre_log):
        current_time = time.perf_counter()
        if current_time - time_pre_log >= self.params.log_freq_sec or time_pre_log == time_start:
            _time_pre_log = current_time
            if self.params.log_to_console:
                logging.info(
                    f"{self.result.n_iter:{CST.LOG_ITER_WIDTH}}, "
                    f"{self.result.lb:>{CST.LOG_ITER_WIDTH}.2f}, "
                    f"{self.result.ub:>{CST.LOG_ITER_WIDTH}.2f}, "
                    f"{self.result.obj:>{CST.LOG_ITER_WIDTH}.2f}, "
                    f"{self.result.gap * 100:>{CST.LOG_ITER_WIDTH}.2f}, "
                    f"{self.result.runtime:>{CST.LOG_ITER_WIDTH}.2f}"
                )
            return _time_pre_log
        return time_pre_log

    def log_end(self):
        l = CST.LOG_ITER_WIDTH * 7
        if self.params.log_to_console:
            logging.info(
                f"{self.result.n_iter:{CST.LOG_ITER_WIDTH}}, "
                f"{self.result.lb:>{CST.LOG_ITER_WIDTH}.2f}, "
                f"{self.result.ub:>{CST.LOG_ITER_WIDTH}.2f}, "
                f"{self.result.obj:>{CST.LOG_ITER_WIDTH}.2f}, "
                f"{self.result.gap * 100:>{CST.LOG_ITER_WIDTH}.2f}, "
                f"{self.result.runtime:>{CST.LOG_ITER_WIDTH}.2f}"
            )
            logging.info("-" * l)
            logging.info(self.result)
            logging.info("=" * l)

            if self.params.log_file:
                logging.info(f"Log file (level: {self.params.log_level}) saved to: '{self.params.log_file}'")


if __name__ == "__main__":
    pass
