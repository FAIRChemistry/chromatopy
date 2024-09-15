import importlib.resources as pkg_resources

import toml


def read_static_file(path, filename: str):
    """Reads a static file from the specified library path.

    Args:
        path (Module): Import path of the library.
        filename (str): The name of the file to read.

    Returns:
        dict: The contents of the file as a dictionary.
    """

    source = pkg_resources.files(path).joinpath(filename)
    with pkg_resources.as_file(source) as file:
        return toml.load(file)
