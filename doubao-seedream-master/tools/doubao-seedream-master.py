import base64
from collections.abc import Generator
from typing import Any, List

import httpx
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.file.file import File
from pydantic import BaseModel, Field
from volcenginesdkarkruntime import Ark
from volcenginesdkarkruntime.types.images import SequentialImageGenerationOptions
from loguru import logger


class ToolPayload(BaseModel):
    prompt: str = Field(..., description="用于生成图像的提示词")
    images: List[File] | None = Field(default_factory=list, description="参考图片")
    model: str = Field(default="doubao-seedream-4-0-250828", description="模型名")
    size: str | None = Field(default="4k", description="图片分辨率")
    seed: int | None = Field(default=-1, description="随机种子", ge=-1, le=2147483647)

    def to_seedream_images(self) -> List[str] | None:
        if not self.images:
            return None

        seedream_images: List[str] = []

        for image in self.images:
            try:
                response = httpx.get(image.url, timeout=40.0)
                response.raise_for_status()
            except Exception as exc:
                logger.warning(f"Failed to download reference image from `{image.url}`: {exc}")
                continue

            image_bytes = response.content
            if not image_bytes:
                logger.warning(f"Reference image `{image.url}` is empty, skip it.")
                continue

            mime_type: str | None = None

            if image.mime_type:
                mime_type = image.mime_type.split(";", 1)[0].strip().lower()
            elif image.extension:
                extension = image.extension.lower().lstrip(".")
                if extension == "jpg":
                    extension = "jpeg"
                mime_type = f"image/{extension}"
            else:
                content_type = (
                    response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                )
                if content_type.startswith("image/"):
                    mime_type = content_type

            if not mime_type or not mime_type.startswith("image/"):
                mime_type = "image/png"

            image_format = mime_type.split("/", 1)[1]
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            seedream_images.append(f"data:image/{image_format};base64,{b64_image}")

        return seedream_images or None


class DoubaoSeedreamMasterTool(Tool):
    """
    https://www.volcengine.com/docs/82379/1541523
    """

    DEFAULT_ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

    def _generate(self, tp: ToolPayload):
        base_url = self.runtime.credentials.get("ARK_BASE_URL", self.DEFAULT_ARK_BASE_URL)
        api_key = self.runtime.credentials["ARK_API_KEY"]

        client = Ark(base_url=base_url.strip(), api_key=api_key.strip())

        reference_images = tp.to_seedream_images()

        images_response = client.images.generate(
            model=tp.model,
            prompt=tp.prompt,
            size=tp.size,
            image=reference_images,
            sequential_image_generation="auto",
            sequential_image_generation_options=SequentialImageGenerationOptions(max_images=9),
            response_format="url",
            watermark=False,
            seed=tp.seed,
        )
        return images_response

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        tp = ToolPayload(**tool_parameters)

        images_response = self._generate(tp)

        yield self.create_log_message(label="Generated images", data=tp.model_dump(mode="json"))

        for image in images_response.data:
            try:
                yield self.create_image_message(image_url=image.url)
            except Exception as e:
                yield self.create_log_message(
                    label="Exception: Unable to return image response",
                    data={"error": f"Error when invoke ARK model `{tp.model}` - error={e}"},
                )
