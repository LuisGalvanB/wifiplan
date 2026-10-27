from app.core.config import settings
from app.services import storage


def test_presigned_url_uses_public_endpoint_for_signature(monkeypatch):
    endpoints: list[str | None] = []
    expected_url = "https://files.example.test/floorplans/asset.png?signature=test"

    class Presigner:
        def generate_presigned_url(self, operation, Params, ExpiresIn):
            assert operation == "get_object"
            assert Params == {"Bucket": "floorplans", "Key": "asset.png"}
            assert ExpiresIn == 3600
            return expected_url

    def create_client(endpoint_url=None):
        endpoints.append(endpoint_url)
        return Presigner()

    monkeypatch.setattr(settings, "S3_PUBLIC_URL", "https://files.example.test")
    monkeypatch.setattr(storage, "_client", create_client)

    url = storage.get_presigned_url("floorplans", "asset.png")

    assert url == expected_url
    assert endpoints == ["https://files.example.test"]
