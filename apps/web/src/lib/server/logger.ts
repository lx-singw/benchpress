/**
 * Server-only Structured JSON Logger for Google Cloud Logging
 */

export interface StructuredLogPayload {
  severity: "DEBUG" | "INFO" | "WARNING" | "ERROR";
  message: string;
  correlation_id?: string;
  decision_id?: string;
  experiment_id?: string;
  truth_class?: string;
  [key: string]: unknown;
}

export function logJson(payload: StructuredLogPayload): void {
  const timestamp = new Date().toISOString();
  const logEntry = {
    timestamp,
    ...payload,
  };
  if (payload.severity === "ERROR") {
    console.error(JSON.stringify(logEntry));
  } else if (payload.severity === "WARNING") {
    console.warn(JSON.stringify(logEntry));
  } else {
    console.log(JSON.stringify(logEntry));
  }
}
