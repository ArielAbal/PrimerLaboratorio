from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Pregunta:
    title: str
    prompt: str
    hints: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "prompt": self.prompt,
            "hints": self.hints,
            "tags": self.tags,
        }


@dataclass
class BancoPreguntas:
    preguntas: List[Pregunta] = field(default_factory=list)

    def agregar(self, pregunta: Pregunta):
        self.preguntas.append(pregunta)

    def agregar_varias(self, preguntas: List[Pregunta]):
        self.preguntas.extend(preguntas)

    def to_list_dict(self) -> List[Dict]:
        return [pregunta.to_dict() for pregunta in self.preguntas]
