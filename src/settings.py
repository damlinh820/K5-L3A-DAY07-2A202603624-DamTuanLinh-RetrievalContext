"""Portable paths and explicit credentials for the Day 6/Day 7 workspace."""
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DAY6 = ROOT.parent / 'K5-L3A-DAY06-2A202603624-DataIngestion'


@dataclass
class Settings:
    day6: Path
    corpus: Path
    chroma: Path
    cache: Path
    model: str = 'gpt-4o-mini'
    max_cost_usd: float = 0.10

    @classmethod
    def load(cls):
        load_dotenv(ROOT/'.env')
        day6 = Path(os.getenv('DAY6_ROOT', str(DEFAULT_DAY6)))
        load_dotenv(day6/'.env')
        return cls(day6, Path(os.getenv('LAB7_CORPUS', str(day6/'results/chunks_C.jsonl'))),
                   Path(os.getenv('LAB7_CHROMA', str(ROOT/'runs/day6_rebuild/chroma'))),
                   ROOT/'runs/local_cache', os.getenv('LAB7_CHAT_MODEL', 'gpt-4o-mini'),
                   float(os.getenv('LAB7_MAX_COST_USD', '0.10')))

    def pipeline(self):
        from .pipeline import Day6DenseBackend, LegalPipeline
        if not self.corpus.is_file(): raise RuntimeError('Corpus missing; configure DAY6_ROOT or LAB7_CORPUS')
        if not self.chroma.is_dir(): raise RuntimeError('Chroma missing; run build-index with --execute')
        backend = Day6DenseBackend(self.chroma, self.corpus, self.cache)
        return LegalPipeline(list(backend.lookup.values()), backend)
