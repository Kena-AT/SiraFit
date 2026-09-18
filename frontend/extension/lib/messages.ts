import { CapturedJob, CaptureValidationResult } from "../types/job";

export type ExtensionMessage =
  | { type: "CAPTURE_ACTIVE_TAB" }
  | { type: "GET_AUTH_STATUS" }
  | { type: "SAVE_AUTH_TOKEN"; token: string }
  | { type: "IMPORT_JOB"; payload: CapturedJob };

export type CaptureResponse = CaptureValidationResult | { error: string };
