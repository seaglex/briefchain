# Technology Stack
- **python** `python 3.13+`
- **Dependency Managemnt** `uv`
- **Asynchronous Programming:** Prefer `async` and `await`
- **Web Framework:** `fastapi`
- **ORM Framework:** `SQLAlchemy`
- **Version Control:** `git`
- **LLM Framework:** `google adk`

# Coding Guidelines

## 1. Pythonic Practices

- **Elegance and Readability:** Strive for elegant and Pythonic code that is easy to understand and maintain.
- **PEP 8 Compliance:** Adhere to PEP 8 guidelines for code style, with Ruff as the primary linter and formatter.
- **Explicit over Implicit:** Favor explicit code that clearly communicates its intent over implicit, overly concise code.
- **Zen of Python:** Keep the Zen of Python in mind when making design decisions.

## 2. Modular Design

- **Single Responsibility Principle:** Each module/file should have a well-defined, single responsibility.
- **Reusable Components:** Develop reusable functions and classes, favoring composition over inheritance.
- **Package Structure:** Organize code into logical packages and modules.

## 3. Code Quality

- **Comprehensive Type Annotations:** All functions, methods, and class members must have type annotations, using the most specific types possible.
- **Detailed Docstrings:** All functions, methods, and classes must have Google-style docstrings, thoroughly explaining their purpose, parameters, return values, and any exceptions raised. Include usage examples where helpful.
- **Unit Testing:** Prefer meaningful UT for the common cases.
- **Robust Exception Handling:** Use specific exception types, provide informative error messages, and handle exceptions gracefully. Implement custom exception classes when needed. Avoid bare `except` clauses.
- **DO NOT ignore Errors:** Do NOT catch exceptions and ignore. If there is proper fallback, fallback and log.
- **Logging:** Employ the `logging` module judiciously to log important events, warnings, and errors.

## 4. ORM Design
- **Prevent unintentional queries:** set lazy="raise" in relationship.
- **DO NOT use num / string to represent state:** always convert data in db to enum
- **Use UTC datetime in db:** convert to local time when use

## 5. Agent Specific Guidelines

- **LLM Prompt Engineering:** Dedicate a module or files for managing Prompt templates with version control.
- **Structured output:** Prefer pydantic.BaseModel as a interface between LLM and normal python code. Rely on LLM to format output. 
  - model.bind_tools(tools=[], response_format=StructuredModelBasingOnBaseModel)
- **LLM needs tokens to think:**: Include a str thinking field as the first element of the structured data, so that the LLM can think.

# Code Example Requirements

- All functions must include type annotations.
- Must provide clear, Google-style docstrings.
- Key logic should be annotated with comments.
- Provide usage examples (e.g., in the `tests/` directory or as a `__main__` section).
- Include error handling.


# Others

- **Prioritize new features in Python 3.10+.**
- **When explaining code, provide clear logical explanations and code comments.**
- **When making suggestions, explain the rationale and potential trade-offs.**
- **If code examples span multiple files, clearly indicate the file name.**
- **Do not over-engineer solutions. Strive for simplicity and maintainability while still being efficient.**
- **Favor modularity, but avoid over-modularization.**
- **Use the most modern and efficient libraries when appropriate, but justify their use and ensure they don't add unnecessary complexity.**
- **When providing solutions or examples, ensure they are self-contained and executable without requiring extensive modifications.**
- **If a request is unclear or lacks sufficient information, ask clarifying questions before proceeding.**
- **Always consider the security implications of your code, especially when dealing with user inputs and external data.**
- **Actively use and promote best practices for the specific tasks at hand (LLM app development, data cleaning, demo creation, etc.).**