import pytest
from unittest.mock import MagicMock, patch, Mock
from agents.uncle_kahneman import UncleKahneman


class TestUncleKahnemanS1Prompt:
    """Test System 1 prompt generation."""

    def test_s1_prompt_structure(self):
        """Verify S1 prompt contains required JSON format instruction."""
        with patch('agents.reviewer_base.LLMFactory.get_llm'), \
             patch('agents.reviewer_base.Retriever'):
            reviewer = UncleKahneman()
            prompt = reviewer._s1_prompt("Test paragraph about audit findings.")

            assert 'быстрый рецензент' in prompt
            assert '"suspicious"' in prompt
            assert '"hint"' in prompt
            assert 'JSON' in prompt
            assert 'Test paragraph' in prompt

    def test_s1_prompt_includes_paragraph(self):
        """Verify S1 prompt includes the input paragraph."""
        with patch('agents.reviewer_base.LLMFactory.get_llm'), \
             patch('agents.reviewer_base.Retriever'):
            reviewer = UncleKahneman()
            test_para = "System controls were not documented properly."
            prompt = reviewer._s1_prompt(test_para)

            assert test_para in prompt


class TestUncleKahnemanS2Prompt:
    """Test System 2 prompt with RAG context."""

    def test_s2_prompt_uses_template(self):
        """Verify S2 prompt uses persona_prompt template."""
        with patch('agents.reviewer_base.LLMFactory.get_llm'), \
             patch('agents.reviewer_base.Retriever'):
            reviewer = UncleKahneman()
            reviewer.persona_prompt = "Шаблон: {s1_hint} {rag_context} {paragraph}"

            s2 = reviewer._s2_prompt(
                "Параграф",
                "Контекст корпуса",
                "Сигнал S1"
            )

            assert "Шаблон:" in s2
            assert "Параграф" in s2
            assert "Контекст корпуса" in s2
            assert "Сигнал S1" in s2

    def test_s2_prompt_handles_empty_hint(self):
        """Verify S2 prompt handles missing S1 hint gracefully."""
        with patch('agents.reviewer_base.LLMFactory.get_llm'), \
             patch('agents.reviewer_base.Retriever'):
            reviewer = UncleKahneman()
            reviewer.persona_prompt = "Hint: {s1_hint}"

            s2 = reviewer._s2_prompt(
                "Para",
                "Context",
                ""  # empty hint
            )

            # Should handle gracefully (no crash, uses empty or default)
            assert "Hint:" in s2


class TestUncleKahnemanCommentFormat:
    """Test comment formatting."""

    def test_format_comment_structure(self):
        """Verify comment has correct HTML markers and emoji."""
        with patch('agents.reviewer_base.LLMFactory.get_llm'), \
             patch('agents.reviewer_base.Retriever'):
            reviewer = UncleKahneman()
            comment = reviewer._format_comment("Это ошибка смещения.")

            assert '<!-- REVIEWER:uncle_kahneman:START -->' in comment
            assert '<!-- REVIEWER:uncle_kahneman:END -->' in comment
            assert '💬' in comment
            assert 'Дядя Канеман' in comment
            assert 'Это ошибка смещения.' in comment

    def test_format_comment_is_valid_markdown(self):
        """Verify formatted comment is valid markdown blockquote."""
        with patch('agents.reviewer_base.LLMFactory.get_llm'), \
             patch('agents.reviewer_base.Retriever'):
            reviewer = UncleKahneman()
            comment = reviewer._format_comment("Test review")

            lines = comment.split('\n')
            # Should have blockquote lines with '>'
            blockquote_lines = [l for l in lines if l.strip().startswith('>')]
            assert len(blockquote_lines) > 0


@patch('agents.reviewer_base.LLMFactory.get_llm')
@patch('agents.reviewer_base.Retriever')
class TestUncleKahnemanReviewMarkdown:
    """Integration tests for review_markdown() algorithm."""

    def test_review_markdown_empty_draft(self, mock_retriever, mock_factory):
        """Verify empty draft returns as-is with warning."""
        reviewer = UncleKahneman()
        result = reviewer.review_markdown("")

        assert result == ""

    def test_review_markdown_max_comments_zero(self, mock_retriever, mock_factory):
        """Verify max_comments=0 skips all reviews."""
        reviewer = UncleKahneman()
        reviewer.max_comments = 0

        draft = "# Heading\n\nThis is a long paragraph with enough content to normally be reviewed and analyzed for cognitive biases in audit findings."
        result = reviewer.review_markdown(draft)

        assert result == draft  # unchanged

    def test_review_markdown_skips_heading(self, mock_retriever, mock_factory):
        """Verify headings are not reviewed."""
        reviewer = UncleKahneman()
        reviewer.llm_s1 = MagicMock()
        reviewer.llm_s1.invoke = MagicMock(return_value='{"suspicious": true, "hint": "test"}')

        draft = "# Heading\n\nNormal paragraph with enough content to be reviewable and analyzed for various cognitive biases."
        result = reviewer.review_markdown(draft)

        # Heading should pass through unchanged; only normal paragraph processed
        assert "# Heading" in result
        reviewer.llm_s1.invoke.assert_called()

    def test_review_markdown_skips_already_annotated(self, mock_retriever, mock_factory):
        """Verify idempotency — skips blocks with existing reviewer markers."""
        reviewer = UncleKahneman()
        reviewer.llm_s1 = MagicMock()
        reviewer.llm_s1.invoke = MagicMock(return_value='{"suspicious": true}')

        draft = "Already annotated block with reviewer comment.\n\n<!-- REVIEWER:uncle_kahneman:START -->\nComment\n<!-- REVIEWER:uncle_kahneman:END -->"
        result = reviewer.review_markdown(draft)

        # Should not add new comments to already-annotated content
        assert result == draft

    def test_review_markdown_s1_not_suspicious(self, mock_retriever, mock_factory):
        """Verify S2 skipped when S1 returns suspicious=false."""
        reviewer = UncleKahneman()
        reviewer.llm_s1 = MagicMock()
        reviewer.llm_s1.invoke = MagicMock(return_value='{"suspicious": false, "hint": ""}')
        reviewer.llm_s2 = MagicMock()

        draft = "This is a normal audit paragraph with sufficient length to be reviewable and analyzed for potential cognitive biases."
        result = reviewer.review_markdown(draft)

        # S1 called, S2 NOT called (not suspicious)
        reviewer.llm_s1.invoke.assert_called()
        reviewer.llm_s2.invoke.assert_not_called()
        assert "<!-- REVIEWER:uncle_kahneman:START -->" not in result

    def test_review_markdown_s1_suspicious_triggers_s2(self, mock_retriever, mock_factory):
        """Verify S2 called when S1 returns suspicious=true."""
        reviewer = UncleKahneman()
        reviewer.llm_s1 = MagicMock()
        reviewer.llm_s1.invoke = MagicMock(return_value='{"suspicious": true, "hint": "Possible halo effect"}')
        reviewer.llm_s2 = MagicMock()
        reviewer.llm_s2.invoke = MagicMock(return_value="This shows classic halo bias.")

        # Mock retriever
        reviewer.retriever.retrieve = MagicMock(return_value=[
            {"content": "Context 1"},
            {"content": "Context 2"}
        ])

        draft = "This system is excellent because one good metric suggests everything is fine without detailed verification of controls."
        result = reviewer.review_markdown(draft)

        # Both S1 and S2 should be called
        reviewer.llm_s1.invoke.assert_called()
        reviewer.llm_s2.invoke.assert_called()
        # Comment should be present
        assert "<!-- REVIEWER:uncle_kahneman:START -->" in result
        assert "This shows classic halo bias." in result

    def test_review_markdown_respects_max_comments_limit(self, mock_retriever, mock_factory):
        """Verify max_comments cap stops processing after limit."""
        reviewer = UncleKahneman()
        reviewer.max_comments = 1
        reviewer.llm_s1 = MagicMock()
        reviewer.llm_s1.invoke = MagicMock(return_value='{"suspicious": true}')
        reviewer.llm_s2 = MagicMock()
        reviewer.llm_s2.invoke = MagicMock(return_value="Comment")
        reviewer.retriever.retrieve = MagicMock(return_value=[{"content": "ctx"}])

        draft = (
            "First paragraph that should be reviewed with enough content to trigger the review process properly here.\n\n"
            "Second paragraph that should not get reviewed because limit is 1 and we already have our comment from first.\n\n"
            "Third paragraph also should be skipped due to max_comments limit of 1 being reached."
        )
        result = reviewer.review_markdown(draft)

        # Only 1 comment should be added
        comment_count = result.count('<!-- REVIEWER:uncle_kahneman:START -->')
        assert comment_count == 1

    def test_review_markdown_s1_fallback_json_parsing(self, mock_retriever, mock_factory):
        """Verify S1 response parsing with malformed JSON fallback."""
        reviewer = UncleKahneman()
        reviewer.llm_s1 = MagicMock()
        reviewer.llm_s1.invoke = MagicMock(return_value='suspicious=true')  # Malformed JSON
        reviewer.llm_s2 = MagicMock()
        reviewer.llm_s2.invoke = MagicMock(return_value="Comment")
        reviewer.retriever.retrieve = MagicMock(return_value=[{"content": "ctx"}])

        draft = "Long paragraph about audit findings with potential cognitive biases that need careful analysis."
        result = reviewer.review_markdown(draft)

        # Should still work with regex fallback
        assert "<!-- REVIEWER:uncle_kahneman:START -->" in result

    def test_review_markdown_preserves_structure(self, mock_retriever, mock_factory):
        """Verify paragraph structure and content preserved."""
        reviewer = UncleKahneman()
        reviewer.llm_s1 = MagicMock()
        reviewer.llm_s1.invoke = MagicMock(return_value='{"suspicious": false}')

        draft = "Para 1 with enough length to be reviewable for cognitive biases.\n\nPara 2 also long enough to be reviewed and analyzed.\n\nPara 3 final paragraph."
        result = reviewer.review_markdown(draft)

        # Original paragraphs should remain intact
        assert "Para 1" in result
        assert "Para 2" in result
        assert "Para 3" in result

    def test_review_markdown_handles_s2_error_gracefully(self, mock_retriever, mock_factory):
        """Verify S2 error doesn't crash, just skips that block."""
        reviewer = UncleKahneman()
        reviewer.llm_s1 = MagicMock()
        reviewer.llm_s1.invoke = MagicMock(return_value='{"suspicious": true}')
        reviewer.llm_s2 = MagicMock()
        reviewer.llm_s2.invoke = MagicMock(side_effect=RuntimeError("LLM error"))
        reviewer.retriever.retrieve = MagicMock(return_value=[{"content": "ctx"}])

        draft = "Long paragraph with potential cognitive bias that requires deep System 2 analysis."
        
        # Should not raise, but log error and continue
        result = reviewer.review_markdown(draft)
        
        # Original paragraph preserved, no comment added (error skipped)
        assert draft in result
        assert "<!-- REVIEWER:uncle_kahneman:START -->" not in result


class TestUncleKahnemanInitialization:
    """Test initialization and configuration loading."""

    @patch('agents.reviewer_base.LLMFactory.get_llm')
    @patch('agents.reviewer_base.Retriever')
    def test_initialization_with_defaults(self, mock_retriever, mock_factory):
        """Verify default initialization."""
        reviewer = UncleKahneman()

        assert reviewer.persona_name == "uncle_kahneman"
        assert reviewer.max_comments is None or isinstance(reviewer.max_comments, (int, type(None)))
        assert reviewer.k_rag > 0
        assert reviewer.llm_s1 is not None
        assert reviewer.llm_s2 is not None

    @patch('agents.reviewer_base.LLMFactory.get_llm')
    @patch('agents.reviewer_base.Retriever')
    def test_custom_persona_name(self, mock_retriever, mock_factory):
        """Verify custom persona name support."""
        # This would only work if config exists, so just test the basic flow
        with patch('agents.reviewer_base.Path.exists', return_value=False):
            reviewer = UncleKahneman(persona_name="custom_reviewer")
            assert reviewer.persona_name == "custom_reviewer"
