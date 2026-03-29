# coding:utf-8

import sys
import logging
import time

from .consts import BendersConsts as CST
from . import __version__, __author__, __url__, __copyright__, __license__


class BendersLogger:

    def __init__(self, benders):
        self.benders = benders
        self.result = benders.result
        self._is_setup = False
        self._last_log_iter = -1
        self.logger = logging.getLogger("BendersLib")

    def setup(self):
        if self._is_setup:
            return

        logger = self.logger
        logger.propagate = False

        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        logger.setLevel(logging.INFO)

        params = self.benders.params

        if params.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter('%(message)s'))
            logger.addHandler(console_handler)

        if params.log_file:
            file_handler = logging.FileHandler(params.log_file, mode='w', encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(message)s'))
            logger.addHandler(file_handler)

        if not logger.hasHandlers():
            logger.addHandler(logging.NullHandler())

        self._is_setup = True

    def log_title(self):
        self.setup()

        l = CST.LOG_ITER_WIDTH * 7
        self.logger.info("=" * l)
        self.logger.info(f"BendersLib (v{__version__}, {__license__}, {__url__}) Copyright {__copyright__}")
        self.logger.info("-" * l)

        self.logger.info(self.benders)
        self.logger.info(self.benders.master_problem)
        self.logger.info(self.benders.sub_problem)
        self.logger.info(self.benders.params)

        self.logger.info("-" * l)
        self.logger.info(
            f"{'Iter.':>{CST.LOG_ITER_WIDTH}}, "
            f"{'LB':>{CST.LOG_ITER_WIDTH}}, "
            f"{'UB':>{CST.LOG_ITER_WIDTH}}, "
            f"{'Obj.':>{CST.LOG_ITER_WIDTH}}, "
            f"{'Gap(%)':>{CST.LOG_ITER_WIDTH}}, "
            f"{'Runtime(s)':>{CST.LOG_ITER_WIDTH}}")
        self.logger.info("-" * l)

    def log_line(self, time_start, time_pre_log):
        self.setup()

        current_time = time.perf_counter()
        if current_time - time_pre_log >= self.benders.params.log_freq_sec or time_pre_log == time_start:
            _time_pre_log = current_time
            self.logger.info(
                f"{self.result.n_iter:{CST.LOG_ITER_WIDTH}}, "
                f"{self.result.lb:>{CST.LOG_ITER_WIDTH}.2f}, "
                f"{self.result.ub:>{CST.LOG_ITER_WIDTH}.2f}, "
                f"{self.result.obj:>{CST.LOG_ITER_WIDTH}.2f}, "
                f"{self.result.gap * 100:>{CST.LOG_ITER_WIDTH}.2f}, "
                f"{self.result.runtime:>{CST.LOG_ITER_WIDTH}.2f}"
            )
            if self.result.n_iter > self._last_log_iter:
                self._last_log_iter = self.result.n_iter
            return _time_pre_log
        return time_pre_log

    def log_end(self):
        self.setup()

        if self._last_log_iter != self.result.n_iter:
            self.logger.info(
                f"{self.result.n_iter:{CST.LOG_ITER_WIDTH}}, "
                f"{self.result.lb:>{CST.LOG_ITER_WIDTH}.2f}, "
                f"{self.result.ub:>{CST.LOG_ITER_WIDTH}.2f}, "
                f"{self.result.obj:>{CST.LOG_ITER_WIDTH}.2f}, "
                f"{self.result.gap * 100:>{CST.LOG_ITER_WIDTH}.2f}, "
                f"{self.result.runtime:>{CST.LOG_ITER_WIDTH}.2f}"
            )

        l = CST.LOG_ITER_WIDTH * 7
        self.logger.info("-" * l)
        self.logger.info(self.result)
        self.logger.info("=" * l)

        params = self.benders.params
        if params.log_file:
            self.logger.info(f"Log file (level: {params.log_level}) saved to: '{params.log_file}'")

    @staticmethod
    def warning(msg: str):
        logging.warning(msg)
