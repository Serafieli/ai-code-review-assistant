import httpx
import asyncio
from config import GITLAB_TOKEN, GITLAB_BASE_URL


# ------------------------------------------------------------
# HTTPX client with retry logic
# ------------------------------------------------------------
async def http_request(method: str, url: str, headers: dict, json_data=None, retry=3):
    """
    Универсальный запрос с автоматическими ретраями при:
    - 429 rate limit
    - 5xx ошибках GitLab
    - сетевых ошибках
    """

    for attempt in range(retry):
        try:
            async with httpx.AsyncClient(timeout=20) as client:

                if method == "GET":
                    resp = await client.get(url, headers=headers)
                elif method == "POST":
                    resp = await client.post(url, headers=headers, json=json_data)
                elif method == "PUT":
                    resp = await client.put(url, headers=headers, json=json_data)
                else:
                    raise ValueError("Unsupported HTTP method")

                # GitLab rate limit
                if resp.status_code == 429:
                    wait = 1 + attempt
                    print(f"⚠ GitLab rate limit 429 → retry in {wait}s")
                    await asyncio.sleep(wait)
                    continue

                # 5xx — retry
                if resp.status_code >= 500:
                    wait = 1 + attempt
                    print(f"⚠ GitLab server error {resp.status_code} → retry in {wait}s")
                    await asyncio.sleep(wait)
                    continue

                # Всё норм
                resp.raise_for_status()
                return resp.json()

        except Exception as e:
            print(f"❌ HTTP ERROR attempt {attempt + 1}/{retry}: {e}")

            if attempt == retry - 1:
                print("❌ FAILED AFTER RETRIES:", url)
                raise

            await asyncio.sleep(1)

    raise RuntimeError("Unexpected request failure")


# ------------------------------------------------------------
# MAIN CLASS
# ------------------------------------------------------------
class GitLabClient:
    def __init__(self):
        self.base_url = GITLAB_BASE_URL.rstrip("/")
        self.headers = {
            "PRIVATE-TOKEN": GITLAB_TOKEN,
            "Content-Type": "application/json"
        }

    # ----------------------------------------------------------
    # GET MR INFO
    # ----------------------------------------------------------
    async def get_merge_request_info(self, project_id: int, mr_iid: int):
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}"
        return await http_request("GET", url, self.headers)

    # ----------------------------------------------------------
    # GET MR DIFF (changes)
    # ----------------------------------------------------------
    async def get_merge_request_diff(self, project_id: int, mr_iid: int):
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/changes"

        try:
            data = await http_request("GET", url, self.headers)
        except Exception as e:
            print("❌ ERROR getting diff:", e)
            return []

        return data.get("changes", [])

    # ----------------------------------------------------------
    # POST COMMENT TO MR
    # ----------------------------------------------------------
    async def post_comment(self, project_id: int, mr_iid: int, body: str):
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes"
        payload = {"body": body}

        try:
            return await http_request("POST", url, self.headers, payload)
        except Exception as e:
            print("❌ ERROR posting comment:", e)
            print("Payload:", payload)
            return {"status": "failed"}

    # ----------------------------------------------------------
    # SET LABELS
    # ----------------------------------------------------------
    async def set_labels(self, project_id: int, mr_iid: int, labels: list[str]):
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}"
        payload = {"labels": ",".join(labels)}

        try:
            return await http_request("PUT", url, self.headers, payload)
        except Exception as e:
            print("❌ ERROR setting labels:", e)
            print("Labels:", labels)
            return {"status": "failed"}

    # ----------------------------------------------------------
    # APPROVE MR
    # ----------------------------------------------------------
    async def approve_mr(self, project_id: int, mr_iid: int):
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/approve"

        try:
            return await http_request("POST", url, self.headers)
        except Exception as e:
            print("❌ ERROR approving MR:", e)
            return {"status": "failed"}


gitlab = GitLabClient()
