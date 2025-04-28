import os
import openai
from dotenv import load_dotenv
import logging
import re

logger = logging.getLogger(__name__)

load_dotenv()

def query_openai_for_best_selector(candidates, model="gpt-3.5-turbo"):
    """Ask OpenAI which candidate HTML block looks like a movie item, and log full interaction."""

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise Exception("OPENAI_API_KEY not found in environment variables.")

    client = openai.OpenAI(api_key=api_key)

    messages = [
        {
            "role": "system",
            "content": "You are a web scraping expert specializing in movie websites."
        },
        {
            "role": "user",
            "content": (
                "Below are several HTML snippets extracted from a Burmese movie website. "
                "Identify which block most likely contains a single movie listing (with title, image, and streaming link). "
                "Reply with the block number only. "
                "Candidates:\n\n" +
                "\n\n".join([f"Block {i+1}:\n{c}" for i, c in enumerate(candidates)])
            )
        }
    ]

    # Log the full prompt
    logger.info("[OpenAI Prompt] Messages:")
    for msg in messages:
        logger.info(msg['content'])

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            max_tokens=100
        )

        reply_content = response.choices[0].message.content.strip()

        # Log the full response
        logger.info(f"[OpenAI Response] {reply_content}")

        selected_index = parse_openai_block_response(reply_content) - 1
        if 0 <= selected_index < len(candidates):
            return selected_index
        else:
            logger.warning(f"OpenAI suggested invalid block index: {reply_content}. Falling back to Block 1.")
            return 0

    except Exception as e:
        logger.error(f"[OpenAI ERROR] {str(e)}")
        selected_index = 0
        return 0

def parse_openai_block_response(response_text):
    """Extract the numeric block ID from OpenAI's response."""
    match = re.search(r'\d+', response_text)
    if match:
        return int(match.group())
    else:
        raise ValueError(f"Could not extract block number from OpenAI response: {response_text}")
