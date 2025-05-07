from trafilatura import extract
import logging

logger = logging.getLogger(__name__)

def pick_movie_block_with_trafilatura(candidates):
    """Select the most movie-like HTML block using Trafilatura's text extraction score."""
    if not candidates:
        return 0

    scores = []
    for i, html in enumerate(candidates):
        try:
            extracted = extract(
                html,
                favor_precision=True,
                include_images=True,
                include_links=True,
                output_format="txt",
                include_tables=True
            )
            score = len(extracted.strip()) if extracted else 0
        except Exception as e:
            logger.warning(f"Trafilatura extraction failed for block {i+1}: {e}")
            score = 0

        scores.append(score)
        logger.debug(f"Block {i+1} score: {score}")

    best_index = scores.index(max(scores))
    logger.info(f"[Trafilatura] Selected Block {best_index + 1} with score {scores[best_index]}")
    return best_index
