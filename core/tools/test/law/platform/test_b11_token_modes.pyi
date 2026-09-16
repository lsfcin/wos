from _typeshed import Incomplete

posix_only: Incomplete

@posix_only
def test_secure_dir_leaves_a_directory_owner_only(tmp_path) -> None: ...
@posix_only
def test_secure_file_makes_an_existing_file_owner_only(tmp_path) -> None: ...
@posix_only
def test_the_token_config_dir_is_written_tight(tmp_path, monkeypatch): ...
