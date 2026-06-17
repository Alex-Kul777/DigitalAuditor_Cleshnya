from agents.reviewer_base import ReviewerAgent


class UncleKahneman(ReviewerAgent):
    """Cognitive bias reviewer based on Kahneman's System 1/System 2 thinking.

    Analyzes audit findings for cognitive distortions:
    - System 1: Fast, intuitive bias detection
    - System 2: Slow, deliberate analysis with corpus context
    """

    def __init__(self, persona_name: str = "uncle_kahneman"):
        super().__init__(persona_name=persona_name)

    def _s1_prompt(self, paragraph: str) -> str:
        """System 1: Quick bias scan prompt (cheap, fast LLM).

        Returns JSON: {"suspicious": bool, "hint": "<1 sentence>"}
        """
        return f"""Ты — быстрый рецензент. Оцени параграф ИТ-аудита: есть ли признаки когнитивных искажений (эффект ореола, поспешный вывод, лень Системы 2, подмена вопроса)?

Ответь **строго** JSON только:
{{"suspicious": true/false, "hint": "<1 предложение максимум>"}}

Параграф:
<<<{paragraph}>>>"""

    def _s2_prompt(self, paragraph: str, rag_context: str, s1_hint: str) -> str:
        """System 2: Deep analysis prompt using persona template (strong LLM + RAG).

        Fills in persona_prompt.md template with context and S1 signal.
        """
        # Fill template variables
        template = self.persona_prompt
        prompt = template.format(
            s1_hint=s1_hint or "(Система 1 не выявила явных сигналов)",
            rag_context=rag_context,
            paragraph=paragraph
        )
        return prompt

    def _format_comment(self, review_text: str) -> str:
        """Format review as HTML comment block (idempotent marker).

        Output: <!-- REVIEWER:uncle_kahneman:START -->
                > **💬 Дядя Канеман замечает:**
                > {review_text}
                <!-- REVIEWER:uncle_kahneman:END -->
        """
        formatted = f"""<!-- REVIEWER:uncle_kahneman:START -->
> **💬 Дядя Канеман замечает:**
> {review_text}
<!-- REVIEWER:uncle_kahneman:END -->"""
        return formatted
