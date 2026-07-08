from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from app.core.config import settings


def get_llm(temperature: float = 0.0) -> ChatHuggingFace:
    """
    Builds a chat model backed by HF's Inference API. Temperature is the
    only thing that varies between chains (JD parsing wants deterministic
    output, outreach drafting wants some variation).
    """
    endpoint = HuggingFaceEndpoint(
        repo_id=settings.chat_model,
        huggingfacehub_api_token=settings.huggingfacehub_api_token,
        temperature=temperature if temperature > 0 else 0.01,  # HF endpoint requires > 0
        max_new_tokens=512,
    )
    return ChatHuggingFace(llm=endpoint)
