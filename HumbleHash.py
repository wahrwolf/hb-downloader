from __future__ import division
import os
import hashlib
from Events import Events
import configuration


class HumbleHash(object):
    @staticmethod
    def calculate_hash(full_filename):
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
        stored_md5hash = HumbleHash.read_md5(full_filename)
        if len(stored_md5hash) == 0:
            stored_md5hash = HumbleHash.calculate_hash(full_filename)

        if stored_md5hash != md5_hash:
            return False
        else:
            return True

    @staticmethod
    def _check_percent(current, total, current_percentage):
        percentage = current / total * 100
        percentage -= percentage % 10
        if current_percentage < percentage:
            current_percentage = percentage
            Events.trigger(configuration.EVENT_PROGRESS, current_percentage)

        return current_percentage

    @staticmethod
    def remove_md5file(full_filename):
        md5full_filename = HumbleHash.md5filename(full_filename)

        if os.path.exists(md5full_filename):
            os.remove(md5full_filename)

    @staticmethod
    def read_md5(full_filename):
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

        f.close()

        if md5line is None:
            return ""
        else:
            return md5line[0:32]

    @staticmethod
    def write_md5(full_filename, md5_hash):
        if not configuration.write_md5:
            return ""

        md5full_filename = HumbleHash.md5filename(full_filename)
        local_filename = os.path.basename(md5full_filename)

        if os.path.exists(md5full_filename):
            os.remove(md5full_filename)

        if md5_hash is None:
            md5_hash = HumbleHash.calculate_hash(full_filename)

        with open(md5full_filename, "wb") as f:
            f.write(md5_hash + " *%s" % local_filename)

        f.close()

    @staticmethod
    def md5filename(full_filename):
        full_filename += ".md5"
        return full_filename
