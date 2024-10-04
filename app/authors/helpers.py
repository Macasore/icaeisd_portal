from app.models import Paper, CoAuthor

def check_paper_limits(email):
    authored_papers_count = Paper.query.filter_by(author_email=email).count()
    print(authored_papers_count)
    
    coauthored_papers_count = CoAuthor.query.filter_by(email=email).count()
    print(coauthored_papers_count)
    
    total_papers_count = authored_papers_count + coauthored_papers_count
    print(total_papers_count)
    
    max_papers_allowed = 2
    
    if authored_papers_count >= max_papers_allowed:
        return False, "You have already submitted the maximum number of papers allowed (2)."
    
    if total_papers_count >= max_papers_allowed:
        return False, "You have reached the maximum paper limit as an author or coauthor."
    
    return True, ""