from app.ai import hybrid_match, match_reasons
from app.db import SessionLocal
from app.models import Rating, Skill, SwapRequest
from conftest import auth


def test_public_discovery_counts_filters_and_private_fields(client, people):
    first = people['ids'][0]
    with SessionLocal() as db:
        db.add(Skill(owner_id=first, title='Python', description='Practice Python together',
                     type='Requesting', category='Technology', level='Beginner'))
        db.commit()
    summary = client.get('/api/v1/community/summary').json()
    assert summary['people'] == 3
    assert summary['teaching_skills'] == 3
    assert summary['learning_goals'] == 1
    popular = client.get('/api/v1/community/popular-skills').json()
    python = next(s for s in popular if s['title'] == 'Python')
    assert python['teachers'] == python['learners'] == 1
    result = client.get('/api/v1/community/members', params={'search': 'Python', 'limit': 1}).json()
    assert result['total'] == 2 and len(result['items']) == 1
    member = result['items'][0]
    assert member['id'] == first
    assert {'email', 'password_hash', 'messages'}.isdisjoint(member)
    assert client.get('/api/v1/community/members', params={'category': 'Design'}).json()['total'] == 0
    assert client.get('/api/v1/community/members', params={'offset': 1, 'limit': 1}).json()['items'][0]['id'] != first
    assert client.get('/api/v1/community/members', params={'limit': 999}).status_code == 422
    assert client.get('/api/v1/community/members/999999').status_code == 404


def test_profile_ratings_are_received_not_written(client, people):
    with SessionLocal() as db:
        db.get(SwapRequest, people['swap']).status = 'completed'
        db.add_all([
            Rating(rater_id=people['ids'][0], rated_id=people['ids'][1], swap_id=people['swap'], score=5, review='Great Python exchange'),
            Rating(rater_id=people['ids'][1], rated_id=people['ids'][0], swap_id=people['swap'], score=3, review='Helpful React practice'),
        ])
        db.commit()
    profile = client.get(f"/api/v1/community/members/{people['ids'][0]}").json()
    assert profile['rating'] == 3 and profile['review_count'] == 1
    assert profile['reviews'][0]['review'] == 'Helpful React practice'
    # Existing submitted-review contract remains available to Swaps.
    assert client.get('/api/v1/ratings', headers=auth(people)).json()[0]['score'] == 5


def test_match_explanations_keep_actual_skill_and_level_direction():
    teacher = Skill(title='React', type='Offering', category='Technology', level='Advanced', description='', tags='')
    learner = Skill(title='Python', type='Requesting', category='Technology', level='Beginner', description='', tags='')
    reasons = ' '.join(match_reasons(teacher, learner, hybrid_match(teacher, learner)))
    assert 'wants to learn Python' in reasons
    assert 'Advanced teaching for a Beginner goal' in reasons
    assert 'wants to learn React' not in reasons
