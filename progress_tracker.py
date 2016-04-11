import logger

__author__ = "Brian Schkerke"
__copyright__ = "Copyright 2016 Brian Schkerke"
__license__ = "MIT"


class ProgressTracker(object):
    order_count_current = 0
    order_count_total = 0

    subproduct_count_current = 0
    subproduct_count_total = 0

    download_count_current = 0
    download_count_total = 0

    download_size_current = 0
    download_size_total = 0

    current_product = ""
    current_subproduct = ""
    current_download = ""

    @staticmethod
    def display_summary():
        progress_message = "O: %d/%d SP: %d/%d D: %d/%d DL: %s/%s (%s)" % (ProgressTracker.order_count_current,
            ProgressTracker.order_count_total, ProgressTracker.subproduct_count_current,
            ProgressTracker.subproduct_count_total, ProgressTracker.download_count_current,
            ProgressTracker.download_count_total,
            ProgressTracker.format_filesize(ProgressTracker.download_size_current),
            ProgressTracker.format_filesize(ProgressTracker.download_size_total),
            ProgressTracker.format_percentage(ProgressTracker.download_size_current,
                                              ProgressTracker.download_size_total))

        logger.display_message(False, "Progress", progress_message)
        logger.display_message(True, "Progress", "Product: %s" % ProgressTracker.current_product)
        logger.display_message(True, "Progress", "Subproduct: %s" % ProgressTracker.current_subproduct)
        logger.display_message(True, "Progress", "Download: %s" % ProgressTracker.current_download)


    @staticmethod
    def format_filesize(filesize):
        prefixes = ['B', 'Kb', 'Mb', 'Gb', 'Tb']
        index_level = 0

        while abs(filesize / 1024) > 0:
            index_level += 1
            filesize /= 1024

        return "%d%s" % (filesize, prefixes[index_level])

    @staticmethod
    def format_percentage(current, total):
        return '{percent:.2%}'.format(percent=(1.0 * current)/total)
