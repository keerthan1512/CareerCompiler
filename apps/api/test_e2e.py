import asyncio
import httpx
import json
from generate_dummy_pdf import generate_pdf

async def run_test():
    url_base = "http://localhost:8000/api/v1"
    headers = {
        "X-Dev-User-Id": "11111111-1111-1111-1111-111111111111"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n=== [Phase 1] Generate and Upload Master Resume ===")
        generate_pdf("e2e_sample_resume.pdf")
        with open("e2e_sample_resume.pdf", "rb") as f:
            files = {"pdf_file": ("e2e_sample_resume.pdf", f, "application/pdf")}
            data = {"display_name": "E2E Master Resume"}
            res = await client.post(f"{url_base}/master-resumes", headers=headers, data=data, files=files)
        print("Upload Status:", res.status_code)
        if res.status_code != 201:
            print("Error:", res.text)
            return
        resume_id = res.json().get("id")
        
        while True:
            res2 = await client.get(f"{url_base}/master-resumes/{resume_id}", headers=headers)
            profile = res2.json().get("canonical_profile", {})
            status = profile.get("status")
            if status == "complete":
                print("Parse Complete!")
                break
            elif status == "failed":
                print("Parse Failed!")
                return
            await asyncio.sleep(2)
            
        print("\n=== [Phase 2] Analyze Job Description ===")
        job_data = {
            "display_name": "E2E Test Job",
            "raw_text": "We are looking for a Senior Developer with Python, FastAPI, and React experience. Must have 5 years experience building scalable APIs."
        }
        res3 = await client.post(f"{url_base}/job-descriptions", headers=headers, json=job_data)
        print("Job Upload Status:", res3.status_code)
        if res3.status_code != 202:
            print("Error:", res3.text)
            return
        job_id = res3.json().get("id")
        
        while True:
            res4 = await client.get(f"{url_base}/job-descriptions/{job_id}", headers=headers)
            status = res4.json().get("status")
            if status == "complete":
                print("Job Analysis Complete!")
                break
            elif status == "failed":
                print("Job Analysis Failed!")
                return
            await asyncio.sleep(2)
            
        print("\n=== [Phase 3] Generate Tailoring Plan ===")
        plan_data = {
            "job_id": job_id,
            "master_resume_id": resume_id,
            "mode": "review"
        }
        res5 = await client.post(f"{url_base}/tailoring-plans", headers=headers, json=plan_data)
        print("Plan Creation Status:", res5.status_code)
        if res5.status_code != 202:
            print("Error:", res5.text)
            return
        plan_id = res5.json().get("id")
        
        while True:
            res6 = await client.get(f"{url_base}/tailoring-plans/{plan_id}", headers=headers)
            status = res6.json().get("status")
            if status == "complete":
                print("Tailoring Plan Generated!")
                break
            elif status == "failed":
                print("Tailoring Plan Failed!")
                return
            await asyncio.sleep(2)
            
        print("\n=== [Phase 4] Compile Document ===")
        res7 = await client.post(f"{url_base}/documents/compile?tailoring_plan_id={plan_id}", headers=headers)
        print("Compile Trigger Status:", res7.status_code)
        if res7.status_code != 202:
            print("Error:", res7.text)
            return
        document_id = res7.json().get("id")
        
        while True:
            res8 = await client.get(f"{url_base}/documents/{document_id}", headers=headers)
            status = res8.json().get("status")
            if status == "complete":
                print("Compilation Complete!")
                break
            elif status == "failed":
                print("Compilation Failed!")
                print("Validation Results:", res8.json().get("validation_results"))
                return
            await asyncio.sleep(2)
            
        print("\n=== [Phase 5] Download PDF ===")
        res9 = await client.get(f"{url_base}/documents/{document_id}/download", headers=headers)
        print("Download Status:", res9.status_code)
        with open("e2e_output.pdf", "wb") as f:
            f.write(res9.content)
        print("Saved successfully to e2e_output.pdf!")

if __name__ == "__main__":
    asyncio.run(run_test())
