import re
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from agents.base import BaseAgent
from core.llm import LLMFactory
from core.logger import setup_logger
from knowledge.retriever import Retriever


class ReviewerAgent(BaseAgent, ABC):
    """Abstract reviewer agent with two-pass S1/S2 review algorithm.

    System 1 (cheap, fast): Quick scan for cognitive biases → suspicion signal
    System 2 (deep, strong+RAG): Deep analysis with corpus context → detailed feedback

    Output: Markdown with inline comments <!-- REVIEWER:<name>:START -->...<!-- END -->
    """

    def __init__(self, persona_name: str):
        """Initialize reviewer with persona config and LLMs.

        Args:
            persona_name: Name of persona (e.g., 'uncle_kahneman')
        """
        super().__init__(name=f"reviewer.{persona_name}")
        self.persona_name = persona_name

        # Load persona configuration
        self.config = self._load_persona_config()
        self.max_comments = self.config.get("max_comments", None)
        self.k_rag = self.config.get("k_rag", 3)
        self.skip_s1 = self.config.get("skip_s1", False)

        # Load persona prompt template
        self.persona_prompt = self._load_persona_prompt()

        # Initialize dual LLMs
        self.llm_s1 = None
        self.llm_s2 = None
        self._init_dual_llms()

        # Initialize retriever with persona filter
        self.retriever = Retriever()
        self._warmup_retriever()

    def _load_persona_config(self) -> dict:
        """Load persona config from config.yaml."""
        config_path = Path(f"personas/{self.persona_name}/config.yaml")
        if not config_path.exists():
            self.logger.warning(f"Persona config not found: {config_path}")
            return {}

        import yaml
        return yaml.safe_load(config_path.read_text(encoding='utf-8')) or {}

    def _load_persona_prompt(self) -> str:
        """Load persona prompt template from persona_prompt.md."""
        prompt_path = Path(f"personas/{self.persona_name}/persona_prompt.md")
        if not prompt_path.exists():
            self.logger.warning(f"Persona prompt not found: {prompt_path}")
            return ""

        return prompt_path.read_text(encoding='utf-8')

    def _init_dual_llms(self) -> None:
        """Initialize S1 (cheap) and S2 (deep) LLMs with fallback."""
        try:
            self.llm_s1 = LLMFactory.get_llm(mode="cheap")
            self.logger.info("S1 (cheap) LLM initialized")
        except Exception as e:
            self.logger.warning(f"S1 initialization failed: {e}, degrading to S2-only mode")
            self.skip_s1 = True

        try:
            self.llm_s2 = LLMFactory.get_llm(mode="deep")
            self.logger.info("S2 (deep) LLM initialized")
        except Exception as e:
            self.logger.error(f"S2 initialization failed (critical): {e}")
            raise

    def _warmup_retriever(self) -> None:
        """Warmup retriever with persona filter. Log warning if corpus empty."""
        try:
            docs = self.retriever.retrieve(
                "test",
                k=1,
                filter={"persona": self.persona_name}
            )
            if not docs:
                self.logger.warning(f"Persona corpus '{self.persona_name}' is empty")
            else:
                self.logger.info(f"Retriever ready: {len(docs)} corpus doc(s)")
        except Exception as e:
            self.logger.error(f"Retriever warmup failed: {e}")

    def review_markdown(self, draft: str) -> str:
        """Review markdown draft and inject comments.

        Args:
            draft: Markdown text to review

        Returns:
            Markdown with inline <!-- REVIEWER:... --> comments
        """
        if not draft:
            self.logger.warning("Empty draft, returning as-is")
            return draft

        if self.max_comments == 0:
            self.logger.info("max_comments=0, skipping review")
            return draft

        # Split into paragraphs
        blocks = re.split(r'\n\s*\n', draft)
        out = []
        comments = 0

        for block in blocks:
            out.append(block)

            # Skip if not reviewable
            if not self._is_reviewable(block):
                continue

            # Stop if comment limit reached
            if self.max_comments and comments >= self.max_comments:
                continue

            try:
                # S1: Quick bias scan
                s1_result = self._call_s1(block) if not self.skip_s1 else None

                if s1_result is None:
                    suspicious = False
                    s1_hint = "(S1 skipped)"
                elif not s1_result.get("suspicious", False):
                    continue  # Not suspicious, skip S2
                else:
                    suspicious = True
                    s1_hint = s1_result.get("hint", "")

                # S2: Deep RAG analysis
                rag_context = self._get_rag_context(block)
                s2_text = self._call_s2(block, rag_context, s1_hint)

                # Format and append comment
                comment = self._format_comment(s2_text)
                out.append(comment)
                comments += 1

            except Exception as e:
                self.logger.error(f"Review error for block: {e}")
                continue

        return "\n\n".join(out)

    def _is_reviewable(self, block: str) -> bool:
        """Check if block should be reviewed.

        Skip:
        - Headings (#{1,6})
        - Blockquotes (>)
        - Tables (|)
        - Code fences (```)
        - Very short blocks (< 80 chars)
        - Already annotated blocks
        """
        stripped = block.strip()

        # Skip headings, tables, blockquotes
        if re.match(r'^#{1,6}\s', stripped) or stripped.startswith('>') or stripped.startswith('|'):
            return False

        # Skip code fences
        if stripped.startswith('```'):
            return False

        # Skip very short blocks
        if len(stripped) < 80:
            return False

        # Skip already annotated blocks (idempotency)
        if '<!-- REVIEWER:' in block:
            return False

        return True

    def _call_s1(self, paragraph: str) -> Optional[Dict[str, Any]]:
        """Call System 1 (cheap LLM) for bias detection.

        Returns:
            {"suspicious": bool, "hint": str} or None on error
        """
        if not self.llm_s1:
            return None

        prompt = self._s1_prompt(paragraph)

        try:
            response = self.llm_s1.invoke(prompt)
            return self._parse_s1_response(response)
        except Exception as e:
            self.logger.debug(f"S1 call failed: {e}")
            return None

    def _call_s2(self, paragraph: str, rag_context: str, s1_hint: str) -> str:
        """Call System 2 (strong LLM + RAG) for detailed review.

        Args:
            paragraph: Block to review
            rag_context: Retrieved corpus context
            s1_hint: Signal from System 1

        Returns:
            Review text (markdown)
        """
        prompt = self._s2_prompt(paragraph, rag_context, s1_hint)

        try:
            response = self.llm_s2.invoke(prompt)
            return response.strip()
        except Exception as e:
            self.logger.error(f"S2 call failed: {e}")
            raise

    def _get_rag_context(self, paragraph: str) -> str:
        """Retrieve corpus context for paragraph."""
        try:
            docs = self.retriever.retrieve(
                paragraph[:400],
                k=self.k_rag,
                filter={"persona": self.persona_name}
            )

            if not docs:
                return "[корпус пуст]"

            context = "\n---\n".join(d.get("content", "") for d in docs)
            return context or "[контекст недоступен]"

        except Exception as e:
            self.logger.warning(f"RAG retrieval failed: {e}")
            return "[ошибка доступа к корпусу]"

    @abstractmethod
    def _s1_prompt(self, paragraph: str) -> str:
        """Build S1 prompt. Must return JSON-parseable response."""
        pass

    @abstractmethod
    def _s2_prompt(self, paragraph: str, rag_context: str, s1_hint: str) -> str:
        """Build S2 prompt using corpus context and S1 signal."""
        pass

    @abstractmethod
    def _format_comment(self, review_text: str) -> str:
        """Format review text as HTML comment block."""
        pass

    def _parse_s1_response(self, response: str) -> Dict[str, Any]:
        """Parse S1 response (JSON or fallback regex).

        Args:
            response: LLM response text

        Returns:
            {"suspicious": bool, "hint": str}
        """
        # Try JSON parse first
        try:
            data = json.loads(response)
            return {
                "suspicious": data.get("suspicious", False),
                "hint": data.get("hint", "")
            }
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: regex search for "suspicious: true/false"
        match = re.search(r'suspicious\s*[:=]\s*(true|false)', response, re.IGNORECASE)
        if match:
            suspicious = match.group(1).lower() == "true"
            return {"suspicious": suspicious, "hint": ""}

        # Default: not suspicious
        return {"suspicious": False, "hint": ""}

    def execute(self, task: str) -> str:
        """Placeholder to satisfy BaseAgent ABC. Use review_markdown() instead."""
        return self.review_markdown(task)
