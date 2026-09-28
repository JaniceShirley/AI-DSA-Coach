# Database Architecture & SQL Analytics Documentation

## 1. Relational Schema Design

The application utilizes PostgreSQL as its primary relational database. The schema is normalized and indexed to support analytical reporting and code submission auditing.

```text
+-------------------+       +-----------------------+       +---------------------+
|       User        |       |  UserProblemProgress  |       |       Problem       |
+-------------------+       +-----------------------+       +---------------------+
| id (PK)           |<----->| id (PK)               |<----->| id (PK)             |
| email (Unique,IX) |       | user_id (FK, IX)      |       | title               |
| name              |       | problem_id (FK, IX)   |       | slug (Unique, IX)   |
| password_hash     |       | status (IX)           |       | difficulty (IX)     |
| created_at        |       | attempts              |       | topics (JSONB)      |
+-------------------+       | solved_at             |       | patterns (JSONB)    |
                            | time_spent            |       | starter_code (JSONB)|
                            +-----------------------+       +---------------------+
                                                                      |
                                                                      | 1:N
                                                                      v
+-------------------+                                       +---------------------+
|    Submission     |                                       |      TestCase       |
+-------------------+                                       +---------------------+
| id (PK)           |                                       | id (PK)             |
| user_id (FK, IX)  |                                       | problem_id (FK, IX) |
| problem_id(FK, IX)|                                       | input_data          |
| status (IX)       |                                       | expected_output     |
| runtime           |                                       | is_public (IX)      |
| memory            |                                       +---------------------+
| created_at (IX)   |
+-------------------+
```

---

## 2. Key SQL / Django ORM Queries & Optimizations

### Query A: Aggregated Dashboard Progress Metrics
Calculates problem completion rates, total submissions, average attempts per solved problem, and average solving time directly within PostgreSQL using database aggregations.

**Django ORM Code:**
```python
solved_entries = UserProblemProgress.objects.filter(user=user, status='SOLVED')
stats = solved_entries.aggregate(
    avg_attempts=Avg('attempts'),
    avg_solving_time=Avg('time_spent')
)
```

**Equivalent Generated SQL:**
```sql
SELECT
    AVG(user_problem_progress.attempts) AS avg_attempts,
    AVG(user_problem_progress.time_spent) AS avg_solving_time
FROM user_problem_progress
WHERE user_problem_progress.user_id = 1
  AND user_problem_progress.status = 'SOLVED';
```
* **Performance Note:** Uses composite index on `(user_id, status)`. Returns aggregated numbers in `O(1)` space without transferring raw row data to python memory.

---

### Query B: Rule-Based Recommendation Query (Weakest Topic Targeting)
Finds the user's weakest topic based on completion percentage and recommends an unsolved problem matching that topic.

**Django ORM Code:**
```python
solved_problem_ids = set(
    UserProblemProgress.objects.filter(user=user, status='SOLVED')
    .values_list('problem_id', flat=True)
)

candidate = Problem.objects.filter(
    ~Q(id__in=solved_problem_ids)
).filter(topics__contains=weakest_topic).first()
```

**Equivalent Generated SQL:**
```sql
SELECT *
FROM problems
WHERE NOT (problems.id IN (
    SELECT problem_id
    FROM user_problem_progress
    WHERE user_id = 1 AND status = 'SOLVED'
))
AND problems.topics @> '["Array"]'::jsonb
ORDER BY problems.id ASC
LIMIT 1;
```
* **Performance Note:** Leverages PostgreSQL `JSONB` containment operator (`@>`) and subquery filtering for candidate problems.

---

## 3. Database Indexing Strategy

1. **`UserProblemProgress` Composite Unique Index:**
   * `UNIQUE(user_id, problem_id)` prevents duplicate tracking rows and speeds up progress lookup for specific problem pages.
2. **`Submission` Indexed Foreign Keys & Timestamps:**
   * `db_index=True` on `user_id`, `problem_id`, `status`, and `created_at` ensures submission audit history loads instantaneously even with millions of submission logs.
3. **`Problem` Unique Slug Index:**
   * `SlugField(unique=True, db_index=True)` enables `O(1)` problem lookup by URL slug (`/problems/two-sum`).
