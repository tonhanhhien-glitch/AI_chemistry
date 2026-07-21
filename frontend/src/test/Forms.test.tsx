import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { expect, it, vi } from "vitest";
import FeedbackForm from "../components/feedback/FeedbackForm";
import SurveyPage from "../pages/SurveyPage";
import { submitFeedback } from "../api/feedbackApi";
import { submitSurvey } from "../api/surveyApi";

vi.mock("../api/feedbackApi", () => ({ submitFeedback: vi.fn() }));
vi.mock("../api/surveyApi", () => ({ submitSurvey: vi.fn() }));

it("submits anonymous feedback", async () => { vi.mocked(submitFeedback).mockResolvedValue({ accepted: true, session_id: "a2b70c63-0fa8-4c47-8a18-e07dc786d156", message_vi: "Đã lưu." }); render(<FeedbackForm moleculeId="h2o" />); await userEvent.click(screen.getByRole("button", { name: "Gửi phản hồi ẩn danh" })); expect(await screen.findByText("Đã lưu.")).toBeInTheDocument(); expect(submitFeedback).toHaveBeenCalledWith(expect.objectContaining({ molecule_id: "h2o", rating: 5 })); });

it("requires consent then submits the survey", async () => { vi.mocked(submitSurvey).mockResolvedValue({ accepted: true, session_id: "a2b70c63-0fa8-4c47-8a18-e07dc786d156", message_vi: "Khảo sát đã lưu." }); render(<MemoryRouter><SurveyPage /></MemoryRouter>); const submit = screen.getByRole("button", { name: "Gửi khảo sát ẩn danh" }); expect(submit).toBeDisabled(); await userEvent.click(screen.getByLabelText(/Tôi đã đọc/)); await userEvent.click(submit); expect(await screen.findByText("Khảo sát đã lưu.")).toBeInTheDocument(); expect(submitSurvey).toHaveBeenCalledWith(expect.objectContaining({ consent: true, phase: "pre" })); });
