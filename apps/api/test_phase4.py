import asyncio
import httpx
from src.database import AsyncSessionLocal
from src.models import TailoringPlan
from sqlalchemy.future import select
import json
import time

async def get_plan_id():
    async with AsyncSessionLocal() as session:
        # Get the first complete tailoring plan
        res = await session.execute(select(TailoringPlan).where(TailoringPlan.status == "complete").limit(1))
        plan = res.scalar_one_or_none()
        return str(plan.id) if plan else None

async def run_test():
    plan_id = await get_plan_id()
    if not plan_id:
        print("No complete TailoringPlan found in the database. Please run Phase 3 test first.")
        return
        
    print(f"Using TailoringPlan ID: {plan_id}")
    
    url = "http://localhost:8000/api/v1/documents"
    headers = {
        "accept": "application/json",
        "X-Dev-User-Id": "11111111-1111-1111-1111-111111111111"
    }
    
    async with httpx.AsyncClient() as client:
        # Trigger compilation
        print("Triggering compilation...")
        res = await client.post(f"{url}/compile?tailoring_plan_id={plan_id}", headers=headers, timeout=20.0)
        print("POST status:", res.status_code, res.text)
        
        if res.status_code != 202:
            return
            
        doc_id = res.json().get("id")
        
        # Poll status
        for i in range(60):
            print(f"Polling document {doc_id}... ({i+1}/60)")
            await asyncio.sleep(5)
            res2 = await client.get(f"{url}/{doc_id}", headers=headers)
            data = res2.json()
            print("Status:", data.get("status"))
            
            if data.get("status") in ["complete", "failed"]:
                print("Validation Results:", json.dumps(data.get("validation_results"), indent=2))
                
                if data.get("status") == "complete":
                    print("Downloading PDF...")
                    res3 = await client.get(f"{url}/{doc_id}/download", headers=headers)
                    print("Download status:", res3.status_code)
                    if res3.status_code == 200:
                        with open("test_output.pdf", "wb") as f:
                            f.write(res3.content)
                        print("Saved PDF to test_output.pdf")
                break

if __name__ == "__main__":
    asyncio.run(run_test())
