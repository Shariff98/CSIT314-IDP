"""Production hosting: Flask serves the built React app at / when FRONTEND_DIST is set."""
from app import create_app
from tests.chatbot_helpers import FakeLLMGateway


def make_app(tmp_path, dist):
    return create_app(db_path=str(tmp_path / "t.db"), upload_dir=str(tmp_path / "up"),
                      llm_gateway=FakeLLMGateway(), frontend_dist=dist).test_client()


def make_dist(tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<div id=root>react app</div>")
    (dist / "assets" / "app.js").write_text("console.log(1)")
    (dist / "project-kitchen.svg").write_text("<svg/>")
    return str(dist)


def test_root_is_the_react_app_when_dist_is_set(tmp_path):
    client = make_app(tmp_path, make_dist(tmp_path))
    res = client.get("/")
    assert res.status_code == 200 and b"react app" in res.data


def test_assets_and_public_files_are_served(tmp_path):
    client = make_app(tmp_path, make_dist(tmp_path))
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/project-kitchen.svg").status_code == 200


def test_unknown_paths_and_path_tricks_are_404(tmp_path):
    client = make_app(tmp_path, make_dist(tmp_path))
    for path in ("/nope.js", "/assets/missing.js", "/../app.py", "/assets/../../app.py"):
        assert client.get(path).status_code == 404


def test_api_and_old_pages_still_work(tmp_path):
    client = make_app(tmp_path, make_dist(tmp_path))
    assert client.post("/api/chat", json={"message": "hi"}).status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/login").status_code == 200


def test_off_by_default(tmp_path):
    client = make_app(tmp_path, None)
    assert b"react app" not in client.get("/").data
    assert client.get("/project-kitchen.svg").status_code == 404


def test_missing_dist_folder_is_ignored(tmp_path):
    assert make_app(tmp_path, str(tmp_path / "nothing")).get("/login").status_code == 200


def test_logging_out_of_the_flask_pages_returns_to_the_react_app(tmp_path):
    client = make_app(tmp_path, make_dist(tmp_path))
    res = client.get("/logout")
    assert res.status_code == 302 and res.headers["Location"].endswith("/#/login")


def test_logout_without_react_keeps_the_html_login_page(tmp_path):
    res = make_app(tmp_path, None).get("/logout")
    assert res.headers["Location"].endswith("/login")


def test_unknown_api_paths_are_json_even_with_react_served(tmp_path):
    res = make_app(tmp_path, make_dist(tmp_path)).get("/api/missing")
    assert res.status_code == 404 and res.json["error"]["code"] == "not_found"
