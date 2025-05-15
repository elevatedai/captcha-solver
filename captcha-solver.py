import asyncio
import os
import logging
from aiohttp import web
from gemini_webapi import GeminiClient
from gemini_webapi.constants import Model
from pathlib import Path
import uuid
import aiofiles

logger = logging.getLogger(__name__)

COOKIE_FILE =  os.environ.get('COOKIE_FILE', "/app/cookies.json")
PROXY = os.environ.get('PROXY')
prompt="Extract all the text content from this image thoroughly and accurately. " \
        "Ensure that no lines, words, or parts of the content are missed, even if " \
        "the text is faint, small, or near the edges. The text may include headings, paragraphs, " \
        "or lists and could appear in various fonts, styles, or layouts. Carefully preserve the " \
        "reading order and structure as it appears in the image. Double-check for any skipped " \
        "lines or incomplete content, and extract every visible text element, ensuring " \
        "completeness across all sections. This is crucial for the task's accuracy.Only return image text and nothing else."


global_client = None

async def initialize_global_client(app):
    """Runs asynchronously before the server starts accepting requests."""
    global global_client
    
    logger.info("Attempting to initialize global GeminiClient...")
    try:
        client = GeminiClient(cookie_file=Path(COOKIE_FILE), proxy=PROXY)
        await asyncio.wait_for(client.init(timeout=30, auto_close=False, close_delay=300, auto_refresh=True), timeout=35)
        global_client = client
        logger.info("Global GeminiClient initialized successfully.")
    except asyncio.TimeoutError:
         logger.error("Global Client initialization timed out.")
         global_client = None # Set client to None on failure
    except Exception as e:
        logger.error(f"Error initializing global client: {e}")
        global_client = None # Set client to None on failure

def get_client():
    """Retrieves the initialized global client or raises an error."""
    if global_client is None:
        raise RuntimeError("GeminiClient is not initialized. Check server logs for errors during startup.")
    return global_client


async def solve_caption_handler(request:web.Request):
    try:

        file_content = await request.read()

        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)

        temp_file_path = temp_dir / f"{uuid.uuid4()}.png"
        
        async with aiofiles.open(temp_file_path, 'wb') as f:
            await f.write(file_content)

        logger.info(f"Saved temporary file to: {temp_file_path}")

        client = get_client()

        model =request.query.get("model")

        if not model:
            model=Model.G_2_5_FLASH
        else:
            model = Model.from_name(model)

        response = await client.generate_content(prompt, files=[temp_file_path], model=model)

        try:
            os.remove(temp_file_path)
            logger.info(f"Cleaned up temporary file: {temp_file_path}")
        except OSError as e:
            logger.error(f"Error removing temporary file {temp_file_path}: {e}")
        
        await client.delete_chat(response.metadata[0])
        return web.json_response({"text":response.text})

    except RuntimeError as e:
         logger.error(f"Client not initialized: {e}")
         return web.json_response({"error": str(e)}, status=503)
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return web.json_response({"error": str(e)}, status=500)


app = web.Application()

app.on_startup.append(initialize_global_client)

app.add_routes([
    web.post('/solve_captcha', solve_caption_handler),
])


if __name__ == '__main__':
    web.run_app(app, host="0.0.0.0", port=8080,print=None)