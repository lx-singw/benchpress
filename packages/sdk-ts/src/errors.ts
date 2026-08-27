/**
 * Custom Error Hierarchy for @benchpress/sdk.
 */

export class BenchpressError extends Error {
  public readonly status?: number;
  public readonly code?: string;

  constructor(message: string, status?: number, code?: string) {
    super(message);
    this.name = "BenchpressError";
    this.status = status;
    this.code = code;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class AuthenticationError extends BenchpressError {
  constructor(message: string = "Invalid or missing Benchpress API Key") {
    super(message, 401, "UNAUTHORIZED");
    this.name = "AuthenticationError";
  }
}

export class RateLimitError extends BenchpressError {
  constructor(message: string = "Benchpress rate limit exceeded (429)") {
    super(message, 429, "RATE_LIMIT_EXCEEDED");
    this.name = "RateLimitError";
  }
}

export class ValidationError extends BenchpressError {
  public readonly errors?: any[];

  constructor(message: string, errors?: any[]) {
    super(message, 400, "VALIDATION_ERROR");
    this.name = "ValidationError";
    this.errors = errors;
  }
}
