from .models import Session


def get_demo_data(session: Session) -> dict:
    """Returns session blocks with latest_edits applied."""
    blocks_with_edits = []
    for block in session.blocks:
        text = session.latest_edits.get(block.block_id, block.text)
        blocks_with_edits.append({
            "block_id": block.block_id,
            "page": block.page,
            "text": text,
            "x0": block.x0,
            "y0": block.y0,
            "x1": block.x1,
            "y1": block.y1,
        })
    return {
        "session_id": session.session_id,
        "doc_type": session.doc_type,
        "blocks": blocks_with_edits,
    }
