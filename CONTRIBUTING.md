# Contributing to FraudWatch

Thank you for your interest in contributing to FraudWatch! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Be kind, constructive, and professional in all interactions.

## Getting Started

### Prerequisites

- Fork and clone the repository
- Install required dependencies (see [README.md](README.md))
- Set up development environments for both frontend and backend

### Initial Setup

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Configure .env with local settings
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   # Configure .env.local with local settings
   ```

3. **Verify Setup**
   ```bash
   # Backend
   cd backend && uvicorn app.main:app --reload
   
   # Frontend (in another terminal)
   cd frontend && npm run dev
   ```

## Development Workflow

### 1. Create a Branch

Create a descriptive branch name from `main`:

```bash
# Feature branches
git checkout -b feature/auth-implementation

# Bug fix branches
git checkout -b fix/token-validation-error

# Documentation branches
git checkout -b docs/api-endpoints
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests
- `style/` - Code style changes (formatting, etc.)

### 2. Make Changes

- Write clean, maintainable, and well-documented code
- Follow the existing code style and architecture
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

**Backend:**
```bash
cd backend
pytest tests/ -v --cov=app
black app/ tests/
isort app/ tests/
flake8 app/ tests/
```

**Frontend:**
```bash
cd frontend
npm run lint
npm run test
```

### 4. Commit Changes

Follow the [commit guidelines](#commit-guidelines) below.

## Code Standards

### Python (Backend)

- **Linting**: Black, isort, flake8
- **Type Hints**: All function signatures must include type hints
- **Docstrings**: All modules, classes, and functions must have docstrings
- **Formatting**: Black (88 character line length)
- **Imports**: isort with Black profile

```python
# Good example
def process_transaction(
    transaction_id: str,
    amount: Decimal,
    user_id: str,
) -> TransactionResult:
    """
    Process a financial transaction.
    
    Args:
        transaction_id: Unique transaction identifier
        amount: Transaction amount in decimal
        user_id: ID of the user initiating transaction
    
    Returns:
        TransactionResult: Result of transaction processing
    
    Raises:
        ValidationException: If transaction data is invalid
        DatabaseException: If database operation fails
    """
    pass
```

### TypeScript (Frontend)

- **Linting**: ESLint with Airbnb config
- **Formatting**: Prettier
- **Components**: Functional components with hooks
- **Types**: Explicit TypeScript types, avoid `any`

```typescript
// Good example
interface TransactionProps {
  transactionId: string;
  amount: number;
  status: TransactionStatus;
}

export const TransactionCard: React.FC<TransactionProps> = ({
  transactionId,
  amount,
  status,
}) => {
  // Component logic
};
```

### General Principles

1. **DRY** - Don't Repeat Yourself
2. **SOLID** - Follow SOLID principles
3. **KISS** - Keep It Simple, Stupid
4. **YAGNI** - You Aren't Gonna Need It
5. **Separation of Concerns** - Keep business logic separate from presentation
6. **Error Handling** - Always handle errors explicitly
7. **Security** - Never log sensitive data, sanitize all inputs

## Commit Guidelines

### Commit Message Format

```
Type(scope): Subject

[Optional body]

[Optional footer]
```

### Types

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style (formatting, missing semicolons, etc.)
- `refactor` - Code refactoring
- `perf` - Performance improvements
- `test` - Adding or updating tests
- `chore` - Maintenance tasks

### Examples

```
feat(auth): Add JWT token refresh endpoint

Implement token refresh flow with proper validation
and error handling.

Closes #42
```

```
fix(api): Correct pagination offset calculation

The offset was incorrectly calculated when page size
changed between requests.
```

```
docs(readme): Update development setup instructions
```

## Pull Request Process

### Before Submitting

1. Ensure all tests pass
2. Update documentation if needed
3. Add or update tests for your changes
4. Ensure code follows style guidelines
5. Rebase on latest `main` branch

### PR Template

```markdown
## Description
[Provide a brief description of the changes]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
```

### Review Process

1. Automated CI checks must pass
2. At least one maintainer review required
3. Approval and merge by project maintainer
4. Branch deletion after merge

## Testing

### Backend Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/unit/test_auth.py -v

# Run integration tests
pytest tests/integration/ -v
```

### Frontend Tests

```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test -- TransactionCard
```

## Reporting Bugs

### Before Submitting a Bug Report

1. Check if the bug has already been reported in Issues
2. Ensure you're using the latest version
3. Collect relevant information (logs, screenshots, steps to reproduce)

### Bug Report Template

```markdown
## Bug Description
[Clear description of the bug]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [See error]

## Expected Behavior
[What you expected to happen]

## Actual Behavior
[What actually happened]

## Environment
- OS: [e.g., macOS 14.0]
- Browser: [e.g., Chrome 120]
- Version: [e.g., 1.0.0]

## Additional Context
[Add any other context, logs, or screenshots]
```

## Suggesting Features

### Before Suggesting a Feature

1. Check if the feature has already been requested
2. Ensure it aligns with the project's goals
3. Consider if it can be implemented as a library/module

### Feature Request Template

```markdown
## Feature Description
[Clear description of the proposed feature]

## Use Case
[Why is this feature needed? Who will use it?]

## Proposed Solution
[How do you envision this feature working?]

## Alternatives Considered
[What other approaches have you considered?]

## Additional Context
[Add any mockups, examples, or references]
```

## Questions?

If you have questions or need help:
1. Check the [documentation](docs/)
2. Search existing [Issues](https://github.com/your-org/fraudwatch/issues)
3. Create a new Issue with the `question` label

## Thank You!

Your contributions make FraudWatch better for everyone. We appreciate your time and effort!
</parameter>
<task_progress>
- [x] Create root project structure
- [x] Initialize frontend (Next.js + TypeScript + Tailwind)
- [x] Initialize backend (FastAPI + SQLAlchemy)
- [x] Set up ML folder structure
- [x] Create Docker configuration
- [x] Configure environment variables
- [x] Prepare security architecture
- [ ] Create documentation and Git files
- [ ] Set up CI/CD pipelines
- [ ] Set up code quality tools
- [ ] Verify complete project structure
</parameter>
</write_to_file>