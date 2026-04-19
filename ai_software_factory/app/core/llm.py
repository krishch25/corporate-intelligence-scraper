from langchain_openai import ChatOpenAI, AzureChatOpenAI
from app.core.config import settings
import httpx

def get_llm():
    """
    Returns an instance of ChatOpenAI or AzureChatOpenAI.
    Prioritizes the EY endpoint if provided, otherwise falls back to standard OpenAI API.
    """
    if settings.eyq_incubator_endpoint and settings.eyq_incubator_key:
        # Use EY custom endpoint as AzureOpenAI
        return AzureChatOpenAI(
            azure_endpoint=settings.eyq_incubator_endpoint,
            api_key=settings.eyq_incubator_key,
            api_version=settings.eyq_api_version,
            deployment_name=settings.eyq_model,
            temperature=0.1,
            model_kwargs={"max_completion_tokens": 4000},
            http_client=httpx.Client(verify=False)
        )
    else:
        # Standard OpenAI fallback
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model="gpt-4o",
            temperature=0.1
        )
