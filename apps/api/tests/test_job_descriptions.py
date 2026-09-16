import pytest
from httpx import ASGITransport, AsyncClient
from src.main import app

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-Dev-User-Id": "11111111-1111-1111-1111-111111111111"},
    ) as c:
        yield c

@pytest.mark.asyncio
async def test_job_descriptions_flow(client: AsyncClient):
    # 1. Test POST /api/v1/job-descriptions
    payload = {
        "display_name": "Senior Go Engineer",
        "raw_text": "We are looking for a Senior Go Engineer with 5+ years of experience in Kubernetes and microservices."
    }
    
    response = await client.post(
        "/api/v1/job-descriptions",
        json=payload,
    )
    
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["display_name"] == "Senior Go Engineer"
    assert data["status"] == "pending"
    
    job_id = data["id"]
    
    # 2. Test GET /api/v1/job-descriptions/{id}
    get_response = await client.get(
        f"/api/v1/job-descriptions/{job_id}",
    )
    
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["id"] == job_id
    assert get_data["status"] == "pending"
    
    # 3. Test GET /api/v1/job-descriptions
    list_response = await client.get(
        "/api/v1/job-descriptions",
    )
    
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert len(list_data) > 0
    assert any(job["id"] == job_id for job in list_data)
