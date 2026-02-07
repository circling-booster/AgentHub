"""Resource 엔티티 테스트

TDD로 작성됨:
- Resource 메타데이터
- ResourceContent (text/blob)
"""

from src.domain.entities.resource import Resource, ResourceContent


class TestResource:
    def test_resource_creation_with_required_fields(self):
        """리소스 생성 - 필수 필드"""
        resource = Resource(
            uri="file:///test.txt",
            name="Test File",
        )
        assert resource.uri == "file:///test.txt"
        assert resource.name == "Test File"
        assert resource.description == ""
        assert resource.mime_type == ""

    def test_resource_creation_with_all_fields(self):
        """리소스 생성 - 모든 필드"""
        resource = Resource(
            uri="file:///test.txt",
            name="Test File",
            description="Test description",
            mime_type="text/plain",
        )
        assert resource.mime_type == "text/plain"


class TestResourceContent:
    def test_text_content_creation(self):
        """텍스트 콘텐츠 생성"""
        content = ResourceContent(
            uri="file:///test.txt",
            text="Hello, World!",
            mime_type="text/plain",
        )
        assert content.text == "Hello, World!"
        assert content.blob is None

    def test_blob_content_creation(self):
        """바이너리 콘텐츠 생성"""
        content = ResourceContent(
            uri="file:///image.png",
            blob=b"\x89PNG...",
            mime_type="image/png",
        )
        assert content.blob == b"\x89PNG..."
        assert content.text is None
