import uuid
from unittest.mock import MagicMock, patch

from app.schemas.resume import ResumeTailorOutput
from app.services import pdf_service

SAMPLE_OUTPUT = ResumeTailorOutput(
    summary="Backend engineer.",
    skills=["Python"],
    experience=[],
    projects=[],
    match_explanation="n/a",
)
CONTACT = {"full_name": "Jane Doe", "email": "jane@example.com", "phone": None, "location": None, "linkedin_url": None}


@patch("app.services.pdf_service._r2_client")
@patch("app.services.pdf_service.typst")
async def test_generate_and_upload_pdf_success(mock_typst, mock_r2_client):
    mock_typst.compile.return_value = b"%PDF-1.7 fake bytes"
    mock_client = MagicMock()
    mock_r2_client.return_value = mock_client
    user_id, resume_id = uuid.uuid4(), uuid.uuid4()

    with patch("app.services.pdf_service.settings") as mock_settings:
        mock_settings.r2_bucket_name = "cvura-resumes"
        key = await pdf_service.generate_and_upload_pdf(user_id, resume_id, SAMPLE_OUTPUT, CONTACT, [], [])

    assert key == f"resumes/{user_id}/{resume_id}.pdf"
    mock_client.put_object.assert_called_once()
    call_kwargs = mock_client.put_object.call_args.kwargs
    assert call_kwargs["Bucket"] == "cvura-resumes"
    assert call_kwargs["Key"] == f"resumes/{user_id}/{resume_id}.pdf"
    assert call_kwargs["ContentType"] == "application/pdf"


@patch("app.services.pdf_service._r2_client")
def test_generate_presigned_url_calls_s3_with_expiry(mock_r2_client):
    mock_client = MagicMock()
    mock_client.generate_presigned_url.return_value = "https://r2.example.com/signed?sig=abc"
    mock_r2_client.return_value = mock_client

    with patch("app.services.pdf_service.settings") as mock_settings:
        mock_settings.r2_bucket_name = "cvura-resumes"
        url = pdf_service.generate_presigned_url("resumes/u1/r1.pdf", expires_in=1800)

    assert url == "https://r2.example.com/signed?sig=abc"
    mock_client.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={"Bucket": "cvura-resumes", "Key": "resumes/u1/r1.pdf"},
        ExpiresIn=1800,
    )


@patch("app.services.pdf_service._r2_client")
@patch("app.services.pdf_service.typst")
async def test_generate_and_upload_pdf_compile_failure_returns_none(mock_typst, mock_r2_client):
    mock_typst.compile.side_effect = RuntimeError("bad typst source")
    user_id, resume_id = uuid.uuid4(), uuid.uuid4()

    key = await pdf_service.generate_and_upload_pdf(user_id, resume_id, SAMPLE_OUTPUT, CONTACT, [], [])

    assert key is None
    mock_r2_client.assert_not_called()


@patch("app.services.pdf_service._r2_client")
@patch("app.services.pdf_service.typst")
async def test_generate_and_upload_pdf_upload_failure_returns_none(mock_typst, mock_r2_client):
    mock_typst.compile.return_value = b"%PDF-1.7 fake bytes"
    mock_client = MagicMock()
    mock_client.put_object.side_effect = ConnectionError("R2 unreachable")
    mock_r2_client.return_value = mock_client
    user_id, resume_id = uuid.uuid4(), uuid.uuid4()

    key = await pdf_service.generate_and_upload_pdf(user_id, resume_id, SAMPLE_OUTPUT, CONTACT, [], [])

    assert key is None


async def test_generate_and_upload_pdf_compiles_real_typst_source():
    """No mocks: exercises the real Typst compile step (fast, offline, no R2
    call) to catch template syntax errors that a fully-mocked test would miss."""
    with patch("app.services.pdf_service._upload_to_r2", return_value="resumes/u1/r1.pdf") as mock_upload:
        key = await pdf_service.generate_and_upload_pdf(
            uuid.uuid4(), uuid.uuid4(), SAMPLE_OUTPUT, CONTACT, [], []
        )

    assert key == "resumes/u1/r1.pdf"
    mock_upload.assert_called_once()
