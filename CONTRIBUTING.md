# Contributing to OrangeFi

Thank you for your interest in contributing to OrangeFi. This document provides guidelines and expectations for contributions.

> **Note:** OrangeFi is proprietary software. External contributions are subject to contributor licensing agreements.

---

## Code of Conduct

All contributors are expected to maintain a professional, respectful, and inclusive environment. Harassment or discriminatory behavior will not be tolerated.

---

## How to Contribute

### Reporting Bugs

1. Check the issue tracker to avoid duplicates
2. Use the bug report template
3. Include:
   - Clear description of the issue
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, browser, Docker version)
   - Logs and screenshots if applicable

### Feature Requests

1. Check the issue tracker for existing requests
2. Use the feature request template
3. Describe the problem you're solving, not just the solution
4. Include use cases and expected behavior

### Pull Requests

1. Fork the repository (external) or create a feature branch (internal)
2. Follow the coding standards below
3. Write or update tests
4. Update documentation
5. Ensure CI passes
6. Request review from at least one maintainer

---

## Development Workflow

### Branch Naming

```
feature/description       — New features
fix/description           — Bug fixes
chore/description         — Maintenance tasks
docs/description          — Documentation changes
refactor/description      — Code refactoring
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`

Examples:
```
feat(underwriting): add cash flow scoring blend
fix(api): handle null borrower on application detail
docs(deployment): add Render deploy steps
```

### Pull Request Checklist

- [ ] Code follows the project's style guidelines
- [ ] Tests pass (`pytest -x -v` for backend, `npm test` for frontend)
- [ ] New code has appropriate test coverage
- [ ] Documentation is updated (README, API docs, inline docs)
- [ ] No new warnings or lint errors
- [ ] Migration scripts are included for database changes
- [ ] Environment variables are documented in `.env.example`
- [ ] Security implications have been considered

---

## Coding Standards

### Python (Backend)

- **Python version:** 3.12+
- **Style:** PEP 8 with Black formatter (line length: 100)
- **Typing:** Type hints required for all functions
- **Docstrings:** Google-style docstrings for all public functions and classes
- **Async:** All I/O operations must use async/await
- **Imports:** Grouped: stdlib → third-party → local

```python
"""Module docstring."""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.models import Borrower
from app.utils.dependencies import get_current_borrower

logger = logging.getLogger(__name__)


async def get_borrower_profile(
    borrower: Borrower = Depends(get_current_borrower),
) -> dict[str, Any]:
    """Get the authenticated borrower's profile.

    Args:
        borrower: The authenticated borrower (from dependency injection).

    Returns:
        dict: Borrower profile data.
    """
    return {
        "id": str(borrower.id),
        "email": borrower.email,
    }
```

### TypeScript / JavaScript (Frontend)

- **Style:** ESLint + Prettier (project config)
- **Typing:** TypeScript strict mode, no `any` where avoidable
- **Components:** React functional components with hooks
- **State:** Zustand for global state, local state for component-specific data
- **CSS:** Tailwind utility classes, custom CSS only when necessary

```typescript
// Good
interface BorrowerProfile {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
}

export function ProfileCard({ profile }: { profile: BorrowerProfile }) {
  return (
    <div className="rounded-lg bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold">
        {profile.firstName} {profile.lastName}
      </h2>
      <p className="text-gray-600">{profile.email}</p>
    </div>
  );
}
```

### Database Migrations

- Use Alembic for all schema changes
- Generate migration after model changes:
  ```bash
  cd backend
  alembic revision --autogenerate -m "description"
  alembic upgrade head
  ```
- Test migrations both forward and backward (`downgrade`)
- Never edit existing migrations (create new ones)

---

## Testing

### Backend Tests

```bash
cd backend
pytest -x -v                          # Run tests
pytest --cov=app --cov-report=html    # Coverage report
pytest -x -v tests/ -k "underwriting"  # Run specific test group
```

**Testing requirements:**
- Unit tests for all business logic (underwriting, pricing, scoring)
- Integration tests for all API endpoints
- Test both success and failure paths
- Test edge cases (boundary values, null inputs)

### Frontend Tests

```bash
cd frontend
npm run lint          # ESLint
npm run typecheck     # TypeScript type checking
# Jest tests (when added):
# npm test
```

---

## Documentation

- All public API endpoints must have docstrings and Pydantic schema documentation
- README updates for new features or configuration changes
- Architecture decisions documented in `docs/` as needed
- Inline comments for complex logic (why, not what)

---

## Review Process

1. **Draft PR** — Open for early feedback
2. **CI Check** — Automated checks must pass
3. **Code Review** — At least one maintainer review required
4. **Approval** — Address all review comments
5. **Merge** — Squash merge to `main` (keep commit history clean)

---

## Getting Help

- **Issues:** GitHub issue tracker
- **Internal:** Slack #orangefi-engineering
- **Email:** engineering@orangefi.com
