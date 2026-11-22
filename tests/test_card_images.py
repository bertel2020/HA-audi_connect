"""The card editor offers the pictures in the www folder."""

from custom_components.ha_audi_connect.card import list_www_images


def test_lists_pictures_as_local_paths(tmp_path):
    (tmp_path / "audi.png").write_bytes(b"")
    (tmp_path / "cars").mkdir()
    (tmp_path / "cars" / "a6 front.JPG").write_bytes(b"")
    (tmp_path / "notes.txt").write_bytes(b"")

    assert list_www_images(tmp_path) == [
        {"path": "/local/audi.png", "name": "audi.png"},
        {"path": "/local/cars/a6%20front.JPG", "name": "cars/a6 front.JPG"},
    ]


def test_skips_hidden_and_community_folders(tmp_path):
    for folder in (".hidden", "community"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "x.png").write_bytes(b"")
    (tmp_path / ".dot.png").write_bytes(b"")

    assert list_www_images(tmp_path) == []


def test_missing_folder_is_an_empty_list(tmp_path):
    assert list_www_images(tmp_path / "nothing") == []
