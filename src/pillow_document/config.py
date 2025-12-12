import logging

logger = logging.getLogger("pillow-document-writer")
logger.addHandler(logging.NullHandler())

debugging: bool


def debug(debug_on: bool = True, default_handler: bool = True) -> None:
    """Turn on/off debugging of DICOM file reading and writing.

    When debugging is on, file location and details about the elements read at
    that location are logged to the 'pydicom' logger using Python's
    :mod:`logging`
    module.

    Parameters
    ----------
    debug_on : bool, optional
        If ``True`` (default) then turn on debugging, ``False`` to turn off.
    default_handler : bool, optional
        If ``True`` (default) then use :class:`logging.StreamHandler` as the
        handler for log messages.
    """
    global logger, debugging

    if default_handler:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if debug_on:
        logger.setLevel(logging.DEBUG)
        debugging = True
    else:
        logger.setLevel(logging.WARNING)
        debugging = False


debug(False, False)
