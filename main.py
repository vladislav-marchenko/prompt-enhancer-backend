from fastapi import FastAPI, Request, HTTPException, Depends
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
async def enhance_prompt(payload: PromptRequest, request: Request, allowed: bool = Depends(limiter)):
    if not allowed:
        raise HTTPException(
            status_code=429, detail="Too many requests. Please try again later.")

    user_prompt = payload.prompt.strip()
    if not user_prompt:
        return "ERROR: The prompt is empty. Please provide a valid prompt and try again."

    request_body = {
        "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "messages": [
            {
                "role": "system",
                "content": "Your task is to help users improve their prompts by making them more detailed, structured, and clear for the AI. You may correct any errors in the original prompt, including grammar, spelling, or logical issues. Reformulate or expand the prompt to ensure maximum clarity and completeness, with the goal of achieving the best possible results from the AI model. Do not answer the user's questions or try to solve their requests directly — your sole role is to edit and enhance their prompt. Be concise, but do not omit important context or intent."
            },
            {
                "role": "user",
                "content": f"{SYSTEM_PROMPT}\n\nPrompt: {user_prompt}"
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
        raise HTTPException(status_code=500, detail="Error from external API")

    result = response.json()
    try:
        return result["choices"][0]["message"]["content"]
    except Exception:
        return "ERROR: The prompt is unclear or invalid. Please provide a clear and valid prompt and try again."
