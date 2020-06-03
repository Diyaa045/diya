import pytest
from .fixtures import make_app_client


@pytest.fixture
def canned_write_client():
    for client in make_app_client(
        extra_databases={"data.db": "create table names (name text)"},
        metadata={
            "databases": {
                "data": {
                    "queries": {
                        "add_name": {
                            "sql": "insert into names (name) values (:name)",
                            "write": True,
                            "on_success_redirect": "/data/add_name?success",
                        },
                        "add_name_specify_id": {
                            "sql": "insert into names (rowid, name) values (:rowid, :name)",
                            "write": True,
                            "on_error_redirect": "/data/add_name_specify_id?error",
                        },
                        "delete_name": {
                            "sql": "delete from names where rowid = :rowid",
                            "write": True,
                            "on_success_message": "Name deleted",
                        },
                        "update_name": {
                            "sql": "update names set name = :name where rowid = :rowid",
                            "params": ["rowid", "name"],
                            "write": True,
                        },
                    }
                }
            }
        },
    ):
        yield client


def test_insert(canned_write_client):
    response = canned_write_client.post(
        "/data/add_name", {"name": "Hello"}, allow_redirects=False
    )
    assert 302 == response.status
    assert "/data/add_name?success" == response.headers["Location"]
    messages = canned_write_client.ds.unsign(
        response.cookies["ds_messages"], "messages"
    )
    assert [["Query executed, 1 row affected", 1]] == messages


def test_custom_success_message(canned_write_client):
    response = canned_write_client.post(
        "/data/delete_name", {"rowid": 1}, allow_redirects=False
    )
    assert 302 == response.status
    messages = canned_write_client.ds.unsign(
        response.cookies["ds_messages"], "messages"
    )
    assert [["Name deleted", 1]] == messages


def test_insert_error(canned_write_client):
    canned_write_client.post("/data/add_name", {"name": "Hello"})
    response = canned_write_client.post(
        "/data/add_name_specify_id",
        {"rowid": 1, "name": "Should fail"},
        allow_redirects=False,
    )
    assert 302 == response.status
    assert "/data/add_name_specify_id?error" == response.headers["Location"]
    messages = canned_write_client.ds.unsign(
        response.cookies["ds_messages"], "messages"
    )
    assert [["UNIQUE constraint failed: names.rowid", 3]] == messages
    # How about with a custom error message?
    canned_write_client.ds._metadata["databases"]["data"]["queries"][
        "add_name_specify_id"
    ]["on_error_message"] = "ERROR"
    response = canned_write_client.post(
        "/data/add_name_specify_id",
        {"rowid": 1, "name": "Should fail"},
        allow_redirects=False,
    )
    assert [["ERROR", 3]] == canned_write_client.ds.unsign(
        response.cookies["ds_messages"], "messages"
    )
