import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Keep component tests independent so rendered elements cannot leak to later tests.
afterEach(() => {
  cleanup();
});
