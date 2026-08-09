# Shared contracts

This package is the first migration target for the Instrument Alpha codebase. It preserves the useful typed domain model from the AI Studio donor while enforcing the current contract that one `Finding` represents one mechanism on one exact span.

The current browser build is deliberately dependency-light. `contracts.ts` is compiled with the web application as global TypeScript declarations; later Python/TypeScript code generation can move these contracts to JSON Schema without changing the user-facing scanner behavior.
