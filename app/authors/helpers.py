from app.models import Paper, CoAuthor,User
from sqlalchemy.orm import aliased

MAX_ABSTRACT_WORDS = 300

def check_paper_limits(email):
    Useralias = aliased(User)
    authored_papers_count = Paper.query.join(Useralias, Paper.author_id == Useralias.id).filter(Useralias.email == email).count()
    
    coauthored_papers_count = CoAuthor.query.filter_by(email=email).count()
    
    total_papers_count = authored_papers_count + coauthored_papers_count
    
    max_papers_allowed = 2
    
    if authored_papers_count >= max_papers_allowed:
        return False, "You have already submitted the maximum number of papers allowed (2)."
    
    if total_papers_count >= max_papers_allowed:
        return False, "You have reached the maximum paper limit as an author or coauthor."
    
    return True, ""

def count_words(text):
    return len(text.split())

def validate_abstract(abstract):
    word_count = count_words(abstract)
    if word_count > MAX_ABSTRACT_WORDS:
        return False, word_count
    return True, word_count