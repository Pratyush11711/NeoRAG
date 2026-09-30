# Contributing to NeoRAG

Thank you for your interest in contributing to **NeoRAG**! This project was built as a portfolio and learning project to explore and demonstrate modern Retrieval-Augmented Generation (RAG) architectural patterns.

## Guidelines

1. **Focus on Clarity & Education**: Changes should aim to improve understandability, benchmarking, or clean architectural decoupling.
2. **Ephemeral Data Respect**: NeoRAG does not persist user data. PRs must preserve this privacy-first, ephemeral model.
3. **No Secrets in Code**: Never commit API keys, `.env` files, or internal credentials.
4. **Testing**: Run all backend unit tests before submitting a PR:
   ```bash
   pytest backend/tests
   ```

## Local Development Workflow

1. Fork the repository and clone your fork.
2. Create a feature branch: `git checkout -b feature/my-enhancement`.
3. Set up your `.env` following `.env.example`.
4. Commit your changes with concise, descriptive commit messages.
5. Push to your branch and open a Pull Request.
