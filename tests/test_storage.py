import boto3
import pytest
from moto import mock_aws

from app.core import storage as storage_module
from app.core.storage import LocalStorage, S3Storage, build_storage, new_image_key

KEY = "posts/7/0123456789abcdef0123456789abcdef.jpg"


def test_new_image_keys_are_unique_and_valid():
    keys = {new_image_key(7) for _ in range(200)}
    assert len(keys) == 200
    assert all(storage_module.KEY_RE.match(k) for k in keys)


@pytest.mark.parametrize(
    "bad_key",
    [
        "../etc/passwd",
        "/etc/passwd",
        "posts/7/../../x.jpg",
        "posts/7/arquivo.jpg",
        "posts/x/0123456789abcdef0123456789abcdef.jpg",
        "posts/7/0123456789abcdef0123456789abcdef.png",
        "",
    ],
)
async def test_local_storage_rejects_suspicious_keys(tmp_path, bad_key):
    store = LocalStorage(str(tmp_path), "https://x.com")
    with pytest.raises(ValueError, match="inválida"):
        await store.save(bad_key, b"x")
    with pytest.raises(ValueError, match="inválida"):
        await store.delete(bad_key)
    assert list(tmp_path.rglob("*")) == []


async def test_local_storage_roundtrip(tmp_path):
    store = LocalStorage(str(tmp_path / "media"), "https://exemplo.com/")
    await store.save(KEY, b"dados")
    assert (tmp_path / "media" / KEY).read_bytes() == b"dados"
    assert not list((tmp_path / "media").rglob("*.tmp")), "arquivo temporário não pode sobrar"
    assert store.public_url(KEY) == f"https://exemplo.com/media/{KEY}"

    await store.delete(KEY)
    assert not (tmp_path / "media" / KEY).exists()
    await store.delete(KEY)  # apagar o que não existe não é erro


async def test_s3_storage_with_moto():
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="meu-bucket")
        store = S3Storage("meu-bucket", "https://cdn.exemplo.com/", client=client)

        await store.save(KEY, b"jpegdata")
        obj = client.get_object(Bucket="meu-bucket", Key=KEY)
        assert obj["Body"].read() == b"jpegdata"
        assert obj["ContentType"] == "image/jpeg"
        assert "immutable" in obj["CacheControl"]
        assert store.public_url(KEY) == f"https://cdn.exemplo.com/{KEY}"

        await store.delete(KEY)
        assert "Contents" not in client.list_objects_v2(Bucket="meu-bucket")

        with pytest.raises(ValueError, match="inválida"):
            await store.save("../fora.jpg", b"x")


async def test_s3_storage_builds_client_from_settings_with_empty_endpoint(monkeypatch):
    """Variável vazia no .env chega como "" e não pode virar endpoint_url="" no boto3."""
    s = storage_module.settings
    for name, value in {
        "S3_ENDPOINT_URL": "",
        "S3_REGION": "us-east-1",
        "S3_ACCESS_KEY_ID": "id",
        "S3_SECRET_ACCESS_KEY": "segredo",
    }.items():
        monkeypatch.setattr(s, name, value)
    with mock_aws():
        store = S3Storage("meu-bucket", "https://cdn.exemplo.com")  # cria o cliente de verdade, sem injetar
        store.client.create_bucket(Bucket="meu-bucket")
        await store.save(KEY, b"x")
        assert store.client.get_object(Bucket="meu-bucket", Key=KEY)["Body"].read() == b"x"


def test_build_storage_validates_configuration(monkeypatch, tmp_path):
    s = storage_module.settings
    monkeypatch.setattr(s, "STORAGE_BACKEND", "ftp")
    with pytest.raises(RuntimeError, match="inválido"):
        build_storage()

    monkeypatch.setattr(s, "STORAGE_BACKEND", "s3")
    monkeypatch.setattr(s, "S3_BUCKET", None)
    with pytest.raises(RuntimeError, match="S3_BUCKET"):
        build_storage()

    for name, value in {
        "S3_BUCKET": "b",
        "S3_PUBLIC_BASE_URL": "https://cdn.exemplo.com",
        "S3_ACCESS_KEY_ID": "id",
        "S3_SECRET_ACCESS_KEY": "segredo",
    }.items():
        monkeypatch.setattr(s, name, value)
    assert isinstance(build_storage(), S3Storage)

    monkeypatch.setattr(s, "STORAGE_BACKEND", "local")
    monkeypatch.setattr(s, "MEDIA_ROOT", str(tmp_path / "m"))
    assert isinstance(build_storage(), LocalStorage)
