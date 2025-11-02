"""
ペルソナテンプレートの読み込みと管理を行うモジュール
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

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

    def __init__(self, personas_dir: str = "api/personas") -> None:
        """
        Args:
            personas_dir: ペルソナYAMLファイルが格納されているディレクトリ
        """
        self.personas_dir: Path = Path(personas_dir)
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
        """
        YAMLファイルから単一のペルソナを読み込む

        Args:
            file_path: YAMLファイルのパス

        Returns:
            読み込んだペルソナ

        Raises:
            ValueError: YAMLファイルが不正な形式、または必須フィールドが欠落している場合
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data: Any = yaml.safe_load(f)

        # YAMLデータがdictであることを確認
        if not isinstance(data, dict):
            raise ValueError(
                f"Invalid YAML format in {file_path}: expected dict, got {type(data).__name__}"
            )

        # 必須フィールドの検証
        required_fields = ["name", "icon", "color", "description", "system_prompt"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(
                f"Missing required fields in {file_path}: {', '.join(missing_fields)}"
            )

        # 各フィールドの型と値の検証
        if not isinstance(data["name"], str) or not data["name"].strip():
            raise ValueError(f"Invalid 'name' in {file_path}: must be a non-empty string")

        if not isinstance(data["icon"], str) or not data["icon"].strip():
            raise ValueError(f"Invalid 'icon' in {file_path}: must be a non-empty string")

        # colorフィールドの検証（intまたはhex文字列）
        if isinstance(data["color"], str):
            try:
                if data["color"].startswith("0x"):
                    color_int = int(data["color"], 16)
                else:
                    color_int = int(data["color"])
            except ValueError:
                raise ValueError(
                    f"Invalid 'color' format in {file_path}: {data['color']}"
                )
        elif isinstance(data["color"], int):
            color_int = data["color"]
        else:
            raise ValueError(
                f"Invalid 'color' type in {file_path}: expected int or hex string, got {type(data['color']).__name__}"
            )

        # color値の範囲検証（Discord埋め込みカラー範囲: 0x000000-0xFFFFFF）
        if not (0 <= color_int <= 0xFFFFFF):
            raise ValueError(
                f"Invalid 'color' value in {file_path}: {color_int} (must be 0x000000-0xFFFFFF)"
            )

        if not isinstance(data["description"], str) or not data["description"].strip():
            raise ValueError(
                f"Invalid 'description' in {file_path}: must be a non-empty string"
            )

        if not isinstance(data["system_prompt"], str) or not data["system_prompt"].strip():
            raise ValueError(
                f"Invalid 'system_prompt' in {file_path}: must be a non-empty string"
            )

        # ファイル名（拡張子なし）をIDとして使用
        persona_id = file_path.stem

        # サンプル応答例のパース（オプション）
        examples: List[PersonaExample] = []
        if "examples" in data and data["examples"]:
            if not isinstance(data["examples"], list):
                raise ValueError(
                    f"Invalid 'examples' in {file_path}: must be a list"
                )

            for i, ex in enumerate(data["examples"]):
                if not isinstance(ex, dict):
                    raise ValueError(
                        f"Invalid example {i} in {file_path}: must be a dict"
                    )

                if "input" not in ex or "output" not in ex:
                    raise ValueError(
                        f"Invalid example {i} in {file_path}: must have 'input' and 'output' fields"
                    )

                examples.append(
                    PersonaExample(
                        input=str(ex["input"]),
                        output=str(ex["output"])
                    )
                )

        return Persona(
            id=persona_id,
            name=data["name"],
            icon=data["icon"],
            color=color_int,
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
