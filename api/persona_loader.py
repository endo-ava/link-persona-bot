"""
ペルソナテンプレートの読み込みと管理を行うモジュール
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class PersonaExample:
    """ペルソナの応答例"""
    input: str
    output: str


@dataclass
class Persona:
    """ペルソナ情報を保持するデータクラス"""
    id: str  # ファイル名から生成される一意のID
    name: str
    icon: str
    color: int
    description: str
    system_prompt: str
    examples: List[PersonaExample]

    def get_system_message(self) -> str:
        """システムメッセージを取得（LLM APIに渡す用）"""
        return self.system_prompt

    def get_display_name(self) -> str:
        """表示用の名前を取得（アイコン付き）"""
        return f"{self.icon} {self.name}"


class PersonaLoader:
    """ペルソナテンプレートを読み込み・管理するクラス"""

    def __init__(self, personas_dir: str = "api/personas"):
        """
        Args:
            personas_dir: ペルソナYAMLファイルが格納されているディレクトリ
        """
        self.personas_dir = Path(personas_dir)
        self._personas: Dict[str, Persona] = {}
        self._load_all_personas()

    def _load_all_personas(self) -> None:
        """ペルソナディレクトリ内のすべてのYAMLファイルを読み込む"""
        if not self.personas_dir.exists():
            raise FileNotFoundError(f"Personas directory not found: {self.personas_dir}")

        yaml_files = list(self.personas_dir.glob("*.yaml")) + list(
            self.personas_dir.glob("*.yml")
        )

        if not yaml_files:
            raise ValueError(f"No persona YAML files found in {self.personas_dir}")

        for yaml_file in yaml_files:
            persona = self._load_persona_from_file(yaml_file)
            self._personas[persona.id] = persona

    def _load_persona_from_file(self, file_path: Path) -> Persona:
        """YAMLファイルから単一のペルソナを読み込む"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # ファイル名（拡張子なし）をIDとして使用
        persona_id = file_path.stem

        # サンプル応答例のパース
        examples = []
        if "examples" in data and data["examples"]:
            for ex in data["examples"]:
                examples.append(
                    PersonaExample(input=ex["input"], output=ex["output"])
                )

        return Persona(
            id=persona_id,
            name=data["name"],
            icon=data["icon"],
            color=data["color"],
            description=data["description"],
            system_prompt=data["system_prompt"],
            examples=examples,
        )

    def get_persona(self, persona_id: str) -> Optional[Persona]:
        """IDからペルソナを取得"""
        return self._personas.get(persona_id)

    def get_all_personas(self) -> Dict[str, Persona]:
        """すべてのペルソナを取得"""
        return self._personas.copy()

    def list_persona_ids(self) -> List[str]:
        """利用可能なペルソナIDのリストを取得"""
        return list(self._personas.keys())

    def list_persona_names(self) -> List[str]:
        """利用可能なペルソナ名のリストを取得"""
        return [p.get_display_name() for p in self._personas.values()]


# グローバルなペルソナローダーインスタンス
_persona_loader: Optional[PersonaLoader] = None


def get_persona_loader() -> PersonaLoader:
    """
    グローバルなペルソナローダーインスタンスを取得
    （シングルトンパターン）
    """
    global _persona_loader
    if _persona_loader is None:
        _persona_loader = PersonaLoader()
    return _persona_loader
