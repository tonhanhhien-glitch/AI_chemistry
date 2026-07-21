import { AxiosError, type AxiosResponse } from "axios";
import { expect, it } from "vitest";
import { getApiErrorDetail } from "../api/client";

it("preserves ambiguous molecule candidates", () => {
  const response = { data: { detail: { code: "AMBIGUOUS_MOLECULE", message: "Chọn chất.", candidates: [{ id: "a", formula: "C2H6O", name_vi: "A" }] } }, status: 409, statusText: "Conflict", headers: {}, config: {} } as AxiosResponse;
  const detail = getApiErrorDetail(new AxiosError("ambiguous", "409", undefined, undefined, response));
  expect(detail.code).toBe("AMBIGUOUS_MOLECULE"); expect(detail.candidates?.[0].id).toBe("a");
});
