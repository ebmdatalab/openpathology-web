import errno
import os
import os.path
import tempfile


def get_temp_filename(filename):
    """
    Return the name of a temporary file in the same directory as the supplied
    file
    """
    directory, basename = os.path.split(filename)
    if directory == '':
        directory = '.'
    _ensure_dir_exists(directory)
    # We want to return the name of the file without actually creating it as
    # sometimes we use this to create a new SQLite file and SQLite will
    # complain if the file already exists
    return "{directory}/.tmp.{random}.{basename}".format(
        directory=directory,
        basename=basename,
        random=next(tempfile._get_candidate_names()),
    )


def _ensure_dir_exists(directory):
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
