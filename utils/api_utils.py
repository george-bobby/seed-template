import json
import re
from contextlib import asynccontextmanager, suppress
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import aiohttp
from aiohttp import FormData
from tenacity import retry, stop_after_attempt, wait_fixed

from config.constants import AppEndpoint
from config.settings import settings
from common.logger import logger


_session: aiohttp.ClientSession | None = None
_cookies: Any = None
_base_url: str = settings.APP_API_URL


async def init_session() -> aiohttp.ClientSession:
    """Initializes a new HTTP session and authenticates."""
    global _session, _cookies
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
        await authenticate()
    return _session


async def close_session() -> None:
    """Closes the HTTP session and clears cookies."""
    global _session, _cookies
    if _session and not _session.closed:
        await _session.close()
    _session = None
    _cookies = None


async def get_session() -> aiohttp.ClientSession:
    """Gets the current session, initializing if necessary."""
    global _session
    if _session is None or _session.closed:
        await init_session()
    return _session


@asynccontextmanager
async def app_session():
    """Context manager for application session."""
    await init_session()
    try:
        yield
    finally:
        await close_session()


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def authenticate() -> bool:
    """Authenticates with the application API."""
    global _cookies
    try:
        session = await get_session()
        # TODO: Update this endpoint to match your application's login endpoint
        login_url = urljoin(_base_url, AppEndpoint.LOGIN.value)
        login_data = {
            "username": settings.APP_ADMIN_EMAIL,
            "password": settings.APP_ADMIN_PASSWORD,
        }

        # TODO: Adjust if your app uses site names or other authentication parameters
        if settings.APP_SITE_NAME:
            login_data["siteName"] = settings.APP_SITE_NAME

        async with session.post(
            login_url,
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            allow_redirects=True
        ) as response:
            if response.status == 200:
                _cookies = response.cookies
                logger.succeed("Authentication successful.")
                return True
            else:
                logger.error(f"Authentication failed with status: {response.status}")
                return False

    except Exception as e:
        logger.error(f"Authentication error: {e!s}")
        return False


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def submit_form(endpoint: str, form_data: dict[str, Any], use_multipart: bool = False) -> dict[str, Any]:
    """Submits a form to the application API."""
    try:
        session = await get_session()
        url = urljoin(_base_url, endpoint)

        # TODO: Adjust 'postback' or similar hidden fields if your app uses them
        if "postback" not in form_data:
            form_data["postback"] = "postback"

        if use_multipart:
            multipart_data = FormData()
            for key, value in form_data.items():
                field_value = "" if value is None else str(value)
                multipart_data.add_field(key, str(field_value))
            
            async with session.post(
                url,
                data=multipart_data,
                cookies=_cookies,
                allow_redirects=True,
                chunked=False
            ) as response:
                response_text = await response.text()

                result = {
                    "status_code": response.status,
                    "url": str(response.url),
                    "content": response_text,
                    "entity_id": None  # TODO: Implement entity ID extraction if needed
                }

                if response.status in [200, 302]:
                    # TODO: Implement logic to extract entity_id from response URL or content
                    try:
                        entity_id = extract_entity_id_from_url(str(response.url))
                        result["entity_id"] = entity_id
                    except ValueError:
                        with suppress(ValueError):
                            entity_id = extract_entity_id_from_content(response_text)
                            result["entity_id"] = entity_id
                
                return result
        else:
            async with session.post(
                url,
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                cookies=_cookies,
                allow_redirects=True
            ) as response:
                response_text = await response.text()

                result = {
                    "status_code": response.status,
                    "url": str(response.url),
                    "content": response_text,
                    "entity_id": None  # TODO: Implement entity ID extraction if needed
                }

                if response.status in [200, 302]:
                    # TODO: Implement logic to extract entity_id from response URL or content
                    try:
                        entity_id = extract_entity_id_from_url(str(response.url))
                        result["entity_id"] = entity_id
                    except ValueError:
                        with suppress(ValueError):
                            entity_id = extract_entity_id_from_content(response_text)
                            result["entity_id"] = entity_id

                return result

    except Exception as e:
        logger.error(f"Form submission error: {e!s}")
        raise RuntimeError(f"Form submission error for endpoint {endpoint}: {e!s}") from e


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def ajax_request(function: str, data: dict[str, Any]) -> dict[str, Any]:
    """Sends an AJAX request to the application API."""
    try:
        session = await get_session()
        # TODO: Adjust AJAX endpoint if different
        url = urljoin(_base_url, AppEndpoint.AJAX.value)

        # TODO: Adjust 'f' parameter if different
        ajax_data = {"f": function, **data}

        async with session.post(
            url,
            data=ajax_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            cookies=_cookies
        ) as response:
            response_text = await response.text()

            return {"status_code": response.status, "content": response_text}

    except Exception as e:
        logger.error(f"AJAX request error: {e!s}")
        raise RuntimeError(f"AJAX request error for function {function}: {e!s}") from e


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def get_request(url_path: str) -> dict[str, Any]:
    """Sends a GET request to the application API."""
    try:
        session = await get_session()
        url = urljoin(_base_url, url_path)

        async with session.get(url, cookies=_cookies, allow_redirects=True) as response:
            response_text = await response.text()

            return {
                "status_code": response.status,
                "url": str(response.url),
                "content": response_text
            }

    except Exception as e:
        logger.error(f"GET request error: {e!s}")
        raise RuntimeError(f"GET request error for path {url_path}: {e!s}") from e


# TODO: Add your application-specific API interaction functions here.
# Examples might include:
# async def get_all_entities(entity_type: AppDataItemType) -> list[dict[str, Any]]:
#     ...
# async def get_entity_details(entity_id: int, entity_type: AppDataItemType) -> dict[str, Any]:
#     ...
# async def update_entity(entity_id: int, entity_type: AppDataItemType, data: dict[str, Any]) -> bool:
#     ...
# async def delete_entity(entity_id: int, entity_type: AppDataItemType) -> bool:
#     ...


def extract_entity_id_from_url(url: str) -> int | None:
    """
    Extracts an entity ID from a URL.
    TODO: Customize this function to match your application's URL patterns for IDs.
    """
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        # TODO: Add your application's specific ID parameter names here
        id_patterns = [
            "entityID", "id",  # Generic patterns
            # Add your application's specific ID parameter names here, e.g., "productID", "userID"
        ]
        for pattern in id_patterns:
            if pattern in query_params:
                return int(query_params[pattern][0])
        raise ValueError(f"Cannot extract entity ID from URL: no matching ID pattern found in '{url}'")
    except (ValueError, IndexError, KeyError, TypeError) as e:
        if isinstance(e, ValueError) and "Cannot extract entity ID" in str(e):
            raise
        raise ValueError(f"Cannot extract entity ID from URL '{url}': {e}") from e


def extract_entity_id_from_content(content: str) -> int | None:
    """
    Extracts an entity ID from HTML content.
    TODO: Customize this function to match your application's HTML patterns for IDs.
    """
    try:
        # TODO: Add your application's specific HTML patterns here
        id_patterns = [
            r"entityID[=:](\d+)",
            r"id[=:](\d+)",
            r'name="entityID"[^>]*value="(\d+)"',
            # Add your application's specific HTML patterns here, e.g., r"product_id[=:](\d+)"
        ]
        for pattern in id_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        raise ValueError("Cannot extract entity ID from content: no matching ID pattern found")
    except (ValueError, AttributeError, TypeError) as e:
        if isinstance(e, ValueError) and "Cannot extract entity ID" in str(e):
            raise
        raise ValueError(f"Cannot extract entity ID from content: {e}") from e


def _extract_latest_entity_id(content: str, entity_type: str) -> int:
    """
    Extracts the latest entity ID from a listing page.
    TODO: Customize this function to match your application's HTML patterns for entity listings.
    """
    try:
        # TODO: Add patterns for your entity types
        pattern_map = {
            "generic_entity": r"entityID=(\d+)",  # Example pattern
            # Add patterns for other entity types
        }

        pattern = pattern_map.get(entity_type)
        if not pattern:
            raise ValueError(f"Unknown entity type: {entity_type}")

        matches = re.findall(pattern, content)
        if matches:
            return max(int(match) for match in matches)

    except (ValueError, TypeError) as e:
        raise RuntimeError(f"Error extracting latest entity ID for entity_type {entity_type}") from e
    
    raise RuntimeError(f"Could not extract latest entity ID for entity_type {entity_type}")


def _extract_items_from_listing(content: str, endpoint_name: str) -> list[dict[str, Any]]:
    """
    Extracts items from an HTML listing page.
    TODO: Customize this function to parse your application's entity listing HTML.
    """
    items = []
    try:
        # TODO: Add parsing logic for your entity types
        if endpoint_name == "generic_entity":  # Example for a generic entity
            seen_ids = set()
            link_pattern = r'<a[^>]*entityID=(\d+)[^>]*>([^<]+)</a>'
            link_matches = re.findall(link_pattern, content, re.IGNORECASE)
            for entity_id, entity_name in link_matches:
                entity_id_int = int(entity_id)
                if entity_id_int not in seen_ids:
                    seen_ids.add(entity_id_int)
                    items.append({"entityID": entity_id_int, "name": entity_name.strip()})
        # TODO: Add parsing logic for other entity types
    except Exception as e:
        logger.error(f"Error parsing {endpoint_name} listing: {e!s}")

    return items


def _extract_item_details(content: str, endpoint_name: str, item_id: int) -> dict[str, Any]:
    """
    Extracts details of a single item from an HTML edit/view page.
    TODO: Customize this function to parse your application's entity detail HTML.
    """
    try:
        # TODO: Add parsing logic for your entity types
        if endpoint_name == "generic_entity":  # Example for a generic entity
            item = {"entityID": item_id}
            name_match = re.search(r'<input[^>]*\bname="name"[^>]*\bvalue="([^"]*)"', content, re.IGNORECASE)
            if name_match:
                item["name"] = name_match.group(1).strip()
            # Add more field extraction as needed
            return item
        # TODO: Add parsing logic for other entity types
    except Exception as e:
        logger.error(f"Error extracting {endpoint_name} details: {e!s}")
        raise RuntimeError(f"Error extracting {endpoint_name} details for item_id {item_id}: {e!s}") from e

    raise RuntimeError(f"Could not extract {endpoint_name} details for item_id {item_id}")


async def make_anthropic_request(
    prompt: str,
    api_key: str,
    model: str = "claude-sonnet-4-5-20250929",
    max_tokens: int = 4000,
    temperature: float = 0.7,
    system_message: str | None = None,
) -> dict[str, Any]:    
    """Sends a request to the Anthropic API."""
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }

    if system_message:
        payload["system"] = system_message

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    try:
        timeout = aiohttp.ClientTimeout(total=180)

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=timeout,
            ) as response,
        ):
            response_data = await response.json()

            if response.status == 200:
                return response_data
            else:
                error_message = response_data.get("error", {}).get("message", f"HTTP {response.status}")

                logger.error(f"Anthropic API request failed: {response.status}")
                logger.debug(f"Error response: {response_data}")

                if response.status in [429, 529]:
                    raise RuntimeError(f"Anthropic API rate limit error ({response.status}): {error_message}")
                else:
                    raise RuntimeError(f"Anthropic API error ({response.status}): {error_message}")

    except aiohttp.ClientError as e:
        logger.error(f"Anthropic API network error: {e!s}")
        raise RuntimeError(f"Network error: {e!s}") from e
    except Exception as e:
        logger.error(f"Anthropic API request failed: {e!s}")
        raise RuntimeError(f"Unexpected error: {e!s}") from e


def parse_anthropic_response(response_data: dict[str, Any]) -> list[dict]:
    """Parses the JSON response from the Anthropic API."""
    try:
        content = response_data["content"]
        text_content = content[0].get("text", "")

        markdown_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text_content, re.DOTALL)
        if markdown_match:
            extracted_content = markdown_match.group(1).strip()
            json_start_in_extracted = extracted_content.find("[")
            if json_start_in_extracted != -1:
                text_content = extracted_content[json_start_in_extracted:]
                json_start = 0
            else:
                json_start = text_content.find("[")
        else:
            json_start = text_content.find("[")

        if json_start == -1:
            for prefix in ["Here's", "Here is", "JSON:", "Array:"]:
                idx = text_content.find(f"{prefix}[")
                if idx != -1:
                    json_start = idx + len(prefix)
                    break

        if json_start == -1:
            snippet = text_content[:500] + "..." if len(text_content) > 500 else text_content
            logger.error("No JSON array found in Anthropic response")
            logger.debug(f" Response snippet: {snippet}")
            raise RuntimeError(f"No JSON array found in Anthropic response. Response snippet: {snippet}")

        bracket_count = 0
        json_end = -1
        in_string = False
        escape_next = False

        for i in range(json_start, len(text_content)):
            char = text_content[i]

            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == "[":
                    bracket_count += 1
                elif char == "]":
                    bracket_count -= 1
                    if bracket_count == 0:
                        json_end = i + 1
                        break

        if json_end == -1:
            potential_ends = []
            bracket_count = 0
            in_string = False
            escape_next = False

            for i in range(json_start, len(text_content)):
                char = text_content[i]

                if escape_next:
                    escape_next = False
                    continue

                if char == "\\":
                    escape_next = True
                    continue

                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue

                if not in_string:
                    if char == "[":
                        bracket_count += 1
                    elif char == "]":
                        bracket_count -= 1
                        if bracket_count == 0:
                            potential_ends.append(i + 1)

            if potential_ends:
                json_end = potential_ends[-1]
            else:
                last_bracket = text_content.rfind("]")
                json_end = last_bracket + 1 if last_bracket > json_start else -1

        if json_end == -1 or json_end <= json_start:
            logger.error("No valid JSON array ending found")
            logger.debug(f" JSON extraction failed: json_start={json_start}, json_end={json_end}")
            snippet = text_content[json_start : json_start + 200] + "..." if len(text_content) > json_start + 200 else text_content[json_start:]
            logger.debug(f" Text snippet from json_start: {snippet}")
            raise RuntimeError(f"No valid JSON array ending found. JSON extraction failed: json_start={json_start}, json_end={json_end}")

        json_str = text_content[json_start:json_end]

        json_str = json_str.strip()
        json_str = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", json_str)
        json_str = re.sub(r"\s+", " ", json_str)
        json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parse failed, attempting fixes: {e}")

            if "Expecting ',' delimiter" in str(e) or "Expecting ':' delimiter" in str(e):
                last_complete_brace = json_str.rfind("}")
                if last_complete_brace > 0:
                    truncated_json = json_str[: last_complete_brace + 1] + "]"
                    try:
                        logger.info("Attempting to parse truncated JSON")
                        return json.loads(truncated_json)
                    except json.JSONDecodeError:
                        pass
            raise e

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Anthropic response: {e}")
        if "json_str" in locals():
            snippet = json_str[:300] + "..." if len(json_str) > 300 else json_str
            logger.debug(f" JSON snippet: {snippet}")
            raise RuntimeError(f"Failed to parse JSON from Anthropic response: {e}. JSON snippet: {snippet}") from e
        raise RuntimeError(f"Failed to parse JSON from Anthropic response: {e}") from e
    except Exception as e:
        logger.error(f"Error parsing Anthropic response: {e}")
        raise RuntimeError(f"Error parsing Anthropic response: {e}") from e
