from pantheon_v2.core.modelrouter.providers.litellm.config.router_config import Provider

LITE_LLM_CONTENT_TYPE_TEXT = "text"
LITE_LLM_CONTENT_TYPE_IMAGE_URL = "image_url"

PROVIDERS_WITH_NESTED_IMAGE_URL = {
    Provider.OPENAI.value,  # for gpt-4-vision
}

KEY_ROLE = "role"
KEY_CONTENT = "content"
KEY_TYPE = "type"
KEY_TEXT = "text"
KEY_IMAGE_URL = "image_url"
KEY_URL = "url"
