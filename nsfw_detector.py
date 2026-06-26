"""NSFW 检测模块（ONNX Runtime 推理，无重型 ML 框架）"""

import io
import os
from typing import Optional

import numpy as np
import onnxruntime as ort
from PIL import Image

import config

# 模型标签（GantMan/nsfw_model 5 分类）
_CLASSES = ["drawings", "hentai", "neutral", "porn", "sexy"]

# ONNX 模型文件（随包自动下载至缓存目录）
_MODEL_URL = (
    "https://github.com/iola1999/nsfw-detect-onnx/"
    "releases/download/v1.0.0/model.onnx"
)

# 模型文件缓存路径
_MODEL_CACHE_DIR = os.path.join(os.path.dirname(__file__), ".nsfw_cache")
_MODEL_CACHE_PATH = os.path.join(_MODEL_CACHE_DIR, "model.onnx")


def _ensure_model() -> str:
    """确保模型文件存在，不存在则下载"""
    if config.NSFW_MODEL_PATH and os.path.exists(config.NSFW_MODEL_PATH):
        return config.NSFW_MODEL_PATH

    if os.path.exists(_MODEL_CACHE_PATH):
        return _MODEL_CACHE_PATH

    os.makedirs(_MODEL_CACHE_DIR, exist_ok=True)
    import urllib.request

    print(f"[NSFW] 下载模型到 {_MODEL_CACHE_PATH} ...")
    urllib.request.urlretrieve(_MODEL_URL, _MODEL_CACHE_PATH)
    print("[NSFW] 模型下载完成")
    return _MODEL_CACHE_PATH


class NsfwDetector:
    """NSFW 检测器（单例）"""

    _instance: Optional["NsfwDetector"] = None

    def __new__(cls) -> "NsfwDetector":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        model_path = _ensure_model()
        self._session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"],
        )
        self._input_name = self._session.get_inputs()[0].name

    def detect(self, image_bytes: bytes) -> dict:
        """
        对图片 bytes 进行 NSFW 检测。

        返回:
            {
                "nsfw": bool,          # 是否 NSFW
                "score": float,        # 最高 NSFW 类置信度
                "top_class": str,       # 最高分类别
                "probabilities": dict,  # 各类别概率
            }
        """
        # 加载并预处理图片
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((299, 299))
        img_array = np.array(img, dtype=np.float32) / 255.0
        # 缩放到 [-1, 1]
        img_array = (img_array - 0.5) / 0.5
        # NHWC 格式 (batch, height, width, channels)
        img_array = np.expand_dims(img_array, axis=0)

        # 推理
        outputs = self._session.run(None, {self._input_name: img_array})
        probs = outputs[0][0]  # type: ignore shape: (5,)

        # 构建概率字典
        prob_dict = {_CLASSES[i]: float(probs[i]) for i in range(len(_CLASSES))}

        # 判定 NSFW（加权合并）
        hentai = prob_dict.get("hentai", 0.0)
        porn = prob_dict.get("porn", 0.0)
        sexy = prob_dict.get("sexy", 0.0)

        # 加权合并: porn=0.5, hentai=0.3, sexy=0.2
        nsfw_score = porn * 0.5 + hentai * 0.3 + sexy * 0.2

        is_nsfw = nsfw_score >= config.NSFW_THRESHOLD

        # 最高分类别
        top_idx = int(np.argmax(probs))
        top_class = _CLASSES[top_idx]

        return {
            "nsfw": is_nsfw,
            "score": round(nsfw_score, 4),
            "top_class": top_class,
            "probabilities": prob_dict,
        }
