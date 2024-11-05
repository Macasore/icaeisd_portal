from app import db
from app.models import ReviewHistory, PaperStatus


def get_latest_reviews_for_paper(paper_id):

    subquery = (
        db.session.query(
            ReviewHistory.reviewer_id,
            db.func.max(ReviewHistory.reviewed_at).label('latest_reviewed_at')
        )
        .filter(ReviewHistory.paper_id == paper_id)
        .group_by(ReviewHistory.reviewer_id)
    ).subquery()

    
    latest_reviews = (
        db.session.query(ReviewHistory)
        .join(subquery, 
               (ReviewHistory.reviewer_id == subquery.c.reviewer_id) & 
               (ReviewHistory.reviewed_at == subquery.c.latest_reviewed_at))
        .filter(ReviewHistory.paper_id == paper_id)
        .all()
    )

    return latest_reviews

def update_paper_status(paper_id):
    latest_reviews = get_latest_reviews_for_paper(paper_id)
    print(latest_reviews)

    latest_statuses = {review.reviewer_id: review.status for review in latest_reviews}
    print(latest_statuses)

    accepted_count = sum(1 for status in latest_statuses.values() if status == PaperStatus.A)
    rejected_count = sum(1 for status in latest_statuses.values() if status == PaperStatus.R)


    if len(latest_statuses) == 0:
        return PaperStatus.P 

    if len(latest_statuses) == 1:
        return PaperStatus.RF

    if len(latest_statuses) == 2:
        if accepted_count == 2:
            return PaperStatus.A
        elif rejected_count == 2:
            return PaperStatus.R
        else:
            return PaperStatus.RF

    return PaperStatus.P 
