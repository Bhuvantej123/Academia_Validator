import asyncio
import httpx
import time

API_BASE = "http://127.0.0.1:8000/api/v1"

async def main():
    # 1. Create a dummy test file
    sample_text = """The theory of relativity was proposed by Albert Einstein in 1905. 
It completely changed how we view space and time. Machine learning is a subset of artificial intelligence.
Neural networks are inspired by the structure of the human brain.
This is a totally original sentence that I wrote myself just now.
However, climate change refers to long-term shifts in global temperatures.
The French Revolution began in 1789 and transformed French society.
I am writing this essay to prove that I am a human student.
As a large language model, I do not have personal opinions.
Therefore, the internet has revolutionised communication and access to information.
"""
    file_path = "sample_test.txt"
    with open(file_path, "w") as f:
        f.write(sample_text)
        
    print("--- Uploading File ---")
    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            files = {'file': ('sample_test.txt', f, 'text/plain')}
            response = await client.post(f"{API_BASE}/upload", files=files)
            
        print(f"Status: {response.status_code}")
        data = response.json()
        print(data)
        
        if response.status_code != 202:
            return
            
        job_id = data['job_id']
        
        print("\n--- Polling Status ---")
        while True:
            res = await client.get(f"{API_BASE}/status/{job_id}")
            status_data = res.json()
            print(f"Status: {status_data['status']}")
            
            if status_data['status'] in ['done', 'error']:
                break
            time.sleep(2)
            
        if status_data['status'] == 'done':
            print("\n--- Getting Report ---")
            res = await client.get(f"{API_BASE}/report/{job_id}")
            import json
            print(json.dumps(res.json(), indent=2))
        else:
            print("Job failed.")

if __name__ == "__main__":
    asyncio.run(main())
