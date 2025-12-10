import re
import heapq
import math
from typing import List, Dict
from collections import Counter
import logging

from engine.state import WorkflowState

logger = logging.getLogger(__name__)


def split_text(state: WorkflowState) -> WorkflowState:
    text = state.text.strip()
    chunk_size = state.chunk_size
    
    if not text:
        logger.warning("Empty text provided to split_text")
        return state.copy_with_updates(chunks=[])
    
    words = text.split()
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + 1
        
        if current_length + word_length > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    logger.info(f"Split text into {len(chunks)} chunks")
    
    return state.copy_with_updates(
        chunks=chunks,
        execution_metadata={
            **state.execution_metadata,
            "chunks_created": len(chunks)
        }
    )


def summarize_chunks(state: WorkflowState) -> WorkflowState:
    chunks = state.chunks
    
    if not chunks:
        logger.warning("No chunks available for summarization")
        return state.copy_with_updates(chunk_summaries=[])
    
    summaries: List[str] = []
    
    for i, chunk in enumerate(chunks):
        summary = _frequency_based_summarize(chunk)
        summaries.append(summary)
        logger.debug(f"Summarized chunk {i+1}/{len(chunks)}: {len(chunk)} -> {len(summary)} chars")
    
    logger.info(f"Generated {len(summaries)} chunk summaries using frequency scoring")
    
    return state.copy_with_updates(
        chunk_summaries=summaries,
        execution_metadata={
            **state.execution_metadata,
            "summaries_created": len(summaries),
            "summarization_method": "frequency_based_scoring"
        }
    )


def merge_summaries(state: WorkflowState) -> WorkflowState:
    summaries = state.chunk_summaries
    
    if not summaries:
        logger.warning("No summaries available to merge")
        return state.copy_with_updates(
            merged_summary="",
            current_length=0
        )
    
    merged = ". ".join(s.strip().rstrip(".") for s in summaries if s.strip())
    merged = merged + "."
    
    logger.info(f"Merged {len(summaries)} summaries into {len(merged)} chars")
    
    return state.copy_with_updates(
        merged_summary=merged,
        current_length=len(merged),
        refined_summary=merged,
        execution_metadata={
            **state.execution_metadata,
            "merged_length": len(merged)
        }
    )


def refine_summary(state: WorkflowState) -> WorkflowState:
    merged = state.merged_summary or state.text
    max_len = state.max_length
    
    # Normalize spacing + fix periods
    merged = merged.replace("..", ".")
    parts = [p.strip() for p in merged.split(".") if p.strip()]
    
    parts = [p for p in parts if len(p.split()) >= 4]
    
    refined = ""
    for p in parts:
        if len(refined) + len(p) + 2 <= max_len:
            refined = (refined + " " + p).strip()
        else:
            break
    
    if len(refined) > max_len:
        refined = refined[:max_len].rsplit(" ", 1)[0]
    
    final_summary = refined + "."
    new_length = len(final_summary)
    iterations = state.refinement_iterations + 1
    
    logger.info(
        f"Rule-based refinement iteration {iterations}: {len(merged)} -> {new_length} chars "
        f"(target: {max_len}, reduction: {len(merged) - new_length})"
    )
    
    return state.copy_with_updates(
        refined_summary=final_summary,
        current_length=new_length,
        refinement_iterations=iterations,
        execution_metadata={
            **state.execution_metadata,
            f"refinement_{iterations}_length": new_length,
            f"refinement_{iterations}_reduction": len(merged) - new_length
        }
    )





def check_length_loop(state: WorkflowState) -> WorkflowState:
    should_continue = (
        state.current_length > state.max_length and
        state.refinement_iterations < state.max_refinement_iterations
    )
    
    logger.info(
        f"Length check: current={state.current_length}, "
        f"max={state.max_length}, iterations={state.refinement_iterations}, "
        f"should_loop={should_continue}"
    )
    
    return state


def _frequency_based_summarize(text: str) -> str:
    if not text or len(text) < 10:
        return text[:50] if text else ""
    
    sentences = _extract_sentences(text)
    
    if not sentences:
        return text[:50]
    
    if len(sentences) == 1:
        return _compress_sentence(sentences[0], max_words=16)
    
    word_freq = _calculate_word_frequencies(text)
    
    sentence_scores = []
    for sentence in sentences:
        score = _score_sentence(sentence, word_freq)
        sentence_scores.append((score, sentence))
    
    sentence_scores.sort(reverse=True, key=lambda x: x[0])
    best_sentence = sentence_scores[0][1]
    
    compressed = _compress_sentence(best_sentence, max_words=16)
    
    logger.debug(f"Selected sentence (score={sentence_scores[0][0]:.2f}): {compressed[:50]}...")
    
    return compressed


def _extract_sentences(text: str) -> List[str]:
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
    return sentences


def _calculate_word_frequencies(text: str) -> Dict[str, int]:
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    stopwords = _get_stopwords()
    words = [w for w in words if w not in stopwords]
    word_freq = Counter(words)
    return dict(word_freq)


def _score_sentence(sentence: str, word_freq: Dict[str, int]) -> float:
    words = re.findall(r'\b[a-zA-Z]{3,}\b', sentence.lower())
    
    if not words:
        return 0.0
    
    total_score = sum(word_freq.get(word, 0) for word in words)
    normalized_score = total_score / len(words)
    
    return normalized_score


def _compress_sentence(sentence: str, max_words: int = 16) -> str:
    words = sentence.split()
    
    if len(words) <= max_words:
        return sentence.strip()
    
    compressed_words = words[:max_words]
    compressed = " ".join(compressed_words)
    
    return compressed.strip()


def _get_stopwords() -> set:
    return {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each',
        'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
        'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
        'very', 'just', 'also', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'under', 'again', 'further',
        'then', 'once', 'here', 'there', 'all', 'any', 'both', 'each',
        'more', 'most', 'other', 'some', 'such', 'their', 'them', 'they',
        'about', 'against', 'because', 'being', 'down', 'off', 'over',
        'up', 'out', 'until', 'while', 'your'
    }
