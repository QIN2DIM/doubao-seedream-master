import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from pydantic import BaseModel, Field


class ToolPayload(BaseModel):
    prompt: str = Field(..., description="用于生成图像的提示词")
    images: Any | None = Field(default_factory=list, description="参考图片")
    model: str = Field(default="doubao-seedream-4-0-250828", description="模型名")
    size: str | None = Field(default="4k", description="图片分辨率")
    seed: int | None = Field(default=-1, description="随机种子", ge=-1, le=2147483647)


class DoubaoSeedreamMasterTool(Tool):
    def _generate(self, tp: ToolPayload):
        pass

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        print(json.dumps(tool_parameters, indent=2, ensure_ascii=False))
        yield self.create_text_message("hello world!")
