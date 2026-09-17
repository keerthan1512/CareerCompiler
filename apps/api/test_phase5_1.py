import asyncio
import httpx
import json

async def run_test():
    url = "http://localhost:8000/api/v1/master-resumes"
    headers = {
        "X-Dev-User-Id": "11111111-1111-1111-1111-111111111111"
    }
    
    print("Uploading sample_resume.pdf...")
    async with httpx.AsyncClient() as client:
        with open("sample_resume.pdf", "rb") as f:
            files = {"pdf_file": ("sample_resume.pdf", f, "application/pdf")}
            data = {"display_name": "Test PDF"}
            res = await client.post(url, headers=headers, data=data, files=files, timeout=20.0)
            
        print("POST status:", res.status_code, res.text)
        if res.status_code != 201:
            return
            
        resume_id = res.json().get("id")
        
        # Poll status
        for i in range(20):
            print(f"Polling resume {resume_id}... ({i+1}/20)")
            await asyncio.sleep(3)
            res2 = await client.get(f"{url}/{resume_id}", headers=headers)
            data2 = res2.json()
            
            profile = data2.get("canonical_profile")
            if profile:
                status = profile.get("status")
                print("Status:", status)
                if status in ["complete", "failed"]:
                    print("Parse result:", json.dumps(profile, indent=2))
                    break
            else:
                print("Profile not created yet.")

if __name__ == "__main__":
    asyncio.run(run_test())
