from app.core.config import Settings


def _settings(url: str) -> Settings:
    return Settings(
        DATABASE_URL=url,
        JWT_SECRET="un-secreto-de-desarrollo-cualquiera",
        DEBUG=True,
        _env_file=None,
    )


def test_normaliza_el_esquema_de_railway():
    """Railway entrega postgres://, que SQLAlchemy 2.0 ya no acepta."""
    s = _settings("postgres://user:pass@host:5432/db")
    assert s.DATABASE_URL.startswith("postgresql://")


def test_no_toca_una_url_ya_correcta():
    url = "postgresql://user:pass@host:5432/db"
    assert _settings(url).DATABASE_URL == url


def test_solo_reemplaza_el_esquema_no_el_resto():
    """Una contraseña que contenga 'postgres://' no debe alterarse."""
    s = _settings("postgres://user:postgres%3A%2F%2Fx@host:5432/db")
    assert s.DATABASE_URL == "postgresql://user:postgres%3A%2F%2Fx@host:5432/db"


def test_cors_origins_se_parte_en_lista():
    s = _settings("postgresql://x@h/d")
    s.CORS_ORIGINS = "https://uno.app, https://dos.app"
    assert s.cors_origins_list == ["https://uno.app", "https://dos.app"]
