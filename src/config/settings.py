#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 설정 값 읽기·저장과 검증 (FR-13)
# 파일 위치: src/config/settings.py
import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path


@dataclass
class Settings:
    """사용자가 바꿀 수 있는 값. 기본값은 기획서(FR-04, FR-05, FR-05 가중치)를 따른다."""

    daily_new_count: int = 20  # 하루 신규 단어 수 (FR-04)
    daily_review_count: int = 10  # 하루 복습 단어 최대 수 (FR-04)
    quiz_question_count: int = 20  # 시험 문제 수 기본값 (FR-05)
    weight_new: float = 3.0  # 시험 이력이 없는 단어 가산치 (FR-05)
    weight_old: float = 2.0  # 마지막 시험 후 오래된 단어 가산치 (FR-05)
    old_days: int = 7  # "오래됨" 기준 일수 (FR-05)
    weight_wrong: float = 4.0  # 오답률에 곱하는 가산치 (FR-05)
    theme: str = "light"  # 'light' 또는 'dark' (화면 테마)
    font_scale: str = "normal"  # 'small', 'normal', 'large' (글자 크기)

    def validate(self) -> None:
        """값 범위를 검사한다. 문제가 있으면 ValueError."""
        checks = [
            (1 <= self.daily_new_count <= 200, "하루 신규 단어 수는 1~200이어야 합니다"),
            (0 <= self.daily_review_count <= 100, "하루 복습 단어 수는 0~100이어야 합니다"),
            (5 <= self.quiz_question_count <= 100, "시험 문제 수는 5~100이어야 합니다"),
            (self.weight_new >= 0, "가중치는 0 이상이어야 합니다"),
            (self.weight_old >= 0, "가중치는 0 이상이어야 합니다"),
            (self.weight_wrong >= 0, "가중치는 0 이상이어야 합니다"),
            (1 <= self.old_days <= 365, "오래됨 기준 일수는 1~365이어야 합니다"),
            (self.theme in ("light", "dark"), "테마는 light 또는 dark여야 합니다"),
            (self.font_scale in ("small", "normal", "large"), "글자 크기는 small, normal, large 중 하나여야 합니다"),
        ]
        for is_valid, message in checks:
            if not is_valid:
                raise ValueError(message)


def load_settings(path: Path) -> Settings:
    """설정 파일을 읽는다. 파일이 없으면 기본값을 쓴다. 모르는 키는 무시한다."""
    if not path.exists():
        return Settings()
    data = json.loads(path.read_text(encoding="utf-8"))
    known_names = {field.name for field in fields(Settings)}
    settings = Settings(**{key: value for key, value in data.items() if key in known_names})
    settings.validate()
    return settings


def save_settings(path: Path, settings: Settings) -> None:
    settings.validate()  # 잘못된 값은 파일에 쓰지 않는다
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")
