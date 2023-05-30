import argparse
import logging
import os.path
import shutil
from filecmp import dircmp
from time import sleep


def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('source',
                        help="Folder which acts as a source for syncing.")
    parser.add_argument('replica',
                        help="Folder that acts as a replica for syncing.")
    parser.add_argument('--interval',
                        default=10,
                        type=int,
                        help="Syncing interval in seconds.")
    parser.add_argument('--log_file',
                        default='sync_log.txt',
                        help="Text file to which the logging information "
                             "will be written. The same information will "
                             "appear on the terminal.")
    return parser.parse_args()


class Sync:
    def __init__(self, source: str, replica: str, interval: int,
                 log_file: str) -> None:
        self.source = source
        self.replica = replica
        self.interval = interval

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        stream_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(log_file)
        log_format = logging.Formatter("%(asctime)s - %(message)s",
                                       datefmt='%d-%m-%Y %H:%M:%S')
        stream_handler.setFormatter(log_format)
        file_handler.setFormatter(log_format)
        self.logger.addHandler(stream_handler)
        self.logger.addHandler(file_handler)

    def _copy(self, src: str, dst: str) -> None:
        if os.path.isdir(src):
            dst_name = os.path.join(dst, os.path.basename(src))
            os.mkdir(dst_name)
            self.logger.info("Created folder `%s`.", dst_name)
            for child in os.listdir(src):
                self._copy(os.path.join(src, child), dst_name)
        else:
            shutil.copy2(src, dst)
            self.logger.info("Copied file `%s` to `%s`.", src,
                             os.path.join(dst, os.path.basename(src)))

    def _remove(self, pth: str) -> None:
        if os.path.isdir(pth):
            for child in os.listdir(pth):
                self._remove(os.path.join(pth, child))
            os.rmdir(pth)
            self.logger.info("Removed folder `%s`.", pth)
        else:
            os.remove(pth)
            self.logger.info("Removed file `%s`.", pth)

    def _folder_sync(self, source: str, replica: str) -> None:
        comparison = dircmp(source, replica)
        for f in comparison.left_only:
            self._copy(os.path.join(source, f), replica)
        for f in comparison.right_only:
            self._remove(os.path.join(replica, f))
        for f in comparison.diff_files:
            self._copy(os.path.join(source, f), replica)
        for d in comparison.common_dirs:
            self._folder_sync(os.path.join(source, d),
                              os.path.join(replica, d))

    def run(self) -> None:
        while True:
            self._folder_sync(self.source, self.replica)
            sleep(self.interval)


if __name__ == '__main__':
    shutil.copytree('test_left', 'left', dirs_exist_ok=True)
    shutil.copytree('test_right', 'right', dirs_exist_ok=True)

    args = getargs()
    sync = Sync(args.source, args.replica, args.interval, args.log_file)
    sync.run()
