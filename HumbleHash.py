from __future__ import division
import os
import hashlib
from Events import Events
import configuration

__author__ = "Brian Schkerke"
__copyright__ = "Copyright 2016 Brian Schkerke"
__license__ = "MIT"

__all__ = ["HumbleHash"]


class HumbleHash(object):
    """
        HumbleHash is the central repository for all code related to calculating and maintaining
        MD5 checksums for the Humble Bundle downloader.
    """
    @staticmethod
    def calculate_hash(full_filename):
        """
            Calculates the MD5 checksum for the given file and returns the hex representation.

            :param full_filename:  The full path and filename of the file to calculate the MD5 for.
            :return:  The hex representation of the MD5 hash.
        """
        current_percentage = 0
        if not os.path.exists(full_filename):
            return ""

        with open(full_filename, "rb") as f:
            total_length = os.path.getsize(full_filename)
            read_bytes = 0

            Events.trigger(configuration.EVENT_MD5_START, full_filename)

            md5_hash = hashlib.md5()
            while True:
                data = f.read(configuration.chunk_size)
                read_bytes += configuration.chunk_size
                read_bytes = min(total_length, read_bytes)

                if not data:
                    break

                md5_hash.update(data)
                current_percentage = HumbleHash._check_percent(read_bytes, total_length, current_percentage)

            Events.trigger(configuration.EVENT_MD5_END, full_filename)
            HumbleHash.write_md5(full_filename, md5_hash.hexdigest())
            return md5_hash.hexdigest()

    @staticmethod
    def check_hash(full_filename, md5_hash):
        """
            Compares the checksum for the given filename against the given hash.  First checks for the
            existence of an MD5 file and reads the MD5 value from it, if possible.  Otherwise it
            calculates the MD5 of the given file and returns whether it matches the given hash.

            :param full_filename:  The full path and filename of the file to calculate and compare the MD5 hash for.
            :param md5_hash:  The MD5 hash we're comparing the file against; generally read from humblebundle.com.
            :return:  True if the MD5 hash of the given file matches the provided md5_hash.
        """
        stored_md5hash = HumbleHash.read_md5(full_filename)
        if len(stored_md5hash) == 0:
            stored_md5hash = HumbleHash.calculate_hash(full_filename)

        return stored_md5hash == md5_hash

    @staticmethod
    def _check_percent(current, total, current_percentage):
        """
            Checks whether the current progress exceeds the current percentage.  Used to determine whether
            an event should be fired.

            :param current:  The current progress in whatever proprietary format your heart desires.
            :param total:  The total progress in whatever proprietary format your heart desires.
            :param current_percentage:  The current progress percentage as last defined.
            :return:  The new value for the current_percentage, if it is modified.
        """
        percentage = current / total * 100
        percentage -= percentage % 10
        if current_percentage < percentage:
            current_percentage = percentage
            Events.trigger(configuration.EVENT_PROGRESS, current_percentage)

        return current_percentage

    @staticmethod
    def remove_md5file(full_filename):
        """
            Removes an MD5 file from storage.

            :param full_filename:  The full path and filename of the file to remove the MD5 checksum for.
            :return:  None
        """
        md5full_filename = HumbleHash.md5filename(full_filename)

        if os.path.exists(md5full_filename):
            os.remove(md5full_filename)

    @staticmethod
    def read_md5(full_filename):
        """
            Reads an MD5 hash from an MD5 file.

            :param full_filename:  The full path and filename of the file to attempt to read the MD5 file.
            :return:  The MD5 value read, or an empty string if no file was found or its format was invalid.
        """
        if not configuration.read_md5:
            return ""

        md5full_filename = HumbleHash.md5filename(full_filename)
        local_filename = os.path.basename(md5full_filename)

        if not os.path.exists(md5full_filename):
            return ""

        md5line = None

        with open(md5full_filename, "r") as f:
            for line in f:
                if line.endswith(local_filename):
                    md5line = line
                    break

        if md5line is None or len(md5line) == 0:
            return ""
        else:
            return md5line[0:32]

    @staticmethod
    def write_md5(full_filename, md5_hash):
        """
            Writes an MD5 file for a given filename.  If md5_hash is not provided the hash
            will be calculated prior to write.

            :param full_filename:  The full path and filename of the file to create an MD5 file for.
            :param md5_hash:  The MD5 hash value of the given file, if known.
            :return:  None
        """
        if not configuration.write_md5:
            return

        md5full_filename = HumbleHash.md5filename(full_filename)
        local_filename = os.path.basename(md5full_filename)

        if os.path.exists(md5full_filename):
            os.remove(md5full_filename)

        if md5_hash is None:
            md5_hash = HumbleHash.calculate_hash(full_filename)

        with open(md5full_filename, "wb") as f:
            f.write(md5_hash + " *%s" % local_filename)

    @staticmethod
    def md5filename(full_filename):
        """
            Calculates and returns the MD5 filename for a given file.

            :param full_filename:  The full path and filename of the file to calculate the MD5 location for.
            :return: A string representing the MD5 filename for the given file.
            :raise ValueError:  If full_filename is not specified upon function execution.
        """
        if full_filename is None or len(full_filename) == 0:
            raise ValueError("full_filename must be specified in call to md5filename.")

        full_filename += ".md5"
        return full_filename
