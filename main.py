from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import httpx
from limiter import limiter
from config import API_URL, API_KEY, SYSTEM_PROMPT
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware,
                   allow_origins=["https://chatgpt.com"],
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"])


class PromptRequest(BaseModel):
    prompt: str


@app.post("/enhance")
async def enhance_prompt(payload: PromptRequest,
                         allowed: bool = Depends(limiter)
                         ):
    try:
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )

        user_prompt = payload.prompt.strip()
        if not user_prompt:
            raise HTTPException(
                status_code=400,
                detail="The prompt is empty. Please provide a valid prompt and try again."
            )

        request_body = {
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                API_URL,
                json=request_body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}"
                }
            )

            if response.status_code != 200:
                response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        if 'ERROR: ' in content:
            raise HTTPException(
                status_code=400,
                detail=content.split('ERROR: ')[1]
            )

        return content
    except httpx.RequestError as exception:
        raise HTTPException(
            status_code=502,
            detail=f"External API request failed: {str(exception)}"
        )
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="Error from external API."
        )
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail="The prompt is unclear or invalid. Please provide a clear and valid prompt and try again."
        )
    except Exception as exception:
        if isinstance(exception, HTTPException):
            raise exception

        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(exception)}"
        )
